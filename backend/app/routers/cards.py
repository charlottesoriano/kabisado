"""Cards: paginated list, edit payload, flag, topic-targeted generation (RAG; build step 3f).

The deck view includes answers (it is the student's own deck). Flagged cards are listed too so
they can be edited; sessions exclude them.
"""

import base64
import binascii
import json
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.schemas import FlashcardPayload, McqPayload
from app.auth import CurrentUserId
from app.db import models
from app.db.models import CardOrigin, CardType, FlagReason
from app.db.session import SessionDep
from app.errors import (
    ErrorDetail,
    NotEditable,
    NotFound,
    ValidationFailed,
    error_responses,
    guard,
)
from app.routers.documents import owned_document
from app.services.ratelimit import default_rate_limit

router = APIRouter(tags=["cards"], dependencies=[Depends(default_rate_limit)])

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


class Card(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    chunk_id: UUID | None = Field(description="Source chunk; null if it was deleted")
    type: CardType
    payload: dict[str, Any] = Field(
        description="flashcard {front, back}; mcq {question, options[4], answer_index, "
        "explanation}; problem: template (MDs/05-database-schema.md section 6)"
    )
    topic: str | None
    origin: CardOrigin
    flagged: bool
    flag_reason: FlagReason | None
    edited: bool
    created_at: datetime
    updated_at: datetime


class CardPage(BaseModel):
    items: list[Card]
    next_cursor: str | None = Field(description="Pass as `cursor` for the next page; null at end")


class UpdateCardRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payload: FlashcardPayload | McqPayload = Field(
        description="Must match the card's type. Problem templates can't be edited yet."
    )


class FlagCardRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: FlagReason


# Cursor: opaque base64url of [created_at ISO, id] -------------------------------------------
def encode_cursor(created_at: datetime, card_id: UUID) -> str:
    raw = json.dumps([created_at.isoformat(), str(card_id)]).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
        created_at, card_id = json.loads(raw)
        return datetime.fromisoformat(created_at), UUID(card_id)
    except (binascii.Error, ValueError, TypeError) as exc:
        raise ValidationFailed(
            "This page link is invalid. Reload the list.",
            details=[ErrorDetail(loc=["query", "cursor"], msg="invalid cursor")],
        ) from exc


async def owned_card(
    session: AsyncSession, user_id: str, card_id: UUID, *, for_update: bool = False
) -> models.Card:
    stmt = (
        select(models.Card)
        .join(models.Document, models.Document.id == models.Card.document_id)
        .where(models.Card.id == card_id, models.Document.user_id == user_id)
    )
    if for_update:
        stmt = stmt.with_for_update(of=models.Card)
    with guard("db.get_card", card_id=card_id):
        card = (await session.execute(stmt)).scalar_one_or_none()
    if card is None:
        raise NotFound(context={"card_id": card_id})
    return card


# Routes -----------------------------------------------------------------------------------------
@router.get(
    "/documents/{document_id}/cards",
    response_model=CardPage,
    responses=error_responses(401, 404, 422, 429, 503),
)
async def list_cards(
    document_id: UUID,
    user_id: CurrentUserId,
    session: SessionDep,
    type: Annotated[CardType | None, Query(description="Only this card type")] = None,
    cursor: Annotated[str | None, Query(description="From the previous page")] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> CardPage:
    """A deck's cards, oldest first, with answers (the student's own deck view)."""
    await owned_document(session, user_id, document_id)
    stmt = select(models.Card).where(models.Card.document_id == document_id)
    if type is not None:
        stmt = stmt.where(models.Card.type == type)
    if cursor is not None:
        after_created, after_id = decode_cursor(cursor)
        stmt = stmt.where(
            tuple_(models.Card.created_at, models.Card.id) > tuple_(after_created, after_id)
        )
    stmt = stmt.order_by(models.Card.created_at, models.Card.id).limit(limit + 1)
    with guard("db.list_cards", document_id=document_id):
        rows = list((await session.execute(stmt)).scalars())
    page, more = rows[:limit], len(rows) > limit
    next_cursor = encode_cursor(page[-1].created_at, page[-1].id) if more else None
    return CardPage(items=[Card.model_validate(c) for c in page], next_cursor=next_cursor)


@router.patch(
    "/cards/{card_id}",
    response_model=Card,
    responses=error_responses(401, 404, 422, 429, 503),
)
async def update_card(
    card_id: UUID, body: UpdateCardRequest, user_id: CurrentUserId, session: SessionDep
) -> Card:
    """Edit a flashcard or MCQ. Marks it edited and clears any flag."""
    card = await owned_card(session, user_id, card_id, for_update=True)
    if card.type == "problem":
        raise NotEditable(
            "Practice problems can't be edited yet. You can flag it instead.",
            context={"card_id": card_id},
        )
    expected = FlashcardPayload if card.type == "flashcard" else McqPayload
    if not isinstance(body.payload, expected):
        raise ValidationFailed(
            f"This is a {card.type} card, so the edit must be a {card.type}.",
            details=[ErrorDetail(loc=["body", "payload"], msg=f"expected a {card.type} payload")],
        )
    card.payload = body.payload.model_dump()
    card.edited = True
    card.flagged = False
    card.flag_reason = None
    with guard("db.update_card", card_id=card_id):
        await session.commit()
        await session.refresh(card)
    return Card.model_validate(card)


@router.post(
    "/cards/{card_id}/flag",
    response_model=Card,
    responses=error_responses(401, 404, 422, 429, 503),
)
async def flag_card(
    card_id: UUID, body: FlagCardRequest, user_id: CurrentUserId, session: SessionDep
) -> Card:
    """Flag a card with a reason; it is hidden from reviews, quizzes and problem sessions."""
    card = await owned_card(session, user_id, card_id, for_update=True)
    card.flagged = True
    card.flag_reason = body.reason
    with guard("db.flag_card", card_id=card_id):
        await session.commit()
        await session.refresh(card)
    return Card.model_validate(card)
