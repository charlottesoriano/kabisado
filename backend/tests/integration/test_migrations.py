"""Migration upgrade/downgrade and RLS against a real Postgres with pgvector.

Skipped unless ``TEST_DATABASE_URL`` is set. The database must be disposable: the test
downgrades to base, which drops every table in schema ``app``. See backend/README.md.
"""

import os
from collections.abc import Callable, Iterator

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import ProgrammingError

from app.db.base import SCHEMA, Base
from app.db.models import TABLES
from app.jobs.app import _libpq_url

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL is not set"),
]


def _with_driver(url: str, driver: str) -> str:
    return f"postgresql+{driver}://" + _libpq_url(url).removeprefix("postgresql://")


@pytest.fixture
def migrated(alembic_config: Callable[[str], Config]) -> Iterator[Config]:
    cfg = alembic_config(_with_driver(TEST_DATABASE_URL, "asyncpg"))
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    yield cfg


@pytest.fixture
def engine(migrated: Config) -> Iterator[Engine]:
    # Sync psycopg engine: these checks don't need async.
    eng = create_engine(_with_driver(TEST_DATABASE_URL, "psycopg"))
    yield eng
    eng.dispose()


def test_all_tables_have_rls_and_no_policies(engine: Engine) -> None:
    with engine.connect() as conn:
        rls = dict(
            conn.execute(
                text(
                    "select c.relname, c.relrowsecurity from pg_class c "
                    "join pg_namespace n on n.oid = c.relnamespace "
                    "where n.nspname = :s and c.relkind = 'r' and c.relname <> 'alembic_version'"
                ),
                {"s": SCHEMA},
            ).all()
        )
        policies = conn.execute(
            text("select count(*) from pg_policies where schemaname = :s"), {"s": SCHEMA}
        ).scalar_one()
    assert rls == dict.fromkeys(TABLES, True)
    assert policies == 0


def test_client_role_cannot_read(engine: Engine) -> None:
    """BE-SEC-04: as a client role, ``select * from app.cards`` is denied."""
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            has_authenticated = conn.execute(
                text("select exists (select 1 from pg_roles where rolname = 'authenticated')")
            ).scalar_one()
            if has_authenticated:
                conn.execute(text("set local role authenticated"))
            else:  # plain Postgres: a throwaway role with no grants (rolled back below)
                conn.execute(text("create role kabisado_test_client nologin"))
                conn.execute(text("set local role kabisado_test_client"))
            with pytest.raises(ProgrammingError, match="permission denied"):
                conn.execute(text("select * from app.cards"))
        finally:
            trans.rollback()


def test_models_match_migrated_schema(engine: Engine) -> None:
    def include_name(name: str | None, type_: str, parent_names: object) -> bool:
        return name == SCHEMA if type_ == "schema" else True

    with engine.connect() as conn:
        ctx = MigrationContext.configure(
            conn, opts={"include_schemas": True, "include_name": include_name}
        )
        diff = [d for d in compare_metadata(ctx, Base.metadata) if "alembic_version" not in str(d)]
    assert diff == []
