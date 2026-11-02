"""BE-AUTH-01..08: Clerk session token verification (JWKS mocked with respx)."""

import time

import httpx
import pytest
import respx

from app.config import get_settings
from tests.conftest import AZP, OTHER_KEY, auth, needs_db, token_for

pytestmark = pytest.mark.api


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_no_token_is_401(client: httpx.AsyncClient) -> None:
    """BE-AUTH-01"""
    resp = await client.get("/documents")
    assert resp.status_code == 401
    body = resp.json()["error"]
    assert body["code"] == "unauthenticated"
    assert body["request_id"] == resp.headers["x-request-id"]
    assert resp.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "token",
    [
        pytest.param(token_for("user_A", exp=int(time.time()) - 300), id="BE-AUTH-03 expired"),
        pytest.param(token_for("user_A", iss="https://other.clerk.test"), id="BE-AUTH-05 issuer"),
        pytest.param(token_for("user_A", azp="https://evil.example"), id="BE-AUTH-06 azp"),
        pytest.param(token_for("user_A", azp=None), id="missing azp"),
        pytest.param(token_for("user_A", key=OTHER_KEY), id="BE-AUTH-07 signature"),
        pytest.param(token_for("user_A", exp=None), id="missing exp"),
        pytest.param("not-a-jwt", id="garbage"),
    ],
)
async def test_bad_tokens_are_401(client: httpx.AsyncClient, token: str) -> None:
    resp = await client.get("/documents", headers=_bearer(token))
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthenticated"


async def test_unknown_kid_refetches_jwks_once(
    client: httpx.AsyncClient, mock_http: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
) -> None:
    """BE-AUTH-08: cache warm, token with an unknown kid -> one refetch, still 401."""
    monkeypatch.setenv("CLERK_JWKS_MIN_REFETCH_SECONDS", "0")
    get_settings.cache_clear()
    await client.get("/documents", headers=_bearer(token_for("user_A", key=OTHER_KEY)))
    calls_before = mock_http.routes["jwks"].call_count
    resp = await client.get(
        "/documents", headers=_bearer(token_for("user_A", key=OTHER_KEY, kid="rotated"))
    )
    assert resp.status_code == 401
    assert mock_http.routes["jwks"].call_count == calls_before + 1
    get_settings.cache_clear()


async def test_jwks_outage_is_503_not_401(
    client: httpx.AsyncClient, mock_http: respx.MockRouter
) -> None:
    mock_http.routes["jwks"].mock(return_value=httpx.Response(500))
    resp = await client.get("/documents", headers=auth("user_A"))
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "auth_unavailable"


async def test_auth_not_configured_fails_closed(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CLERK_AUTHORIZED_PARTIES", "")
    get_settings.cache_clear()
    try:
        resp = await client.get("/documents", headers=auth("user_A"))
        assert resp.status_code == 401
    finally:
        monkeypatch.setenv("CLERK_AUTHORIZED_PARTIES", AZP)
        get_settings.cache_clear()


@needs_db
async def test_valid_token_and_small_clock_skew(api: httpx.AsyncClient) -> None:
    """BE-AUTH-02, BE-AUTH-04"""
    assert (await api.get("/documents", headers=auth("user_A"))).status_code == 200
    skewed = token_for("user_A", nbf=int(time.time()) + 5)
    assert (await api.get("/documents", headers=_bearer(skewed))).status_code == 200


@needs_db
async def test_rate_limit_per_user(api: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_DEFAULT_PER_MIN", "2")
    get_settings.cache_clear()
    try:
        for _ in range(2):
            assert (await api.get("/documents", headers=auth("user_A"))).status_code == 200
        limited = await api.get("/documents", headers=auth("user_A"))
        assert limited.status_code == 429
        assert limited.json()["error"]["code"] == "rate_limited"
        assert int(limited.headers["retry-after"]) >= 1
        assert (await api.get("/documents", headers=auth("user_B"))).status_code == 200
    finally:
        get_settings.cache_clear()
