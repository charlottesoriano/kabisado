"""BE-SEC-03 / BE-SEC-04 sweep against the live database: Supabase's client roles (``anon``,
``authenticated``) can't use schema ``app`` or ``procrastinate`` and have no table privileges;
RLS is on for every table in both; the Data API doesn't expose either schema.

BE-SEC-03 is checked at the database level plus the local Supabase config (the REST call with
the anon key would need the running Supabase API and its key; see the QA report)."""

import tomllib
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import ProgrammingError

from app.config import BACKEND_DIR
from tests.conftest import TEST_DATABASE_URL, needs_db, with_driver

pytestmark = [pytest.mark.integration, pytest.mark.security, needs_db]

SCHEMAS = ("app", "procrastinate")
CLIENT_ROLES = ("anon", "authenticated")


@pytest.fixture
def engine(migrated_db: str) -> Iterator[Engine]:
    eng = create_engine(with_driver(TEST_DATABASE_URL, "psycopg"))
    yield eng
    eng.dispose()


def _roles(engine: Engine) -> list[str]:
    with engine.connect() as conn:
        present = conn.execute(
            text("select rolname from pg_roles where rolname = any(:r)"), {"r": list(CLIENT_ROLES)}
        ).scalars()
        roles = sorted(present)
    if not roles:
        pytest.skip("no Supabase client roles in this database (plain Postgres)")
    return roles


def test_client_roles_have_no_schema_or_table_privileges(engine: Engine) -> None:
    roles = _roles(engine)
    with engine.connect() as conn:
        tables = conn.execute(
            text(
                "select n.nspname, c.relname, c.oid, c.relrowsecurity from pg_class c "
                "join pg_namespace n on n.oid = c.relnamespace "
                "where n.nspname = any(:s) and c.relkind in ('r', 'p')"
            ),
            {"s": list(SCHEMAS)},
        ).all()
        assert {t.nspname for t in tables} == set(SCHEMAS)
        problems = []
        for role in roles:
            for schema in SCHEMAS:
                if conn.execute(
                    text("select has_schema_privilege(:r, :s, 'USAGE')"), {"r": role, "s": schema}
                ).scalar_one():
                    problems.append(f"{role} has USAGE on {schema}")
            for t in tables:
                for priv in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES"):
                    if conn.execute(
                        text("select has_table_privilege(:r, :o, :p)"),
                        {"r": role, "o": t.oid, "p": priv},
                    ).scalar_one():
                        problems.append(f"{role} has {priv} on {t.nspname}.{t.relname}")
        no_rls = [f"{t.nspname}.{t.relname}" for t in tables if not t.relrowsecurity]
    assert problems == []
    assert no_rls == []


@pytest.mark.parametrize(
    "sql",
    [
        "select * from app.documents",
        "select * from app.cards",
        "select * from app.profiles",
        "insert into app.profiles (id) values ('user_evil')",
        "select * from procrastinate.procrastinate_jobs",
    ],
)
def test_client_roles_are_denied(engine: Engine, sql: str) -> None:
    """BE-SEC-03/04: as anon and as authenticated, every query is permission denied."""
    for role in _roles(engine):
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                conn.execute(text(f"set local role {role}"))
                with pytest.raises(ProgrammingError, match="permission denied"):
                    conn.execute(text(sql))
            finally:
                trans.rollback()


def test_data_api_does_not_expose_private_schemas() -> None:
    """BE-SEC-03 (config side): the local Supabase API only exposes public/graphql_public."""
    config = BACKEND_DIR.parent / "supabase" / "config.toml"
    if not config.exists():
        pytest.skip("no supabase/config.toml")
    api = tomllib.loads(config.read_text(encoding="utf-8")).get("api", {})
    exposed = set(api.get("schemas", [])) | set(api.get("extra_search_path", []))
    assert not exposed & set(SCHEMAS), exposed
