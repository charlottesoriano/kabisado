"""Direct-to-database seeding helpers for API tests.

``commit()`` here only releases a savepoint (the ``db`` fixture's outer transaction is rolled
back after each test), so seeded rows survive the per-request rollback the ``api`` fixture
does, just like committed rows in production."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models

NOTES = "Photosynthesis converts light energy into chemical energy. " * 5

FLASHCARD = {"front": "What does photosynthesis make?", "back": "Glucose and oxygen"}
MCQ = {
    "question": "Which organelle makes ATP?",
    "options": ["Mitochondrion", "Ribosome", "Nucleus", "Golgi body"],
    "answer_index": 0,
    "explanation": "Mitochondria run cellular respiration.",
}
PROBLEM = {"subject": "physics", "question": "A car accelerates at {a} m/s^2 for {t} s."}


async def profile(db: AsyncSession, user_id: str, **fields: Any) -> None:
    await db.execute(insert(models.Profile).values(id=user_id, **fields).on_conflict_do_nothing())
    await db.commit()  # releases the savepoint only


async def document(
    db: AsyncSession,
    user_id: str,
    *,
    title: str = "Biology",
    source_type: str = "pdf",
    status: str = "queued",
    page_count: int | None = None,
    created_at: datetime | None = None,
    **fields: Any,
) -> models.Document:
    await profile(db, user_id)
    doc_id = fields.pop("id", uuid4())
    doc = models.Document(
        id=doc_id,
        user_id=user_id,
        title=title,
        source_type=source_type,
        status=status,
        page_count=page_count,
        file_path=f"{user_id}/{doc_id}.pdf" if source_type == "pdf" else None,
        raw_text=NOTES if source_type == "text" else None,
        **fields,
    )
    if created_at is not None:
        doc.created_at = created_at
        doc.updated_at = created_at
    db.add(doc)
    await db.commit()  # releases the savepoint only
    return doc


async def chunk(db: AsyncSession, document_id: UUID, idx: int = 0) -> models.Chunk:
    c = models.Chunk(
        document_id=document_id,
        idx=idx,
        heading="Light reactions",
        content="Chlorophyll absorbs light.",
        token_count=5,
        page_start=3,
        page_end=4,
    )
    db.add(c)
    await db.commit()  # releases the savepoint only
    return c


async def card(
    db: AsyncSession,
    document_id: UUID,
    *,
    type: str = "flashcard",
    payload: dict[str, Any] | None = None,
    flagged: bool = False,
    created_at: datetime | None = None,
    **fields: Any,
) -> models.Card:
    default = {"flashcard": FLASHCARD, "mcq": MCQ, "problem": PROBLEM}[type]
    c = models.Card(
        document_id=document_id,
        type=type,
        payload=payload or default,
        flagged=flagged,
        flag_reason="unclear" if flagged else None,
        **fields,
    )
    if created_at is not None:
        c.created_at = created_at
    db.add(c)
    await db.commit()  # releases the savepoint only
    return c


async def state(
    db: AsyncSession,
    user_id: str,
    card_id: UUID,
    *,
    due_in: timedelta = timedelta(0),
    interval_days: int = 0,
) -> None:
    db.add(
        models.CardState(
            user_id=user_id,
            card_id=card_id,
            interval_days=interval_days,
            due_at=datetime.now(UTC) + due_in,
        )
    )
    await db.commit()  # releases the savepoint only
