"""Error envelope consistency across the real app, BE-SEC-05 (no note text in logs/errors)
and BE-SEC-07 (no service key or DB URL in responses) on the 3a routes.

Envelope: ``{"error": {"code", "message", "details"?, "request_id", "debug"?}}``; ``debug``
only when APP_ENV != production."""

import json
import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
import respx
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import jwks_cache
from app.config import get_settings
from app.db.session import dispose_engine, get_session
from app.errors import ERROR_CLASSES
from app.main import app
from app.services.storage import close_storage, get_storage
from tests import seed
from tests.api.test_me_and_webhooks import _signed, _user_event
from tests.conftest import AZP, auth, needs_db, public_jwk
from tests.fakes import FakeStorage

pytestmark = pytest.mark.security

ALLOWED_KEYS = {"code", "message", "details", "request_id", "debug"}
NOTE = "Zebrafish neurons regenerate after spinal injury"  # marker that must never leak
NOTES = (NOTE + ". ") * 8
SERVICE_KEY = "sb-service-role-SECRET-0123456789"
DB_PASSWORD = "db-pass-SECRET-9876"  # noqa: S105 (test marker)


def assert_envelope(resp: httpx.Response, *, production: bool) -> dict[str, Any]:
    assert resp.headers["content-type"].startswith("application/json"), resp.text
    body = resp.json()
    assert set(body) == {"error"}, body
    err: dict[str, Any] = body["error"]
    assert set(err) <= ALLOWED_KEYS, err
    assert {"code", "message", "request_id"} <= set(err), err
    assert isinstance(err["message"], str) and err["message"].strip()
    assert err["request_id"] == resp.headers["x-request-id"]
    cls = ERROR_CLASSES.get(err["code"])
    expected_status = 500 if err["code"] == "internal_error" else (cls and cls.status_code)
    assert resp.status_code == expected_status, (err["code"], resp.status_code)
    if production:
        assert "debug" not in err, err
    elif "debug" in err:
        assert set(err["debug"]) <= {"type", "message", "operation"}
    if "details" in err:
        for d in err["details"]:
            assert set(d) <= {"loc", "msg", "type"}, d
    return err


