"""Per-user rate limits (MDs/03-backend.md section 3): in-memory fixed windows.

The MVP runs the API as one process (01-stack section 7), so counters live in memory and reset
on restart. Limits come from config. Keys are the verified Clerk user id, so the dependencies
run after authentication.

- ``default_rate_limit``: everything authenticated, ``RATE_LIMIT_DEFAULT_PER_MIN``.
- ``ai_rate_limit``: AI endpoints (explain, generate-topic; 3f), per minute and per day.

The daily upload limit (``take_upload_slot``) is different: it lives in the database
(``profiles.uploads_day`` / ``uploads_count``, migration 0003) so it survives restarts and deck
deletions, and it is taken in the same transaction as the document insert.
"""

import math
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from sqlalchemy import Date, case, cast, func, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUserId
from app.config import get_settings
from app.db.models import Profile
from app.errors import RateLimited, UploadLimitReached, guard


@dataclass
class FixedWindowLimiter:
    clock: Callable[[], float] = time.time
    _counts: dict[tuple[str, str, int, int], int] = field(default_factory=dict)
    _hits: int = 0

    def hit(self, key: str, bucket: str, limit: int, window_seconds: int) -> float | None:
        """Count one request. Returns ``None`` if allowed, else seconds until the window
        resets."""
        now = self.clock()
        window = int(now // window_seconds)
        k = (key, bucket, window_seconds, window)
        count = self._counts.get(k, 0) + 1
        self._counts[k] = count
        self._hits += 1
        if self._hits % 1000 == 0:
            self._prune(now)
        if count > limit:
            return (window + 1) * window_seconds - now
        return None

    def _prune(self, now: float) -> None:
        self._counts = {k: v for k, v in self._counts.items() if (k[3] + 1) * k[2] > now}

    def reset(self) -> None:
        self._counts.clear()
        self._hits = 0


limiter = FixedWindowLimiter()


def _check(user_id: str, bucket: str, limit: int, window_seconds: int) -> None:
    retry_after = limiter.hit(user_id, bucket, limit, window_seconds)
    if retry_after is not None:
        raise RateLimited(
            headers={"Retry-After": str(max(1, math.ceil(retry_after)))},
            context={"bucket": bucket, "limit": limit, "window_seconds": window_seconds},
        )


async def default_rate_limit(user_id: CurrentUserId) -> None:
    _check(user_id, "default", get_settings().rate_limit_default_per_min, 60)


async def ai_rate_limit(user_id: CurrentUserId) -> None:
    settings = get_settings()
    _check(user_id, "ai_minute", settings.rate_limit_ai_per_min, 60)
    _check(user_id, "ai_day", settings.rate_limit_ai_per_day, 86_400)


async def take_upload_slot(session: AsyncSession, user_id: str) -> int:
    """Use one of today's uploads (PDF or pasted notes) or raise ``upload_limit_reached``.

    One atomic ``UPDATE ... RETURNING`` on the user's profile row: it resets the counter when
    the user's local day (``profiles.timezone``) has changed, and only increments while under
    ``UPLOADS_PER_DAY``. The row lock serializes concurrent uploads, and the change commits or
    rolls back with the document insert. Deleting a deck never gives a slot back.
    Returns the number of uploads used today, including this one.
    """
    limit = get_settings().uploads_per_day
    local_today = cast(func.timezone(Profile.timezone, func.now()), Date)
    stmt = (
        update(Profile)
        .where(
            Profile.id == user_id,
            or_(Profile.uploads_day.is_distinct_from(local_today), Profile.uploads_count < limit),
        )
        .values(
            uploads_count=case(
                (Profile.uploads_day == local_today, Profile.uploads_count + 1), else_=1
            ),
            uploads_day=local_today,
            updated_at=Profile.updated_at,  # bookkeeping, not a profile edit
        )
        .returning(Profile.uploads_count)
        .execution_options(synchronize_session=False)
    )
    with guard("db.take_upload_slot", user_id=user_id):
        used = (await session.execute(stmt)).scalar_one_or_none()
    if used is None:
        raise UploadLimitReached(context={"user_id": user_id, "limit": limit})
    return int(used)
