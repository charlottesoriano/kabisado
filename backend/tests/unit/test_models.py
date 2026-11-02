"""The ORM models match MDs/05-database-schema.md (no database needed)."""

import re

import pytest
from sqlalchemy import CheckConstraint, Index
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from app.db import models
from app.db.base import SCHEMA, Base

SPEC_TABLES = {
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
}

SPEC_INDEXES = {
    "chunks_embedding_hnsw",
    "card_states_due",
    "cards_doc_type",
    "answers_card_time",
    "documents_user",
    "reviews_user_time",
    "attempts_user_doc",
    "attempt_answers_quiz_once",
    "attempt_answers_instance_once",
    "webhook_events_deleted_user",  # migration 0003 (webhook ordering)
}


def _ddl() -> str:
    dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
    parts = [str(CreateTable(t).compile(dialect=dialect)) for t in Base.metadata.sorted_tables]
    for table in Base.metadata.sorted_tables:
        parts += [str(CreateIndex(i).compile(dialect=dialect)) for i in table.indexes]
    return "\n".join(parts)


@pytest.mark.unit
def test_exactly_the_twelve_tables_in_app_schema() -> None:
    names = {t.name for t in Base.metadata.sorted_tables}
    assert names == SPEC_TABLES
    assert set(models.TABLES) == SPEC_TABLES
    assert all(t.schema == SCHEMA for t in Base.metadata.sorted_tables)


@pytest.mark.unit
def test_spec_indexes_exist() -> None:
    names = {i.name for t in Base.metadata.sorted_tables for i in t.indexes}
    assert names == SPEC_INDEXES


@pytest.mark.unit
def test_hnsw_and_partial_indexes() -> None:
    ddl = _ddl()
    assert (
        "CREATE INDEX chunks_embedding_hnsw ON app.chunks USING hnsw (embedding vector_cosine_ops)"
        in ddl
    )
    assert "CREATE INDEX cards_doc_type ON app.cards (document_id, type) WHERE not flagged" in ddl
    assert (
        "CREATE UNIQUE INDEX attempt_answers_quiz_once ON app.attempt_answers "
        "(attempt_id, card_id) WHERE instance_id is null" in ddl
    )
    assert "CREATE INDEX documents_user ON app.documents (user_id, created_at DESC)" in ddl


@pytest.mark.unit
def test_user_ids_are_text_and_embedding_is_384() -> None:
    ddl = _ddl()
    assert "id TEXT NOT NULL" in ddl  # profiles.id is the Clerk id
    assert ddl.count("user_id TEXT NOT NULL") == 4  # documents, card_states, reviews, attempts
    assert "embedding VECTOR(384)" in ddl


@pytest.mark.unit
def test_key_business_rule_checks() -> None:
    checks = {
        str(c.sqltext)
        for t in Base.metadata.sorted_tables
        for c in t.constraints
        if isinstance(c, CheckConstraint)
    }
    assert "ease >= 1.30" in checks
    assert "score is null or total is null or score <= total" in checks
    assert (
        "(kind = 'quiz' and length in (5, 10, 20)) or (kind = 'problem_set' and length in (5, 10))"
        in checks
    )
    assert "status in ('queued', 'extracting', 'chunking', 'generating', 'ready', 'failed')" in (
        checks
    )


@pytest.mark.unit
def test_every_constraint_gets_a_convention_name() -> None:
    names = re.findall(r"CONSTRAINT (\w+)", _ddl())
    assert len(names) == len(set(names))
    assert all(n.split("_")[0] in {"pk", "fk", "ck", "uq"} for n in names)
    assert all(len(n) <= 63 for n in names)


@pytest.mark.unit
def test_cascades() -> None:
    fks = {
        (fk.parent.table.name, fk.parent.name): fk.ondelete
        for t in Base.metadata.sorted_tables
        for fk in t.foreign_keys
    }
    assert fks[("cards", "chunk_id")] == "SET NULL"
    assert all(v == "CASCADE" for k, v in fks.items() if k != ("cards", "chunk_id"))


@pytest.mark.unit
def test_indexes_are_index_objects() -> None:
    # Guards against an Index declared outside a table silently not attaching.
    assert all(isinstance(i, Index) for t in Base.metadata.sorted_tables for i in t.indexes)
