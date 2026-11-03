"""RLS on ``app.alembic_version`` (no policies), like every other table in schema ``app``.

Alembic creates its version table in ``app`` (migrations/env.py, ``version_table_schema``) before
0001 runs, so 0001 never enabled RLS on it. The schema-level revoke in 0001 already keeps the
client roles out; this is the second lock, and keeps Supabase's "RLS disabled" lint quiet.

The migration role owns the table, and owners bypass RLS (no ``force``), so Alembic still reads
and writes it. Guarded on the table existing so it also renders and runs on plain Postgres.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-03
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "app.alembic_version"


def _set_rls(action: str) -> None:
    op.execute(
        f"""
        do $$
        begin
          if to_regclass('{TABLE}') is not null then
            execute 'alter table {TABLE} {action} row level security';
          end if;
        end
        $$
        """
    )


def upgrade() -> None:
    _set_rls("enable")


def downgrade() -> None:
    _set_rls("disable")