@pytest.fixture(params=["test", "production"])
def app_env(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    monkeypatch.setenv("APP_ENV", request.param)
    get_settings.cache_clear()
    yield request.param
    monkeypatch.setenv("APP_ENV", "test")
    get_settings.cache_clear()


class _ExplodingStorage(FakeStorage):
    async def create_signed_upload_url(self, path: str) -> Any:
        raise RuntimeError(f"unexpected bug while handling {NOTE}")


@needs_db
async def test_every_error_uses_the_envelope(
    api: httpx.AsyncClient,
    db: AsyncSession,
    storage: FakeStorage,
    mock_http: respx.MockRouter,
    monkeypatch: pytest.MonkeyPatch,
    app_env: str,
) -> None:
    production = app_env == "production"
    doc_id = (await seed.document(db, "user_A", status="ready", page_count=1)).id
    queued_id = (await seed.document(db, "user_A")).id
    calls: list[tuple[str, str, dict[str, Any]]] = [
        ("GET", "/documents", {}),  # 401
        ("GET", "/documents", {"headers": {"Authorization": "Bearer junk"}}),  # 401
        ("GET", "/nope", {}),  # 404 unknown route
        ("PUT", "/documents", {"headers": auth("user_A")}),  # 405
        ("GET", f"/documents/{doc_id}", {"headers": auth("user_B")}),  # 404
        ("GET", "/documents/not-a-uuid", {"headers": auth("user_A")}),  # 422
        ("POST", "/documents", {"headers": auth("user_A"), "json": {"title": ""}}),  # 422
        (
            "POST",
            "/documents",
            {"headers": {**auth("user_A"), "content-type": "application/json"}, "content": b"{"},
        ),  # 422 invalid JSON
        (
            "POST",
            "/documents",
            {
                "headers": auth("user_A"),
                "json": {"title": "T", "filename": "a.docx", "size_bytes": 10},
            },
        ),  # 422 invalid_file
        ("POST", f"/documents/{doc_id}/retry", {"headers": auth("user_A")}),  # 409 invalid_state
        ("POST", f"/documents/{queued_id}/process", {"headers": auth("user_A")}),  # 409 missing
        ("GET", f"/documents/{doc_id}/cards?cursor=zzz", {"headers": auth("user_A")}),  # 422
        ("POST", "/webhooks/clerk", {"content": b"{}"}),  # 400 invalid_signature
    ]
    seen_codes = set()
    for method, path, kw in calls:
        resp = await api.request(method, path, **kw)
        err = assert_envelope(resp, production=production)
        seen_codes.add(err["code"])
    assert {
        "unauthenticated",
        "not_found",
        "method_not_allowed",
        "validation_error",
        "invalid_file",
        "invalid_state",
        "upload_missing",
        "invalid_signature",
    } <= seen_codes

    # 503 auth_unavailable (Clerk JWKS down)
    jwks_cache.clear()
    mock_http.routes["jwks"].mock(return_value=httpx.Response(500))
    resp = await api.get("/documents", headers=auth("user_C"))
    assert assert_envelope(resp, production=production)["code"] == "auth_unavailable"
    mock_http.routes["jwks"].mock(return_value=httpx.Response(200, json={"keys": [public_jwk()]}))

    # 429 rate_limited, with Retry-After
    monkeypatch.setenv("RATE_LIMIT_DEFAULT_PER_MIN", "1")
    get_settings.cache_clear()
    await api.get("/documents", headers=auth("user_R"))
    limited = await api.get("/documents", headers=auth("user_R"))
    assert assert_envelope(limited, production=production)["code"] == "rate_limited"
    assert int(limited.headers["retry-after"]) >= 1
    monkeypatch.delenv("RATE_LIMIT_DEFAULT_PER_MIN")
    get_settings.cache_clear()

    # 500 internal_error from an unexpected exception: generic message, no note text
    app.dependency_overrides[get_storage] = lambda: _ExplodingStorage()
    crash = await api.post(
        "/documents",
        headers=auth("user_A"),
        json={"title": "T", "filename": "a.pdf", "size_bytes": 10},
    )
    err = assert_envelope(crash, production=production)
    assert err["code"] == "internal_error"
    assert NOTE not in err["message"]
    if production:
        assert NOTE not in crash.text


@needs_db
async def test_errors_keep_cors_headers_for_the_web_app(api: httpx.AsyncClient) -> None:
    """The web app must be able to read the envelope and request id of a failed call."""
    for headers in ({"Origin": AZP}, {"Origin": AZP, **auth("user_A")}):
        resp = await api.get("/documents/not-a-uuid", headers=headers)
        assert resp.status_code in (401, 422)
        assert resp.headers.get("access-control-allow-origin") == AZP
        assert "x-request-id" in resp.headers.get("access-control-expose-headers", "").lower()


# BE-SEC-05: note text never in responses or logs ----------------------------------------------
@needs_db
async def test_note_text_never_echoed_in_errors_or_logs(
    api: httpx.AsyncClient, db: AsyncSession, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    a = auth("user_A")
    card_doc = (await seed.document(db, "user_A")).id
    mcq_id = (await seed.card(db, card_doc, type="mcq")).id
    flash_id = (await seed.card(db, card_doc)).id
    responses = [
        # too short / too long / bad title / extra field / wrong type
        await api.post("/documents/text", headers=a, json={"title": "T", "text": NOTE}),
        await api.post("/documents/text", headers=a, json={"title": "T", "text": NOTES * 300}),
        await api.post("/documents/text", headers=a, json={"title": "", "text": NOTES}),
        await api.post(
            "/documents/text", headers=a, json={"title": "T", "text": NOTES, "extra": NOTES}
        ),
        await api.post("/documents/text", headers=a, json={"title": NOTES, "text": NOTES}),
        await api.post("/documents/text", headers=a, json={"title": "T", "text": [NOTES]}),
        # malformed JSON containing notes
        await api.post(
            "/documents/text",
            headers={**a, "content-type": "application/json"},
            content=('{"title": "T", "text": "' + NOTES + '"').encode(),
        ),
        # invalid card edits containing note text / answers
        await api.patch(
            f"/cards/{mcq_id}",
            headers=a,
            json={
                "payload": {
                    "question": NOTE,
                    "options": [NOTE] * 4,
                    "answer_index": 0,
                    "explanation": NOTES,
                }
            },
        ),
        await api.patch(
            f"/cards/{flash_id}", headers=a, json={"payload": {"front": NOTE, "back": ""}}
        ),
        await api.patch(f"/cards/{flash_id}", headers=a, json={"payload": {"front": NOTE}}),
        await api.post(f"/cards/{flash_id}/flag", headers=a, json={"reason": NOTE}),
        await api.patch(f"/documents/{card_doc}", headers=a, json={"title": NOTES * 10}),
        await api.get(f"/documents/{card_doc}/cards?type={NOTE}", headers=a),
    ]
    for resp in responses:
        assert resp.status_code == 422, resp.text[:300]
        assert NOTE not in resp.text, resp.text[:500]

    # Successful writes don't log content either.
    ok = [
        await api.post("/documents/text", headers=a, json={"title": "T", "text": NOTES}),
        await api.patch(
            f"/cards/{flash_id}",
            headers=a,
            json={"payload": {"front": "What regenerates?", "back": NOTE}},
        ),
    ]
    assert [r.status_code for r in ok] == [201, 200]
    assert NOTE not in caplog.text


# BE-SEC-07: secrets never in responses or logs ------------------------------------------------
@pytest.fixture
async def real_storage(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[None]:
    monkeypatch.setenv("SUPABASE_URL", "https://supabase.test")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", SERVICE_KEY)
    get_settings.cache_clear()
    await close_storage()
    yield
    await close_storage()
    get_settings.cache_clear()


@needs_db
@pytest.mark.parametrize(
    "storage_reply",
    [
        pytest.param(
            httpx.Response(
                500, json={"statusCode": "500", "error": "InternalError", "message": "boom"}
            ),
            id="storage 500",
        ),
        pytest.param(httpx.ReadTimeout("timed out"), id="storage timeout"),
        pytest.param(httpx.ConnectError("refused"), id="storage down"),
    ],
)
async def test_service_key_never_leaks(
    api: httpx.AsyncClient,
    real_storage: None,
    mock_http: respx.MockRouter,
    caplog: pytest.LogCaptureFixture,
    storage_reply: Any,
) -> None:
    """Real SupabaseStorage client against a mocked Storage API that fails."""
    caplog.set_level(logging.DEBUG)
    app.dependency_overrides.pop(get_storage)
    route = mock_http.route(host="supabase.test")
    if isinstance(storage_reply, Exception):
        route.mock(side_effect=storage_reply)
    else:
        route.mock(return_value=storage_reply)
    resp = await api.post(
        "/documents",
        headers=auth("user_A"),
        json={"title": "T", "filename": "a.pdf", "size_bytes": 10},
    )
    assert resp.status_code in (502, 503), resp.text
    assert_envelope(resp, production=False)
    assert route.called
    assert route.calls[0].request.headers["apikey"] == SERVICE_KEY  # the key really was in play
    assert SERVICE_KEY not in resp.text
    assert SERVICE_KEY not in caplog.text


async def test_database_url_never_leaks(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Real session dependency with an unreachable database whose URL carries a password."""
    caplog.set_level(logging.DEBUG)
    monkeypatch.setenv("DATABASE_URL", f"postgresql://kab_app:{DB_PASSWORD}@127.0.0.1:9/postgres")
    get_settings.cache_clear()
    await dispose_engine()
    try:
        resp = await client.get("/documents", headers=auth("user_A"))
        assert resp.status_code == 503, resp.text
        err = assert_envelope(resp, production=False)
        assert err["code"] == "service_unavailable"
        for secret in (DB_PASSWORD, "kab_app", "postgresql://"):
            assert secret not in resp.text
            assert secret not in caplog.text
    finally:
        await dispose_engine()
        get_settings.cache_clear()


@needs_db
async def test_webhook_errors_do_not_echo_payload(
    api: httpx.AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    body, headers = _signed(_user_event("user.created", "user_Q", email="secret.person@x.test"))
    resp = await api.post("/webhooks/clerk", content=body + b" ", headers=headers)
    assert resp.status_code == 400
    assert "secret.person" not in resp.text
    assert "secret.person" not in caplog.text
    assert json.loads(resp.text)["error"]["code"] == "invalid_signature"


def test_session_dependency_is_real_in_sweep() -> None:
    """Guard for the test above: nothing overrides the session globally."""
    assert get_session not in app.dependency_overrides
