"""``GET /me`` (create profile on first call) and ``PATCH /me``."""

from datetime import datetime, time
from typing import Annotated
from zoneinfo import available_timezones

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from app.auth import CurrentProfile
from app.db.session import SessionDep
from app.errors import ErrorDetail, ValidationFailed, error_responses, guard
from app.services.ratelimit import default_rate_limit

router = APIRouter(tags=["account"], dependencies=[Depends(default_rate_limit)])

DisplayName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class Profile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str | None
    display_name: str | None
    timezone: str
    reminder_time: time | None
    created_at: datetime
    updated_at: datetime


class UpdateMeRequest(BaseModel):
    """Only the fields sent are changed. ``reminder_time`` may be set to null."""

    model_config = ConfigDict(extra="forbid")

    display_name: DisplayName | None = None
    timezone: str | None = None
    reminder_time: time | None = None

    @field_validator("timezone")
    @classmethod
    def known_timezone(cls, v: str | None) -> str | None:
        if v is not None and v not in available_timezones():
            raise ValueError("must be an IANA time zone such as 'Asia/Manila'")
        return v


@router.get("/me", response_model=Profile, responses=error_responses(401, 429, 503))
async def get_me(profile: CurrentProfile, session: SessionDep) -> Profile:
    """The signed-in user's profile; created on the first call if the Clerk webhook hasn't
    arrived yet."""
    with guard("db.commit", user_id=profile.id):
        await session.commit()
    return Profile.model_validate(profile)


@router.patch("/me", response_model=Profile, responses=error_responses(401, 422, 429, 503))
async def update_me(body: UpdateMeRequest, profile: CurrentProfile, session: SessionDep) -> Profile:
    """Update display name, time zone or reminder time."""
    fields = body.model_fields_set
    if "timezone" in fields and body.timezone is None:
        raise ValidationFailed(
            details=[ErrorDetail(loc=["body", "timezone"], msg="timezone can't be null")]
        )
    if "display_name" in fields:
        profile.display_name = body.display_name
    if "timezone" in fields and body.timezone is not None:
        profile.timezone = body.timezone
    if "reminder_time" in fields:
        profile.reminder_time = body.reminder_time
    with guard("db.update_profile", user_id=profile.id):
        await session.commit()
        await session.refresh(profile)
    return Profile.model_validate(profile)
