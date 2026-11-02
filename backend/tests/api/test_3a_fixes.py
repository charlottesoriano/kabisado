"""Approved 3a review fixes: upload counter, retry rules, enqueue after commit, trimmed notes,
auth before validation, safe validation locations, webhook ordering."""

import logging
from datetime import timedelta
from typing import Any
from uuid import UUID

import httpx
import pytest
from sqlalchemy import Date, cast, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models
from tests import seed
from tests.api.test_me_and_webhooks import _signed, _user_event
from tests.conftest import auth, needs_db
from tests.fakes import FakeQueue, FakeStorage
from tests.unit.test_services_3a import make_pdf

pytestmark = [pytest.mark.api, needs_db]

A = "user_A"
NOTES = "Cells are the basic unit of life. " * 10


def _create(**overrides: Any) -> dict[str, Any]:
    return {"title": "Biology", "filename": "notes.pdf", "size_bytes": 1000} | overrides


# 1. Daily upload counter ------------------------------------------------------------------------
async def test_counter_resets_on_a_new_local_day(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """20 uploads yesterday (user's time zone) don't block today; the count starts over."""
    await seed.profile(db, A)
    yesterday = cast(func.timezone("Asia/Manila", func.now()), Date) - timedelta(days=1)
    await db.execute(
        update(models.Profile)
        .where(models.Profile.id == A)
        .values(uploads_count=20, uploads_day=yesterday)
    )
    await db.commit()
    resp = await api.post("/documents", headers=auth(A), json=_create())
    assert resp.status_code == 201
    count = select(models.Profile.uploads_count).where(models.Profile.id == A)
    assert (await db.execute(count)).scalar_one() == 1


async def test_failed_create_does_not_use_a_slot(
    api: httpx.AsyncClient, db: AsyncSession, storage: FakeStorage
) -> None:
    await seed.profile(db, A)
    storage.fail_with = httpx.ReadTimeout("slow")
    assert (await api.post("/documents", headers=auth(A), json=_create())).status_code == 503
    count = select(models.Profile.uploads_count).where(models.Profile.id == A)
    assert (await db.execute(count)).scalar_one() == 0


# 2. Retry refuses failures caused by the file ----------------------------------------------
@pytest.mark.parametrize("error_code", ["page_limit_exceeded", "invalid_file"])
async def test_retry_refuses_file_failures(
    api: httpx.AsyncClient, db: AsyncSession, queue: FakeQueue, error_code: str
) -> None:
    doc_id = (await seed.document(db, A, status="failed", error_code=error_code)).id
    resp = await api.post(f"/documents/{doc_id}/retry", headers=auth(A))
    assert resp.status_code == 409
    err = resp.json()["error"]
    assert err["code"] == "invalid_state"
    assert "new" in err["message"] and "upload" in err["message"].lower()
    assert queue.jobs == []


# 3. Enqueue after commit --------------------------------------------------------------------------
async def _doc_state(db: AsyncSession, doc_id: UUID) -> tuple[str, str | None]:
    stmt = select(models.Document.status, models.Document.error_code).where(
        models.Document.id == doc_id
    )
    row = (await db.execute(stmt)).one()
    return row[0], row[1]


async def test_text_enqueue_failure_marks_failed_and_retry_recovers(
    api: httpx.AsyncClient, db: AsyncSession, queue: FakeQueue
) -> None:
    queue.fail_with = httpx.ConnectError("queue down")
    resp = await api.post("/documents/text", headers=auth(A), json={"title": "N", "text": NOTES})
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "enqueue_failed"
    doc = (await api.get("/documents", headers=auth(A))).json()["items"][0]
    doc_id = UUID(doc["id"])
    assert await _doc_state(db, doc_id) == ("failed", "enqueue_failed")
    assert queue.discarded == [doc_id]  # no stale queueing lock left behind

    queue.fail_with = None
    retry = await api.post(f"/documents/{doc_id}/retry", headers=auth(A))
    assert retry.status_code == 202
    assert queue.jobs == [doc_id]


async def test_process_enqueue_failure_marks_failed(
    api: httpx.AsyncClient, db: AsyncSession, storage: FakeStorage, queue: FakeQueue
) -> None:
    created = (await api.post("/documents", headers=auth(A), json=_create())).json()
    doc_id = UUID(created["document"]["id"])
    storage.put(created["upload"]["path"], make_pdf(2))
    queue.fail_with = RuntimeError("boom")
    resp = await api.post(f"/documents/{doc_id}/process", headers=auth(A))
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "enqueue_failed"
    assert await _doc_state(db, doc_id) == ("failed", "enqueue_failed")
    assert queue.discarded == [doc_id]


async def test_retry_enqueue_failure_marks_failed_again(
    api: httpx.AsyncClient, db: AsyncSession, queue: FakeQueue
) -> None:
    doc_id = (
        await seed.document(db, A, status="failed", error_code="ai_unavailable", page_count=2)
    ).id
    queue.fail_with = httpx.ReadTimeout("slow")
    resp = await api.post(f"/documents/{doc_id}/retry", headers=auth(A))
    assert resp.json()["error"]["code"] == "enqueue_failed"
    assert await _doc_state(db, doc_id) == ("failed", "enqueue_failed")


# 4. Pasted notes are trimmed before the length check ---------------------------------------------
@pytest.mark.parametrize(
    "text",
    [" " * 300, "\n\t " * 150, "  " + "a" * 199 + "   \n"],
    ids=["spaces", "mixed whitespace", "padded 199"],
)
async def test_whitespace_does_not_count(api: httpx.AsyncClient, text: str) -> None:
    resp = await api.post("/documents/text", headers=auth(A), json={"title": "N", "text": text})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


async def test_notes_are_stored_trimmed(api: httpx.AsyncClient, db: AsyncSession) -> None:
    text = "\n  " + "a" * 200 + "  \n"
    resp = await api.post("/documents/text", headers=auth(A), json={"title": "N", "text": text})
    assert resp.status_code == 201
    stmt = select(models.Document.raw_text).where(models.Document.id == UUID(resp.json()["id"]))
    assert (await db.execute(stmt)).scalar_one() == "a" * 200


# 5. Authentication is checked before validation ---------------------------------------------------
BAD_REQUESTS: list[tuple[str, str, dict[str, Any]]] = [
    ("POST", "/documents", {"json": {"title": ""}}),
    ("POST", "/documents", {"content": b"{", "headers": {"content-type": "application/json"}}),
    ("POST", "/documents/text", {"json": {"title": "T", "text": "x", "extra": 1}}),
    ("GET", "/documents/not-a-uuid", {}),
    ("GET", "/documents/00000000-0000-0000-0000-000000000000/cards?cursor=zz&limit=0", {}),
    ("PATCH", "/cards/not-a-uuid", {"json": {"payload": {}}}),
    ("POST", "/cards/00000000-0000-0000-0000-000000000000/flag", {"json": {"reason": "x"}}),
    ("PATCH", "/me", {"json": {"timezone": "Mars/Base"}}),
]


@pytest.mark.parametrize(("method", "path", "kw"), BAD_REQUESTS)
@pytest.mark.parametrize("token", [None, "junk"], ids=["no token", "bad token"])
async def test_auth_errors_win_over_validation_errors(
    api: httpx.AsyncClient, method: str, path: str, kw: dict[str, Any], token: str | None
) -> None:
    headers = dict(kw.pop("headers", {}))
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = await api.request(method, path, headers=headers, **kw)
    assert resp.status_code == 401, resp.text
    err = resp.json()["error"]
    assert err["code"] == "unauthenticated"
    assert err["request_id"] == resp.headers["x-request-id"]
    assert "details" not in err


@pytest.mark.parametrize(("method", "path", "kw"), BAD_REQUESTS)
async def test_validation_errors_still_reported_with_a_valid_token(
    api: httpx.AsyncClient, method: str, path: str, kw: dict[str, Any]
) -> None:
    headers = {**dict(kw.pop("headers", {})), **auth(A)}
    resp = await api.request(method, path, headers=headers, **kw)
    assert resp.status_code == 422, resp.text
    assert resp.json()["error"]["code"] == "validation_error"


async def test_auth_outage_wins_over_validation(api: httpx.AsyncClient, mock_http: Any) -> None:
    mock_http.routes["jwks"].mock(return_value=httpx.Response(500))
    resp = await api.post("/documents", headers=auth(A), json={"title": ""})
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "auth_unavailable"


async def test_unauthenticated_routes_still_validate(api: httpx.AsyncClient) -> None:
    resp = await api.post("/webhooks/clerk", content=b"{")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "invalid_signature"


# 6. Client-supplied key names in validation details -----------------------------------------------
@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("colour", "colour"),
        ("_private_1", "_private_1"),
        ("<script>alert(1)</script>", "<unknown field>"),
        ("has space", "<unknown field>"),
        ("x" * 65, "<unknown field>"),
        ("1starts_with_digit", "<unknown field>"),
        ("Zebrafish neurons regenerate", "<unknown field>"),
    ],
)
async def test_unknown_field_names_are_sanitized(
    api: httpx.AsyncClient, caplog: pytest.LogCaptureFixture, key: str, expected: str
) -> None:
    caplog.set_level(logging.DEBUG)
    body = {**_create(), key: "secret value 12345"}
    resp = await api.post("/documents", headers=auth(A), json=body)
    assert resp.status_code == 422
    details = resp.json()["error"]["details"]
    extra = [d for d in details if d.get("type") == "extra_forbidden"]
    assert extra and extra[0]["loc"] == ["body", expected]
    assert extra[0]["msg"] == "Unknown field. Remove it and try again."
    assert "secret value 12345" not in resp.text
    assert "secret value 12345" not in caplog.text
    if expected != key:
        assert key not in resp.text
        assert key not in caplog.text


