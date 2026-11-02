"""Async SQLAlchemy engine and session dependency (asyncpg, Supabase session pooler).

Every query must be scoped to the authenticated Clerk user id.

The engine is created lazily on first use, so the app and the tests start without
``DATABASE_URL``. Pool sizes come from config (``DB_POOL_SIZE``, ``DB_MAX_OVERFLOW``).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def asyncpg_url(url: str) -> str:
    """Force the asyncpg driver: a plain ``postgresql://`` URL would make SQLAlchemy 2.1 pick
    psycopg, whose async mode fails on the Windows Proactor loop."""
    for prefix in ("postgresql+psycopg://", "postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+asyncpg://" + url[len(prefix) :]
    return url


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        if not settings.database_url:
            raise RuntimeError("DATABASE_URL is not set")
        _engine = create_async_engine(
            asyncpg_url(settings.database_url),
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=True,
            hide_parameters=True,  # SQL errors must never echo note text into logs
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _sessionmaker


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request. Handlers commit explicitly."""
    async with get_sessionmaker()() as session:
        yield session


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """A session inside one transaction: commits on success, rolls back on error (worker use)."""
    async with get_sessionmaker()() as session, session.begin():
        yield session


async def dispose_engine() -> None:
    """Close pooled connections (app shutdown)."""
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None


SessionDep = Annotated[AsyncSession, Depends(get_session)]
