"""Procrastinate app (Postgres-backed job queue).

Procrastinate uses psycopg 3 (the API itself uses asyncpg). The connection string comes from
``WORKER_DATABASE_URL`` (falling back to ``DATABASE_URL``); the SQLAlchemy driver suffix
(``+asyncpg``) is stripped because psycopg expects a plain libpq URL. Nothing connects until the
app is opened.

Procrastinate's tables live in the private ``procrastinate`` schema (migration 0002), so every
pooled connection sets ``search_path`` to it when the pool opens it.

Run the worker with::

    uv run procrastinate --app=app.jobs.app.app worker
"""

import asyncio
import sys

import psycopg
from procrastinate import App, PsycopgConnector

from app.config import get_settings


def use_selector_loop_on_windows() -> None:
    """psycopg's async mode can't use the Windows Proactor loop; call this in the worker/tests."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def _libpq_url(url: str) -> str:
    for prefix in ("postgresql+asyncpg://", "postgresql+psycopg://"):
        if url.startswith(prefix):
            return "postgresql://" + url[len(prefix) :]
    return url


PROCRASTINATE_SCHEMA = "procrastinate"


async def _use_procrastinate_schema(conn: psycopg.AsyncConnection) -> None:
    await conn.execute(f"set search_path to {PROCRASTINATE_SCHEMA}")
    await conn.commit()


def _conninfo() -> str:
    settings = get_settings()
    return _libpq_url(settings.worker_database_url or settings.database_url)


app = App(
    connector=PsycopgConnector(conninfo=_conninfo(), configure=_use_procrastinate_schema),
    import_paths=["app.jobs.generate_document"],
)
