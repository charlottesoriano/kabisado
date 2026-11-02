"""Dashboard aggregates (MDs/03-backend.md section 8).

"Today" is the calendar day in the user's ``profiles.timezone`` (05 section 2).
"""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TIMEZONE = "Asia/Manila"
MASTERED_INTERVAL_DAYS = 21


def zone(name: str | None) -> ZoneInfo:
    try:
        return ZoneInfo(name or DEFAULT_TIMEZONE)
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo(DEFAULT_TIMEZONE)


def today_bounds(tz_name: str | None, now: datetime | None = None) -> tuple[datetime, datetime]:
    """Start (inclusive) and end (exclusive) of the user's local today, in UTC."""
    tz = zone(tz_name)
    local_now = (now or datetime.now(UTC)).astimezone(tz)
    start_local = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = (start_local + timedelta(days=1)).replace(tzinfo=None).replace(tzinfo=tz)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)


def mastery_pct(mastered: int, total: int) -> int:
    """Share of cards with ``interval_days >= 21``, as a whole percent (half up)."""
    if total <= 0:
        return 0
    return int(mastered * 100 / total + 0.5)
