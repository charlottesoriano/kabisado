"""Extra seeding for QA tests: a deck with every kind of dependent row (chunks, cards, states,
reviews, a quiz attempt with questions and answers, a generation run), and row counters.

``commit()`` only releases a savepoint (see ``tests/seed.py``)."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models
from tests import seed


@dataclass
class FullDeck:
    document: models.Document
    chunk_ids: list[UUID]
    card_ids: list[UUID]
    attempt_id: UUID


async def full_deck(db: AsyncSession, user_id: str, *, title: str = "Biology") -> FullDeck:
    doc = await seed.document(db, user_id, title=title, status="ready", page_count=3)
    chunks = [await seed.chunk(db, doc.id, idx=i) for i in range(2)]
    flash = await seed.card(db, doc.id, chunk_id=chunks[0].id)
    mcq = await seed.card(db, doc.id, type="mcq", chunk_id=chunks[1].id)
    for c in (flash, mcq):
        await seed.state(db, user_id, c.id)
    db.add(
        models.Review(
            user_id=user_id,
            card_id=flash.id,
            rating=2,
            source="review",
            interval_before=0,
            interval_after=1,
        )
    )
    attempt = models.Attempt(user_id=user_id, document_id=doc.id, kind="quiz", length=5)
    db.add(attempt)
    await db.flush()
    db.add(
        models.AttemptQuestion(
            attempt_id=attempt.id, position=0, card_id=mcq.id, option_order=[2, 0, 3, 1]
        )
    )
    db.add(
        models.AttemptAnswer(attempt_id=attempt.id, card_id=mcq.id, chosen_index=1, result="wrong")
    )
    db.add(models.GenerationRun(document_id=doc.id))
    await db.commit()  # releases the savepoint only
    return FullDeck(doc, [c.id for c in chunks], [flash.id, mcq.id], attempt.id)


async def count(db: AsyncSession, model: Any, *where: Any) -> int:
    stmt = select(func.count()).select_from(model).where(*where)
    return int((await db.execute(stmt)).scalar_one())


async def deck_row_counts(db: AsyncSession, deck: FullDeck, user_id: str) -> dict[str, int]:
    """Rows that belong to ``deck`` (and the user's rows that hang off its cards)."""
    m = models
    return {
        "documents": await count(db, m.Document, m.Document.id == deck.document.id),
        "chunks": await count(db, m.Chunk, m.Chunk.document_id == deck.document.id),
        "cards": await count(db, m.Card, m.Card.document_id == deck.document.id),
        "card_states": await count(
            db, m.CardState, m.CardState.user_id == user_id, m.CardState.card_id.in_(deck.card_ids)
        ),
        "reviews": await count(db, m.Review, m.Review.card_id.in_(deck.card_ids)),
        "attempts": await count(db, m.Attempt, m.Attempt.document_id == deck.document.id),
        "attempt_questions": await count(
            db, m.AttemptQuestion, m.AttemptQuestion.attempt_id == deck.attempt_id
        ),
        "attempt_answers": await count(
            db, m.AttemptAnswer, m.AttemptAnswer.attempt_id == deck.attempt_id
        ),
        "generation_runs": await count(
            db, m.GenerationRun, m.GenerationRun.document_id == deck.document.id
        ),
    }