# 7. Webhook ordering ------------------------------------------------------------------------------
async def test_created_after_deleted_is_ignored(api: httpx.AsyncClient, db: AsyncSession) -> None:
    await seed.profile(db, "user_gone")
    body, headers = _signed(_user_event("user.deleted", "user_gone"))
    assert (await api.post("/webhooks/clerk", content=body, headers=headers)).status_code == 200

    for kind in ("user.created", "user.updated"):
        body, headers = _signed(_user_event(kind, "user_gone"))
        resp = await api.post("/webhooks/clerk", content=body, headers=headers)
        assert resp.status_code == 200
        assert resp.json() == {"status": "ignored"}
    assert await db.get(models.Profile, "user_gone", populate_existing=True) is None
    recorded = select(models.WebhookEvent.user_id).where(models.WebhookEvent.user_id == "user_gone")
    assert len((await db.execute(recorded)).all()) == 3


async def test_other_users_unaffected_by_a_deletion(
    api: httpx.AsyncClient, db: AsyncSession
) -> None:
    body, headers = _signed(_user_event("user.deleted", "user_gone2"))
    await api.post("/webhooks/clerk", content=body, headers=headers)
    body, headers = _signed(_user_event("user.created", "user_fresh"))
    resp = await api.post("/webhooks/clerk", content=body, headers=headers)
    assert resp.json() == {"status": "processed"}
