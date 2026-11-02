"""ORM models for the twelve tables in MDs/05-database-schema.md section 3.

The database schema is defined by migrations/versions/0001_initial_schema.py; these models mirror
it column for column. Allowed values are ``text`` columns with ``CHECK`` constraints (not enums);
the value lists live here as ``Literal`` types so the API's Pydantic models can reuse them.

No ``relationship()``s on purpose: every query is written explicitly and scoped to the Clerk user
id (directly or through ``documents.user_id``).
"""

from datetime import datetime, time
from decimal import Decimal
from typing import Any, Literal, get_args
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    Time,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import SCHEMA, Base

EMBEDDING_DIM = 384

# Allowed values (CHECK constraints) ------------------------------------------------------------
SourceType = Literal["pdf", "text"]
DocumentStatus = Literal["queued", "extracting", "chunking", "generating", "ready", "failed"]
ChunkGenStatus = Literal["pending", "done", "failed"]
CardType = Literal["flashcard", "mcq", "problem"]
CardOrigin = Literal["bulk", "topic"]
FlagReason = Literal["wrong_answer", "unclear", "off_topic"]
ReviewSource = Literal["review", "quiz", "problem"]
AttemptKind = Literal["quiz", "problem_set"]
AnswerResult = Literal["correct", "close", "wrong"]

QUIZ_LENGTHS = (5, 10, 20)
PROBLEM_SET_LENGTHS = (5, 10)


def _in(column: str, allowed: Any) -> str:
    """SQL for ``column in ('a', 'b', ...)`` built from a ``Literal`` type or a tuple of ints."""
    values = get_args(allowed) or tuple(allowed)
    rendered = ", ".join(f"'{v}'" if isinstance(v, str) else str(v) for v in values)
    return f"{column} in ({rendered})"


def _fk(target: str, ondelete: str = "CASCADE") -> ForeignKey:
    return ForeignKey(f"{SCHEMA}.{target}", ondelete=ondelete)


def _uuid_pk() -> Mapped[UUID]:
    return mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )


def _created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


def _updated_at() -> Mapped[datetime]:
    return mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


# Profiles ---------------------------------------------------------------------------------------
class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(Text, primary_key=True)  # Clerk user id (token `sub`)
    email: Mapped[str | None] = mapped_column(Text)
    display_name: Mapped[str | None] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(Text, nullable=False, server_default="Asia/Manila")
    reminder_time: Mapped[time | None] = mapped_column(Time)
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


# Documents (decks) ------------------------------------------------------------------------------
class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint("char_length(title) between 1 and 120", name="title_length"),
        CheckConstraint(_in("source_type", SourceType), name="source_type"),
        CheckConstraint("page_count between 1 and 50", name="page_count"),
        CheckConstraint(_in("status", DocumentStatus), name="status"),
        CheckConstraint(
            "(source_type = 'pdf' and file_path is not null) or "
            "(source_type = 'text' and raw_text is not null "
            "and char_length(raw_text) between 200 and 100000)",
            name="source_content",
        ),
        CheckConstraint("progress_done between 0 and progress_total", name="progress"),
    )

    id: Mapped[UUID] = _uuid_pk()
    user_id: Mapped[str] = mapped_column(Text, _fk("profiles.id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[SourceType] = mapped_column(Text, nullable=False)
    file_path: Mapped[str | None] = mapped_column(Text)  # set for pdf
    raw_text: Mapped[str | None] = mapped_column(Text)  # set for text
    page_count: Mapped[int | None] = mapped_column(Integer)
    generate_kinds: Mapped[list[CardType]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{flashcard,mcq,problem}'")
    )
    status: Mapped[DocumentStatus] = mapped_column(Text, nullable=False, server_default="queued")
    error_code: Mapped[str | None] = mapped_column(Text)
    progress_done: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    progress_total: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


# Chunks -----------------------------------------------------------------------------------------
class Chunk(Base):
    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "idx"),
        CheckConstraint("page_end >= page_start", name="page_range"),
        CheckConstraint(_in("gen_status", ChunkGenStatus), name="gen_status"),
        Index(
            "chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[UUID] = _uuid_pk()
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), _fk("documents.id"), nullable=False
    )
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    heading: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    page_start: Mapped[int] = mapped_column(Integer, nullable=False)
    page_end: Mapped[int] = mapped_column(Integer, nullable=False)
    is_quantitative: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    is_programming: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    # pgvector returns a numpy array; pass a list[float] of length EMBEDDING_DIM when writing.
    embedding: Mapped[Any] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    gen_status: Mapped[ChunkGenStatus] = mapped_column(
        Text, nullable=False, server_default="pending"
    )


# Cards ------------------------------------------------------------------------------------------
class Card(Base):
    __tablename__ = "cards"
    __table_args__ = (
        CheckConstraint(_in("type", CardType), name="type"),
        CheckConstraint(_in("origin", CardOrigin), name="origin"),
        CheckConstraint(_in("flag_reason", FlagReason), name="flag_reason"),
        Index("cards_doc_type", "document_id", "type", postgresql_where=text("not flagged")),
    )

    id: Mapped[UUID] = _uuid_pk()
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), _fk("documents.id"), nullable=False
    )
    chunk_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), _fk("chunks.id", ondelete="SET NULL")
    )
    type: Mapped[CardType] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)  # shape per type, §6
    topic: Mapped[str | None] = mapped_column(Text)
    origin: Mapped[CardOrigin] = mapped_column(Text, nullable=False, server_default="bulk")
    flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    flag_reason: Mapped[FlagReason | None] = mapped_column(Text)
    edited: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    model: Mapped[str | None] = mapped_column(Text)  # generator provider/model
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


