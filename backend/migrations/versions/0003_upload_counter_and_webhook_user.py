"""Per-user daily upload counter on profiles; user id on webhook events.

- ``profiles.uploads_day`` / ``uploads_count``: the daily upload limit (PDFs and pasted notes)
  is counted here, not from ``documents``, so deleting a deck doesn't free a slot. The counter
  is bumped with one atomic ``UPDATE ... RETURNING`` in the same transaction as the document
  insert (app/services/ratelimit.py).
- ``webhook_events.user_id``: the Clerk user an event is about, so a late ``user.created`` /
  ``user.updated`` arriving after ``user.deleted`` can be ignored instead of recreating the
  profile.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = "app"


def upgrade() -> None:
    op.add_column("profiles", sa.Column("uploads_day", sa.Date()), schema=SCHEMA)
    op.add_column(
        "profiles",
        sa.Column("uploads_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        schema=SCHEMA,
    )
    op.create_check_constraint(
        op.f("ck_profiles_uploads_count"), "profiles", "uploads_count >= 0", schema=SCHEMA
    )
    op.add_column("webhook_events", sa.Column("user_id", sa.Text()), schema=SCHEMA)
    op.create_index(
        "webhook_events_deleted_user",
        "webhook_events",
        ["user_id"],
        schema=SCHEMA,
        postgresql_where=sa.text("event_type = 'user.deleted'"),
    )


def downgrade() -> None:
    op.drop_index("webhook_events_deleted_user", table_name="webhook_events", schema=SCHEMA)
    op.drop_column("webhook_events", "user_id", schema=SCHEMA)
    op.drop_constraint(
        op.f("ck_profiles_uploads_count"), "profiles", type_="check", schema=SCHEMA
    )
    op.drop_column("profiles", "uploads_count", schema=SCHEMA)
    op.drop_column("profiles", "uploads_day", schema=SCHEMA)
