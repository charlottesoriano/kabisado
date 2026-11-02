"""Procrastinate job queue in the private ``procrastinate`` schema, RLS on, no client grants.

The SQL is Procrastinate 3.10.0's own schema, vendored in ``migrations/sql/`` so this migration
never changes when the package is upgraded. Upgrading Procrastinate later means a new migration
that applies its bundled migration files for the versions in between.

The worker and API connections set ``search_path = procrastinate`` (app/jobs/app.py).

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-02
"""

from collections.abc import Sequence
from pathlib import Path

from alembic import context, op
from sqlalchemy import text

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = "procrastinate"
SQL_FILE = Path(__file__).resolve().parent.parent / "sql" / "procrastinate_3.10.0_schema.sql"


def _run_script(sql: str) -> None:
    """Multi-statement SQL with ``$$`` function bodies: asyncpg's simple-query protocol online,
    plain text when rendering ``--sql``."""
    if context.is_offline_mode():
        op.execute(text(sql))
        return
    dbapi_conn = op.get_bind().connection.dbapi_connection
    assert dbapi_conn is not None
    dbapi_conn.run_async(lambda driver_conn: driver_conn.execute(sql))  # type: ignore[attr-defined]


def upgrade() -> None:
    op.execute(f"create schema if not exists {SCHEMA}")
    op.execute(f"set local search_path to {SCHEMA}")
    _run_script(SQL_FILE.read_text(encoding="utf-8"))
    op.execute("reset search_path")

    # Procrastinate's functions and triggers name its tables without a schema. Pin their
    # search_path so they work from any connection (dashboards, scripts), not only ours.
    op.execute(
        f"""
        do $$
        declare f regprocedure;
        begin
          for f in select p.oid::regprocedure from pg_proc p
                   join pg_namespace n on n.oid = p.pronamespace
                   where n.nspname = '{SCHEMA}' loop
            execute format('alter function %s set search_path = {SCHEMA}', f);
          end loop;
        end
        $$
        """
    )

    # RLS on, no policies; no grants to Supabase's client roles (same locks as schema app).
    op.execute(
        f"""
        do $$
        declare t text;
        begin
          for t in select tablename from pg_tables where schemaname = '{SCHEMA}' loop
            execute format('alter table {SCHEMA}.%I enable row level security', t);
          end loop;
        end
        $$
        """
    )
    op.execute(
        f"""
        do $$
        declare r text;
        begin
          foreach r in array array['anon', 'authenticated'] loop
            if exists (select 1 from pg_roles where rolname = r) then
              execute format('revoke all on schema {SCHEMA} from %I', r);
              execute format('revoke all on all tables in schema {SCHEMA} from %I', r);
              execute format('revoke all on all sequences in schema {SCHEMA} from %I', r);
              execute format('revoke all on all functions in schema {SCHEMA} from %I', r);
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
    op.execute(f"drop schema if exists {SCHEMA} cascade")
