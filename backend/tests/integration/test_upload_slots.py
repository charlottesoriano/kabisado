"""The daily upload counter under concurrency: real committed rows, separate connections."""

import asyncio
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.config import get_settings
from app.db.models import Profile
from app.errors import UploadLimitReached
from app.services.ratelimit import take_upload_slot
from tests.conftest import needs_db

pytestmark = [pytest.mark.integration, needs_db]


@pytest.fixture
async def engine(migrated_db: str) -> AsyncIterator[AsyncEngine]:
    eng = create_async_engine(migrated_db, pool_size=12, max_overflow=0)
    yield eng
    await eng.dispose()


async def test_concurrent_uploads_never_exceed_the_limit(
    engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("UPLOADS_PER_DAY", "3")
    get_settings.cache_clear()
    user_id = f"user_race_{uuid4().hex[:8]}"
    async with AsyncSession(engine) as s:
        s.add(Profile(id=user_id))
        await s.commit()

    async def attempt() -> bool:
        async with AsyncSession(engine) as s:
            try:
                await take_upload_slot(s, user_id)
                await asyncio.sleep(0.05)  # hold the row lock a little, like a real request
                await s.commit()
                return True
            except UploadLimitReached:
                await s.rollback()
                return False

    try:
        results = await asyncio.gather(*(attempt() for _ in range(10)))
        assert sum(results) == 3
        async with AsyncSession(engine) as s:
            used = (
                await s.execute(select(Profile.uploads_count).where(Profile.id == user_id))
            ).scalar_one()
        assert used == 3
    finally:
        async with AsyncSession(engine) as s:
            await s.execute(delete(Profile).where(Profile.id == user_id))
            await s.commit()
        get_settings.cache_clear()
