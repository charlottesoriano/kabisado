"""The API and Alembic always use asyncpg, whatever driver prefix DATABASE_URL carries."""

import pytest

from app.db.session import asyncpg_url


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://u:p@h:5432/d",
        "postgres://u:p@h:5432/d",
        "postgresql+psycopg://u:p@h:5432/d",
        "postgresql+asyncpg://u:p@h:5432/d",
    ],
)
def test_asyncpg_url_forces_asyncpg(url: str) -> None:
    assert asyncpg_url(url) == "postgresql+asyncpg://u:p@h:5432/d"
