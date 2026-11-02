"""Clerk webhooks (``POST /webhooks/clerk``), Svix-verified.

``user.created`` / ``user.updated`` upsert the profile; ``user.deleted`` deletes the profile
(cascade) and the user's Storage files. Idempotent by ``svix-id`` via ``app.webhook_events``.

- A bad signature is 400 ``invalid_signature`` and changes nothing.
- A ``svix-id`` seen before returns 200 ``duplicate`` and changes nothing.
- ``user.deleted``: Storage files first (idempotent), then the profile delete and the event
  record in one transaction. Any failure returns an error so Svix retries.
- The email always follows Clerk. The display name from Clerk only fills an empty one, so a
  name the student set with ``PATCH /me`` isn't overwritten.
- Other event types are recorded and ignored.
- Events are recorded with the user id they are about. A ``user.created`` / ``user.updated``
  that arrives after that user's ``user.deleted`` (Svix doesn't guarantee order) is recorded
  and ignored, so a deleted user's profile is never recreated.
"""

import json
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from svix.webhooks import Webhook, WebhookVerificationError

from app.config import get_settings
from app.db.models import Profile, WebhookEvent
from app.db.session import SessionDep
from app.errors import BadRequest, InvalidSignature, ServiceUnavailable, error_responses, guard
from app.services.storage import Storage, get_storage

router = APIRouter(tags=["webhooks"])

SVIX_HEADERS = ("svix-id", "svix-timestamp", "svix-signature")


class WebhookAck(BaseModel):
    status: Literal["processed", "ignored", "duplicate"]


def _primary_email(data: dict[str, Any]) -> str | None:
    primary = data.get("primary_email_address_id")
    emails = data.get("email_addresses") or []
    for e in emails:
        if e.get("id") == primary and e.get("email_address"):
            return str(e["email_address"])
    return str(emails[0]["email_address"]) if emails and emails[0].get("email_address") else None


def _display_name(data: dict[str, Any]) -> str | None:
    name = " ".join(p for p in (data.get("first_name"), data.get("last_name")) if p).strip()
    return name or data.get("username") or None


@router.post(
    "/webhooks/clerk",
    response_model=WebhookAck,
    responses=error_responses(400, 502, 503),
)
async def clerk_webhook(
    request: Request, session: SessionDep, storage: Annotated[Storage, Depends(get_storage)]
) -> WebhookAck:
    """Clerk user events (Svix-signed). Not called by the apps."""
    secret = get_settings().clerk_webhook_secret.get_secret_value()
    if not secret:
        raise ServiceUnavailable(
            operation="webhooks.clerk", context={"reason": "webhook_secret_missing"}
        )
    body = await request.body()
    headers = {h: request.headers.get(h, "") for h in SVIX_HEADERS}
    try:
        Webhook(secret).verify(body, headers)
    except WebhookVerificationError as exc:
        raise InvalidSignature(operation="webhooks.clerk.verify") from exc
    try:
        event = json.loads(body)
        event_type = str(event["type"])
        data: dict[str, Any] = event.get("data") or {}
    except (ValueError, KeyError, TypeError) as exc:
        raise BadRequest(operation="webhooks.clerk.parse") from exc

    svix_id = headers["svix-id"]
    with guard("db.get_webhook_event", svix_id=svix_id):
        lookup = select(WebhookEvent.svix_id).where(WebhookEvent.svix_id == svix_id)
        seen = (await session.execute(lookup)).scalar_one_or_none()
    if seen is not None:
        return WebhookAck(status="duplicate")

    raw_user_id = data.get("id")
    user_id = raw_user_id if isinstance(raw_user_id, str) and raw_user_id else None
    result: Literal["processed", "ignored"] = "ignored"
    upsert = event_type in ("user.created", "user.updated") and user_id is not None
    if upsert:
        deleted_lookup = select(WebhookEvent.svix_id).where(
            WebhookEvent.event_type == "user.deleted", WebhookEvent.user_id == user_id
        )
        with guard("db.find_user_deleted", user_id=user_id, svix_id=svix_id):
            upsert = (await session.execute(deleted_lookup.limit(1))).first() is None
    if upsert and user_id is not None:
        stmt = insert(Profile).values(
            id=user_id, email=_primary_email(data), display_name=_display_name(data)
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[Profile.id],
            set_={
                "email": stmt.excluded.email,
                "display_name": func.coalesce(Profile.display_name, stmt.excluded.display_name),
                "updated_at": func.now(),
            },
        )
        with guard("db.upsert_profile", user_id=user_id, svix_id=svix_id):
            await session.execute(stmt)
        result = "processed"
    elif event_type == "user.deleted" and user_id is not None:
        await storage.delete_prefix(user_id)
        with guard("db.delete_profile", user_id=user_id, svix_id=svix_id):
            await session.execute(delete(Profile).where(Profile.id == user_id))
        result = "processed"

    record = (
        insert(WebhookEvent)
        .values(svix_id=svix_id, event_type=event_type, user_id=user_id)
        .on_conflict_do_nothing()
        .returning(WebhookEvent.svix_id)
    )
    with guard("db.record_webhook_event", svix_id=svix_id):
        inserted = (await session.execute(record)).scalar_one_or_none()
        if inserted is None:  # a concurrent delivery won the race
            await session.rollback()
            return WebhookAck(status="duplicate")
        await session.commit()
    return WebhookAck(status=result)
