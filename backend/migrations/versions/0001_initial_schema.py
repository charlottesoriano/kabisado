"""Initial schema: twelve tables in schema ``app``, pgvector, indexes, RLS, no client grants.

Source of truth: MDs/05-database-schema.md sections 4-5. Constraint names follow the naming
convention in app/db/base.py; index names are the spec's.

Revision ID: 0001
Revises:
Create Date: 2026-11-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = "app"

TABLES = (
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


def _now() -> sa.TextClause:
    return sa.text("now()")


def _uuid_pk() -> sa.Column:
    return sa.Column(
        "id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"),
        nullable=False,
    )


def _fk(col: str, table: str, target: str, ondelete: str = "CASCADE") -> sa.ForeignKeyConstraint:
    ref_table, ref_col = target.split(".")
    return sa.ForeignKeyConstraint(
        [col], [f"{SCHEMA}.{ref_table}.{ref_col}"],
        name=op.f(f"fk_{table}_{col}_{ref_table}"), ondelete=ondelete,
    )


def upgrade() -> None:
    op.execute("create extension if not exists vector")
    op.execute("create extension if not exists pgcrypto")
    op.execute(f"create schema if not exists {SCHEMA}")

    # Profiles ---------------------------------------------------------------------------------
    op.create_table(
        "profiles",
        sa.Column("id", sa.Text(), nullable=False),  # Clerk user id (token `sub`)
        sa.Column("email", sa.Text()),
        sa.Column("display_name", sa.Text()),
        sa.Column("timezone", sa.Text(), server_default="Asia/Manila", nullable=False),
        sa.Column("reminder_time", sa.Time()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_profiles")),
        schema=SCHEMA,
    )

    # Documents (decks) ------------------------------------------------------------------------
    op.create_table(
        "documents",
        _uuid_pk(),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("file_path", sa.Text()),
        sa.Column("raw_text", sa.Text()),
        sa.Column("page_count", sa.Integer()),
        sa.Column(
            "generate_kinds", postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{flashcard,mcq,problem}'"), nullable=False,
        ),
        sa.Column("status", sa.Text(), server_default="queued", nullable=False),
        sa.Column("error_code", sa.Text()),
        sa.Column("progress_done", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("progress_total", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
        _fk("user_id", "documents", "profiles.id"),
        sa.CheckConstraint(
            "char_length(title) between 1 and 120", name=op.f("ck_documents_title_length")
        ),
        sa.CheckConstraint("source_type in ('pdf', 'text')", name=op.f("ck_documents_source_type")),
        sa.CheckConstraint("page_count between 1 and 50", name=op.f("ck_documents_page_count")),
        sa.CheckConstraint(
            "status in ('queued', 'extracting', 'chunking', 'generating', 'ready', 'failed')",
            name=op.f("ck_documents_status"),
        ),
        sa.CheckConstraint(
            "(source_type = 'pdf' and file_path is not null) or "
            "(source_type = 'text' and raw_text is not null "
            "and char_length(raw_text) between 200 and 100000)",
            name=op.f("ck_documents_source_content"),
        ),
        sa.CheckConstraint(
            "progress_done between 0 and progress_total", name=op.f("ck_documents_progress")
        ),
        schema=SCHEMA,
    )

    # Chunks -----------------------------------------------------------------------------------
    op.create_table(
        "chunks",
        _uuid_pk(),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("heading", sa.Text()),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=False),
        sa.Column("page_end", sa.Integer(), nullable=False),
        sa.Column("is_quantitative", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_programming", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("embedding", Vector(384)),
        sa.Column("gen_status", sa.Text(), server_default="pending", nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chunks")),
        _fk("document_id", "chunks", "documents.id"),
        sa.UniqueConstraint("document_id", "idx", name=op.f("uq_chunks_document_id")),
        sa.CheckConstraint("page_end >= page_start", name=op.f("ck_chunks_page_range")),
        sa.CheckConstraint(
            "gen_status in ('pending', 'done', 'failed')", name=op.f("ck_chunks_gen_status")
        ),
        schema=SCHEMA,
    )

    # Cards ------------------------------------------------------------------------------------
    op.create_table(
        "cards",
        _uuid_pk(),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True)),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("topic", sa.Text()),
        sa.Column("origin", sa.Text(), server_default="bulk", nullable=False),
        sa.Column("flagged", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("flag_reason", sa.Text()),
        sa.Column("edited", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("model", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cards")),
        _fk("document_id", "cards", "documents.id"),
        _fk("chunk_id", "cards", "chunks.id", ondelete="SET NULL"),
        sa.CheckConstraint("type in ('flashcard', 'mcq', 'problem')", name=op.f("ck_cards_type")),
        sa.CheckConstraint("origin in ('bulk', 'topic')", name=op.f("ck_cards_origin")),
        sa.CheckConstraint(
            "flag_reason in ('wrong_answer', 'unclear', 'off_topic')", name=op.f("ck_cards_flag_reason")
        ),
        schema=SCHEMA,
    )

    # SM-2 state -------------------------------------------------------------------------------
    op.create_table(
        "card_states",
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("card_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ease", sa.Numeric(4, 2), server_default=sa.text("2.50"), nullable=False),
        sa.Column("interval_days", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("repetitions", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("user_id", "card_id", name=op.f("pk_card_states")),
        _fk("user_id", "card_states", "profiles.id"),
        _fk("card_id", "card_states", "cards.id"),
        sa.CheckConstraint("ease >= 1.30", name=op.f("ck_card_states_ease_min")),
        sa.CheckConstraint("interval_days >= 0", name=op.f("ck_card_states_interval_days")),
        sa.CheckConstraint("repetitions >= 0", name=op.f("ck_card_states_repetitions")),
        schema=SCHEMA,
    )

    op.create_table(
        "reviews",
        _uuid_pk(),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("card_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),  # Again, Hard, Good, Easy
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("interval_before", sa.Integer(), nullable=False),
        sa.Column("interval_after", sa.Integer(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reviews")),
        _fk("user_id", "reviews", "profiles.id"),
        _fk("card_id", "reviews", "cards.id"),
        sa.CheckConstraint("rating between 0 and 3", name=op.f("ck_reviews_rating")),
        sa.CheckConstraint("source in ('review', 'quiz', 'problem')", name=op.f("ck_reviews_source")),
        schema=SCHEMA,
    )

    # Quiz and problem sessions ----------------------------------------------------------------
    op.create_table(
        "attempts",
        _uuid_pk(),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("length", sa.SmallInteger(), nullable=False),
        sa.Column("score", sa.Integer()),
        sa.Column("total", sa.Integer()),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_attempts")),
        _fk("user_id", "attempts", "profiles.id"),
        _fk("document_id", "attempts", "documents.id"),
        sa.CheckConstraint("kind in ('quiz', 'problem_set')", name=op.f("ck_attempts_kind")),
        sa.CheckConstraint("score >= 0", name=op.f("ck_attempts_score")),
        sa.CheckConstraint("total >= 0", name=op.f("ck_attempts_total")),
        sa.CheckConstraint(
            "(kind = 'quiz' and length in (5, 10, 20)) or "
            "(kind = 'problem_set' and length in (5, 10))",
            name=op.f("ck_attempts_length"),
        ),
        sa.CheckConstraint(
            "score is null or total is null or score <= total", name=op.f("ck_attempts_score_le_total")
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "attempt_questions",
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.Column("card_id", postgresql.UUID(as_uuid=True), nullable=False),
        # shown index -> original index, e.g. {2,0,3,1}
        sa.Column("option_order", postgresql.ARRAY(sa.SmallInteger()), nullable=False),
        sa.PrimaryKeyConstraint("attempt_id", "position", name=op.f("pk_attempt_questions")),
        _fk("attempt_id", "attempt_questions", "attempts.id"),
        _fk("card_id", "attempt_questions", "cards.id"),
        sa.UniqueConstraint("attempt_id", "card_id", name=op.f("uq_attempt_questions_attempt_id")),
        schema=SCHEMA,
    )

    op.create_table(
        "problem_instances",
        _uuid_pk(),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("card_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variables", postgresql.JSONB(), nullable=False),
        sa.Column("variant_index", sa.SmallInteger()),
        sa.Column("answer_value", sa.Numeric()),  # never sent before grading
        sa.Column("answer_unit", sa.Text()),
        sa.Column("hints_shown", sa.SmallInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "solution_viewed", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_problem_instances")),
        _fk("attempt_id", "problem_instances", "attempts.id"),
        _fk("card_id", "problem_instances", "cards.id"),
        schema=SCHEMA,
    )

    op.create_table(
        "attempt_answers",
        _uuid_pk(),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("card_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instance_id", postgresql.UUID(as_uuid=True)),
        sa.Column("chosen_index", sa.SmallInteger()),  # quiz: original option index
        sa.Column("answer_value", sa.Numeric()),  # problem: converted to the expected unit
        sa.Column("answer_unit", sa.Text()),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("hints_used", sa.SmallInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("explanation", sa.Text()),  # cached "Explain my mistake"
        sa.Column("answered_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_attempt_answers")),
        _fk("attempt_id", "attempt_answers", "attempts.id"),
        _fk("card_id", "attempt_answers", "cards.id"),
        _fk("instance_id", "attempt_answers", "problem_instances.id"),
        sa.CheckConstraint("chosen_index between 0 and 3", name=op.f("ck_attempt_answers_chosen_index")),
        sa.CheckConstraint(
            "result in ('correct', 'close', 'wrong')", name=op.f("ck_attempt_answers_result")
        ),
        schema=SCHEMA,
    )

    # One answer per quiz question per attempt; one answer per problem instance.
    op.create_index(
        "attempt_answers_quiz_once", "attempt_answers", ["attempt_id", "card_id"],
        unique=True, schema=SCHEMA, postgresql_where=sa.text("instance_id is null"),
    )
    op.create_index(
        "attempt_answers_instance_once", "attempt_answers", ["instance_id"],
        unique=True, schema=SCHEMA, postgresql_where=sa.text("instance_id is not null"),
    )

    # Job metrics and webhooks -----------------------------------------------------------------
    op.create_table(
        "generation_runs",
        _uuid_pk(),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column(
            "provider_calls", postgresql.JSONB(), server_default=sa.text("'{}'"), nullable=False
        ),
        sa.Column("cards_kept", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("cards_dropped", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "template_failures", postgresql.JSONB(), server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_generation_runs")),
        _fk("document_id", "generation_runs", "documents.id"),
        schema=SCHEMA,
    )

    op.create_table(
        "webhook_events",
        sa.Column("svix_id", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=_now(), nullable=False),
        sa.PrimaryKeyConstraint("svix_id", name=op.f("pk_webhook_events")),
        schema=SCHEMA,
    )

    # Indexes (05 section 5) -------------------------------------------------------------------
    op.create_index(
        "chunks_embedding_hnsw", "chunks", ["embedding"], schema=SCHEMA,
        postgresql_using="hnsw", postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index("card_states_due", "card_states", ["user_id", "due_at"], schema=SCHEMA)
    op.create_index(
        "cards_doc_type", "cards", ["document_id", "type"], schema=SCHEMA,
        postgresql_where=sa.text("not flagged"),
    )
    op.create_index("answers_card_time", "attempt_answers", ["card_id", "answered_at"], schema=SCHEMA)
    op.create_index(
        "documents_user", "documents", ["user_id", sa.text("created_at desc")], schema=SCHEMA
    )
    op.create_index("reviews_user_time", "reviews", ["user_id", "reviewed_at"], schema=SCHEMA)
    op.create_index(
        "attempts_user_doc", "attempts",
        ["user_id", "document_id", sa.text("started_at desc")], schema=SCHEMA,
    )

    # RLS on, no policies: client roles can never read or write. -------------------------------
    for table in TABLES:
        op.execute(f"alter table {SCHEMA}.{table} enable row level security")

    # No grants to Supabase's client roles. Guarded so the migration also runs on plain Postgres,
    # where these roles don't exist. Default privileges cover tables added by later migrations.
    op.execute(
        f"""
        do $$
        declare r text;
        begin
          foreach r in array array['anon', 'authenticated'] loop
            if exists (select 1 from pg_roles where rolname = r) then
              execute format('revoke all on schema {SCHEMA} from %I', r);
              execute format('revoke all on all tables in schema {SCHEMA} from %I', r);
              execute format(
                'alter default privileges in schema {SCHEMA} revoke all on tables from %I', r
              );
            end if;
          end loop;
        end
        $$
        """
    )


def downgrade() -> None:
    # Extensions (shared with Supabase) and the schema (holds alembic_version) are kept.
    # Dropping a table drops its indexes, constraints and RLS setting.
    for table in reversed(TABLES):
        op.drop_table(table, schema=SCHEMA)
