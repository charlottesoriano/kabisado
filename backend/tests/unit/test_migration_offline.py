"""Render the migration as SQL (Alembic offline mode, no database) and check it against 05 and
against the ORM models, so the two can't drift apart."""

import io
import re
from collections.abc import Callable

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from app.db.base import Base
from app.db.models import TABLES

DUMMY_URL = "postgresql+asyncpg://user:pass@localhost:5432/db"


def _render(make: Callable[[str], Config], *args: str) -> str:
    cfg = make(DUMMY_URL)
    buf = io.StringIO()
    cfg.output_buffer = buf
    if args[0] == "upgrade":
        command.upgrade(cfg, args[1], sql=True)
    else:
        command.downgrade(cfg, args[1], sql=True)
    return buf.getvalue()


def _norm(sql: str) -> str:
    return re.sub(r"\s+", " ", sql).strip()


def _table_body_lines(sql: str, table: str) -> set[str]:
    match = re.search(rf"CREATE TABLE app\.{table} \((.*?)\n\)", sql, re.S)
    assert match, f"no CREATE TABLE for {table}"
    lines = {line.strip().rstrip(",") for line in match.group(1).splitlines() if line.strip()}
    # Columns/constraints added by later migrations (ALTER TABLE ... ADD ...).
    for added in re.findall(rf"ALTER TABLE app\.{table} ADD (?:COLUMN )?(.+?);", sql):
        lines.add(added.strip())
    return lines


@pytest.fixture
def upgrade_sql(alembic_config: Callable[[str], Config]) -> str:
    return _render(alembic_config, "upgrade", "head")


@pytest.mark.unit
def test_extensions_schema_and_tables(upgrade_sql: str) -> None:
    sql = upgrade_sql.lower()
    assert "create extension if not exists vector" in sql
    assert "create extension if not exists pgcrypto" in sql
    assert "create schema if not exists app" in sql
    for table in TABLES:
        assert f"create table app.{table} (" in sql


@pytest.mark.unit
def test_rls_on_every_table_with_no_policies(upgrade_sql: str) -> None:
    sql = upgrade_sql.lower()
    for table in TABLES:
        assert f"alter table app.{table} enable row level security" in sql
    assert "create policy" not in sql


@pytest.mark.unit
def test_client_roles_revoked(upgrade_sql: str) -> None:
    sql = _norm(upgrade_sql.lower())
    assert "array['anon', 'authenticated']" in sql
    assert "revoke all on schema app from %i" in sql
    assert "revoke all on all tables in schema app from %i" in sql
    assert "alter default privileges in schema app revoke all on tables from %i" in sql
    assert "grant " not in sql


@pytest.mark.unit
def test_migration_matches_models(upgrade_sql: str) -> None:
    dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
    for table in Base.metadata.sorted_tables:
        model_sql = str(CreateTable(table).compile(dialect=dialect))
        assert _table_body_lines(upgrade_sql, table.name) == _table_body_lines(
            model_sql, table.name
        ), table.name
        for index in table.indexes:
            model_index = _norm(str(CreateIndex(index).compile(dialect=dialect)))
            assert model_index.lower() in _norm(upgrade_sql).lower(), index.name


@pytest.mark.unit
def test_downgrade_drops_tables_keeps_extensions_and_schema(
    alembic_config: Callable[[str], Config],
) -> None:
    sql = _render(alembic_config, "downgrade", "head:base").lower()
    for table in TABLES:
        assert f"drop table app.{table}" in sql
    assert "drop extension" not in sql
    assert "drop schema app" not in sql
    assert "drop schema if exists app" not in sql
    assert "drop schema if exists procrastinate cascade" in sql
    # Dependents are dropped before what they reference.
    assert sql.index("drop table app.attempt_answers") < sql.index(
        "drop table app.problem_instances"
    )
    assert sql.index("drop table app.documents") < sql.index("drop table app.profiles")


@pytest.mark.unit
def test_procrastinate_schema_is_private(upgrade_sql: str) -> None:
    sql = _norm(upgrade_sql.lower())
    assert "create schema if not exists procrastinate" in sql
    assert "set local search_path to procrastinate" in sql
    assert "create table procrastinate_jobs" in sql
    assert "reset search_path" in sql
    assert "alter table procrastinate.%i enable row level security" in sql
    assert "revoke all on schema procrastinate from %i" in sql
    assert "revoke all on all functions in schema procrastinate from %i" in sql
