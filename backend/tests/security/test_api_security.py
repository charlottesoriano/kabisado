"""BE-SEC-05/07 for the 3a endpoints: no secrets in responses, no note text in logs, CORS."""

import logging

import httpx
import pytest

from tests.conftest import AZP, WEBHOOK_SECRET, auth, needs_db

pytestmark = pytest.mark.security

SECRET_MARKERS = (WEBHOOK_SECRET, "service_role", "postgresql://", "postgresql+asyncpg://")


@needs_db
async def test_no_secrets_and_no_notes_in_logs(
    api: httpx.AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    notes = "Mitochondria are the powerhouse of the cell. " * 10
    caplog.set_level(logging.INFO)
    responses = [
        await api.get("/me", headers=auth("user_S")),
        await api.post(
            "/documents/text", headers=auth("user_S"), json={"title": "T", "text": notes}
        ),
        await api.post("/documents/text", headers=auth("user_S"), json={"title": "T", "text": "x"}),
        await api.get("/documents", headers=auth("user_S")),
    ]
    for resp in responses:
        for marker in SECRET_MARKERS:
            assert marker not in resp.text
    assert "powerhouse" not in caplog.text
    assert "powerhouse" not in responses[2].text  # validation errors don't echo input


async def test_cors_only_for_the_web_app(client: httpx.AsyncClient) -> None:
    allowed = await client.options(
        "/documents",
        headers={"Origin": AZP, "Access-Control-Request-Method": "GET"},
    )
    assert allowed.headers.get("access-control-allow-origin") == AZP
    blocked = await client.options(
        "/documents",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in blocked.headers
