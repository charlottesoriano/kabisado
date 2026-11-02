"""Shared fixtures. External services (JWKS, Svix, LiteLLM, Storage, Judge0) are always mocked."""

from collections.abc import AsyncIterator, Callable, Iterator

import httpx
import pytest
from alembic.config import Config

from app.config import BACKEND_DIR, get_settings
from app.jobs.app import use_selector_loop_on_windows
from app.main import app

use_selector_loop_on_windows()


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def alembic_config(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[[str], Config]]:
    """Build an Alembic config whose env.py sees ``url`` as DATABASE_URL.

    No ini file is passed, so env.py skips ``fileConfig`` and leaves pytest's logging alone.
    """

    def make(url: str) -> Config:
        monkeypatch.setenv("DATABASE_URL", url)
        get_settings.cache_clear()
        cfg = Config()
        cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
        return cfg

    yield make
    get_settings.cache_clear()
