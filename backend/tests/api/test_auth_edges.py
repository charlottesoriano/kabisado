"""QA edge cases around BE-AUTH-01..08 (Clerk token verification) and the auth sweep.

Tokens are signed with the test RSA key; Clerk's JWKS is mocked (``mock_http``)."""

import base64
import hashlib
import hmac
import json
import re
import time
from typing import Any
from uuid import uuid4

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.main import app
from tests import seed
from tests.conftest import AZP, ISSUER, KID, PRIVATE_KEY, auth, needs_db, token_for

pytestmark = pytest.mark.api

PUBLIC_ROUTES = {("GET", "/health"), ("POST", "/webhooks/clerk")}


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _claims(**overrides: Any) -> dict[str, Any]:
    now = int(time.time())
    return {
        "sub": "user_A",
        "iss": ISSUER,
        "azp": AZP,
        "iat": now - 1,
        "exp": now + 300,
    } | overrides


def _hs256_with_public_key() -> str:
    """Algorithm-confusion attack: HS256 'signed' with the RSA public key as the secret."""
    pem = PRIVATE_KEY.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT", "kid": KID}).encode())
    payload = _b64(json.dumps(_claims()).encode())
    sig = hmac.new(pem, f"{header}.{payload}".encode(), hashlib.sha256).digest()
    return f"{header}.{payload}.{_b64(sig)}"


def _unsigned() -> str:
    header = _b64(json.dumps({"alg": "none", "typ": "JWT", "kid": KID}).encode())
    return f"{header}.{_b64(json.dumps(_claims()).encode())}."


def _rs256(claims: dict[str, Any], headers: dict[str, Any] | None = None) -> str:
    return jwt.encode(
        claims, PRIVATE_KEY, algorithm="RS256", headers={"kid": KID} if headers is None else headers
    )


@pytest.mark.security
@pytest.mark.parametrize(
    "headers",
    [
        pytest.param({"Authorization": _unsigned()}, id="no scheme"),
        pytest.param(_bearer(_unsigned()), id="alg none"),
        pytest.param(_bearer(_hs256_with_public_key()), id="HS256 with public key"),
        pytest.param(_bearer(_rs256(_claims(), headers={"typ": "JWT"})), id="no kid"),
        pytest.param(
            _bearer(_rs256({k: v for k, v in _claims().items() if k != "sub"})), id="no sub"
        ),
        pytest.param(_bearer(_rs256(_claims(sub=""))), id="empty sub"),
        pytest.param(
            _bearer(_rs256({k: v for k, v in _claims().items() if k != "iss"})), id="no iss"
        ),
        pytest.param(
            _bearer(token_for("user_A", nbf=int(time.time()) + 120)), id="nbf beyond skew"
        ),
        pytest.param({"Authorization": f"Basic {token_for('user_A')}"}, id="basic scheme"),
        pytest.param({"Authorization": "Bearer "}, id="empty bearer"),
        pytest.param({"Authorization": "Bearer a.b.c"}, id="three garbage segments"),
    ],
)
async def test_more_bad_tokens_are_401(client: httpx.AsyncClient, headers: dict[str, str]) -> None:
    """BE-AUTH-05/07 variants: forged, unsigned and malformed tokens."""
    resp = await client.get("/documents", headers=headers)
    assert resp.status_code == 401, resp.text
    assert resp.json()["error"]["code"] == "unauthenticated"
    assert resp.headers["www-authenticate"] == "Bearer"


@needs_db
async def test_small_exp_skew_and_lowercase_scheme_are_accepted(api: httpx.AsyncClient) -> None:
    """BE-AUTH-04 (exp side of the skew allowance in 03 section 9)."""
    just_expired = token_for("user_A", exp=int(time.time()) - 3)
    assert (await api.get("/documents", headers=_bearer(just_expired))).status_code == 200
    lower = {"Authorization": f"bearer {token_for('user_A')}"}
    assert (await api.get("/documents", headers=lower)).status_code == 200


@needs_db
async def test_valid_token_sees_only_own_documents(
    api: httpx.AsyncClient, db: AsyncSession
) -> None:
    """BE-AUTH-02: 200 and only user A's documents."""
    mine = await seed.document(db, "user_A", title="Mine")
    await seed.document(db, "user_B", title="Theirs")
    resp = await api.get("/documents", headers=auth("user_A"))
    assert resp.status_code == 200
    assert [d["id"] for d in resp.json()["items"]] == [str(mine.id)]
    assert "Theirs" not in resp.text


@pytest.mark.security
async def test_every_private_route_requires_a_token(client: httpx.AsyncClient) -> None:
    """BE-AUTH-01 sweep: every route except /health and the webhook is 401 without a token.
    Runs without a database, so a route touching the DB before auth would fail here too."""
    checked = 0
    for template, ops in app.openapi()["paths"].items():
        for method in (m.upper() for m in ops):
            if (method, template) in PUBLIC_ROUTES:
                continue
            path = re.sub(r"\{[^}]+\}", lambda _: str(uuid4()), template)
            body: dict[str, Any] | None = {} if method in ("POST", "PATCH") else None
            resp = await client.request(method, path, json=body)
            assert resp.status_code == 401, (method, template, resp.text)
            assert resp.json()["error"]["code"] == "unauthenticated"
            checked += 1
    assert checked >= 14


@needs_db
async def test_rate_limit_is_shared_across_routers(
    api: httpx.AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """120/min is per user across all endpoints, not per router."""
    doc = await seed.document(db, "user_A")
    monkeypatch.setenv("RATE_LIMIT_DEFAULT_PER_MIN", "3")
    get_settings.cache_clear()
    try:
        assert (await api.get("/me", headers=auth("user_A"))).status_code == 200
        assert (await api.get("/documents", headers=auth("user_A"))).status_code == 200
        cards = await api.get(f"/documents/{doc.id}/cards", headers=auth("user_A"))
        assert cards.status_code == 200
        limited = await api.patch("/me", headers=auth("user_A"), json={"display_name": "X"})
        assert limited.status_code == 429
        assert limited.json()["error"]["code"] == "rate_limited"
    finally:
        get_settings.cache_clear()