# SM-2 state -------------------------------------------------------------------------------------
class CardState(Base):
    __tablename__ = "card_states"
    __table_args__ = (
        CheckConstraint("ease >= 1.30", name="ease_min"),
        CheckConstraint("interval_days >= 0", name="interval_days"),
        CheckConstraint("repetitions >= 0", name="repetitions"),
        Index("card_states_due", "user_id", "due_at"),
    )

    user_id: Mapped[str] = mapped_column(Text, _fk("profiles.id"), primary_key=True)
    card_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), _fk("cards.id"), primary_key=True)
    ease: Mapped[Decimal] = mapped_column(
        Numeric(4, 2), nullable=False, server_default=text("2.50")
    )
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    repetitions: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    due_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating between 0 and 3", name="rating"),  # Again, Hard, Good, Easy
        CheckConstraint(_in("source", ReviewSource), name="source"),
        Index("reviews_user_time", "user_id", "reviewed_at"),
    )

    id: Mapped[UUID] = _uuid_pk()
    user_id: Mapped[str] = mapped_column(Text, _fk("profiles.id"), nullable=False)
    card_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), _fk("cards.id"), nullable=False)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    source: Mapped[ReviewSource] = mapped_column(Text, nullable=False)
    interval_before: Mapped[int] = mapped_column(Integer, nullable=False)
    interval_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# Quiz and problem sessions ----------------------------------------------------------------------
class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (
        CheckConstraint(_in("kind", AttemptKind), name="kind"),
        CheckConstraint("score >= 0", name="score"),
        CheckConstraint("total >= 0", name="total"),
        CheckConstraint(
            f"(kind = 'quiz' and {_in('length', QUIZ_LENGTHS)}) or "
            f"(kind = 'problem_set' and {_in('length', PROBLEM_SET_LENGTHS)})",
            name="length",
        ),
        CheckConstraint("score is null or total is null or score <= total", name="score_le_total"),
    )

    id: Mapped[UUID] = _uuid_pk()
    user_id: Mapped[str] = mapped_column(Text, _fk("profiles.id"), nullable=False)
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), _fk("documents.id"), nullable=False
    )
    kind: Mapped[AttemptKind] = mapped_column(Text, nullable=False)
    length: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    score: Mapped[int | None] = mapped_column(Integer)
    total: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AttemptQuestion(Base):
    __tablename__ = "attempt_questions"
    __table_args__ = (UniqueConstraint("attempt_id", "card_id"),)

    attempt_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), _fk("attempts.id"), primary_key=True
    )
    position: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    card_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), _fk("cards.id"), nullable=False)
    # shown index -> original index, e.g. [2, 0, 3, 1]
    option_order: Mapped[list[int]] = mapped_column(ARRAY(SmallInteger), nullable=False)


class ProblemInstance(Base):
    __tablename__ = "problem_instances"

    id: Mapped[UUID] = _uuid_pk()
    attempt_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), _fk("attempts.id"), nullable=False
    )
    card_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), _fk("cards.id"), nullable=False)
    variables: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    variant_index: Mapped[int | None] = mapped_column(SmallInteger)  # programming problems
    # Computed by SymPy/Pint; never sent before grading.
    answer_value: Mapped[float | None] = mapped_column(Numeric(asdecimal=False))
    answer_unit: Mapped[str | None] = mapped_column(Text)
    hints_shown: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"))
    solution_viewed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = _created_at()


class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"
    __table_args__ = (
        CheckConstraint("chosen_index between 0 and 3", name="chosen_index"),
        CheckConstraint(_in("result", AnswerResult), name="result"),
        # One answer per quiz question per attempt; one answer per problem instance.
        Index(
            "attempt_answers_quiz_once",
            "attempt_id",
            "card_id",
            unique=True,
            postgresql_where=text("instance_id is null"),
        ),
        Index(
            "attempt_answers_instance_once",
            "instance_id",
            unique=True,
            postgresql_where=text("instance_id is not null"),
        ),
        Index("answers_card_time", "card_id", "answered_at"),
    )

    id: Mapped[UUID] = _uuid_pk()
    attempt_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), _fk("attempts.id"), nullable=False
    )
    card_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), _fk("cards.id"), nullable=False)
    instance_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), _fk("problem_instances.id")
    )
    chosen_index: Mapped[int | None] = mapped_column(SmallInteger)  # quiz: original option index
    # Problem: converted to the expected unit.
    answer_value: Mapped[float | None] = mapped_column(Numeric(asdecimal=False))
    answer_unit: Mapped[str | None] = mapped_column(Text)
    result: Mapped[AnswerResult] = mapped_column(Text, nullable=False)
    hints_used: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"))
    explanation: Mapped[str | None] = mapped_column(Text)  # cached "Explain my mistake"
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# Job metrics and webhooks -----------------------------------------------------------------------
class GenerationRun(Base):
    __tablename__ = "generation_runs"

    id: Mapped[UUID] = _uuid_pk()
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), _fk("documents.id"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider_calls: Mapped[dict[str, int]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'")
    )
    cards_kept: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    cards_dropped: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    template_failures: Mapped[dict[str, int]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'")
    )


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    svix_id: Mapped[str] = mapped_column(Text, primary_key=True)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# Indexes with descending columns (need the mapped columns, so declared after the classes).
Index("documents_user", Document.user_id, Document.created_at.desc())
Index("attempts_user_doc", Attempt.user_id, Attempt.document_id, Attempt.started_at.desc())

TABLES: tuple[str, ...] = (
    "profiles",
    "documents",
    "chunks",
    "cards",
    "card_states",
    "reviews",
    "attempts",
    "attempt_questions",
    "problem_instances",
    "attempt_answers",
    "generation_runs",
    "webhook_events",
)
