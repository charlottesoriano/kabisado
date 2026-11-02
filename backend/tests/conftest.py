"""Shared fixtures. External services (JWKS, Svix, LiteLLM, Storage, Judge0) are always mocked."""

from collections.abc import AsyncIterator

import httpx
import pytest

from app.jobs.app import use_selector_loop_on_windows
from app.main import app

use_selector_loop_on_windows()


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
