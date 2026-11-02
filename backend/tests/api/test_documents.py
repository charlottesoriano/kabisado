"""BE-DOC-01..19, BE-AUTH-16, BE-SEC-02: documents, upload, processing, list, delete."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import models
from tests import seed
from tests.conftest import auth, needs_db
from tests.fakes import FakeQueue, FakeStorage
from tests.unit.test_services_3a import make_pdf

pytestmark = [pytest.mark.api, needs_db]

A = "user_A"
B = "user_B"


def _create(**overrides: Any) -> dict[str, Any]:
    return {"title": "Biology", "filename": "notes.pdf", "size_bytes": 2_000_000} | overrides


async def _uploaded(api: httpx.AsyncClient, storage: FakeStorage, data: bytes) -> str:
    resp = await api.post("/documents", headers=auth(A), json=_create())
    assert resp.status_code == 201, resp.text
    upload = resp.json()["upload"]
    storage.put(upload["path"], data)
    return str(resp.json()["document"]["id"])


async def test_create_pdf_document(api: httpx.AsyncClient, storage: FakeStorage) -> None:
    """BE-DOC-01"""
    resp = await api.post("/documents", headers=auth(A), json=_create())
    assert resp.status_code == 201
    body = resp.json()
    doc = body["document"]
    assert doc["status"] == "queued"
    assert doc["source_type"] == "pdf"
    assert doc["generate_kinds"] == ["flashcard", "mcq", "problem"]
    assert body["upload"]["path"] == f"{A}/{doc['id']}.pdf"
    expires = datetime.fromisoformat(body["upload"]["expires_at"])
    assert expires > datetime.now(UTC)
    assert ("create_signed_upload_url", f"{A}/{doc['id']}.pdf") in storage.calls


@pytest.mark.parametrize(
    ("body", "code"),
    [
        pytest.param(_create(size_bytes=21 * 1024 * 1024), "file_too_large", id="BE-DOC-02"),
        pytest.param(_create(filename="notes.docx"), "invalid_file", id="BE-DOC-03"),
        pytest.param(_create(title=""), "validation_error", id="BE-DOC-04 empty"),
        pytest.param(_create(title="x" * 121), "validation_error", id="BE-DOC-04 long"),
        pytest.param(_create(generate_kinds=[]), "validation_error", id="no kinds"),
        pytest.param(_create(generate_kinds=["mcq", "mcq"]), "validation_error", id="dup kinds"),
    ],
)
async def test_create_validation(api: httpx.AsyncClient, body: dict[str, Any], code: str) -> None:
    resp = await api.post("/documents", headers=auth(A), json=body)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == code


async def test_storage_failure_rolls_back_create(
    api: httpx.AsyncClient, db: AsyncSession, storage: FakeStorage
) -> None:
    storage.fail_with = httpx.ReadTimeout("slow")
    resp = await api.post("/documents", headers=auth(A), json=_create())
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "upstream_timeout"
    count = select(func.count()).select_from(models.Document).where(models.Document.user_id == A)
    assert (await db.execute(count)).scalar_one() == 0


async def test_process_without_upload(api: httpx.AsyncClient) -> None:
    """BE-DOC-05"""
    created = await api.post("/documents", headers=auth(A), json=_create())
    doc_id = created.json()["document"]["id"]
    resp = await api.post(f"/documents/{doc_id}/process", headers=auth(A))
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "upload_missing"


async def test_process_fake_pdf(api: httpx.AsyncClient, storage: FakeStorage) -> None:
    """BE-DOC-06"""
    doc_id = await _uploaded(api, storage, b"\x89PNG\r\n\x1a\n" + b"0" * 200)
    resp = await api.post(f"/documents/{doc_id}/process", headers=auth(A))
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_file"


async def test_page_limit_fails_document(
    api: httpx.AsyncClient, storage: FakeStorage, queue: FakeQueue
) -> None:
    """BE-DOC-07"""
    doc_id = await _uploaded(api, storage, make_pdf(51))
    resp = await api.post(f"/documents/{doc_id}/process", headers=auth(A))
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "page_limit_exceeded"
    detail = (await api.get(f"/documents/{doc_id}", headers=auth(A))).json()
    assert detail["status"] == "failed"
    assert detail["error_code"] == "page_limit_exceeded"
    assert queue.jobs == []


async def test_process_queues_once(
    api: httpx.AsyncClient, storage: FakeStorage, queue: FakeQueue
) -> None:
    """BE-DOC-08, BE-DOC-09"""
    doc_id = await _uploaded(api, storage, make_pdf(3))
    resp = await api.post(f"/documents/{doc_id}/process", headers=auth(A))
    assert resp.status_code == 202
    assert resp.json()["page_count"] == 3
    assert queue.jobs == [UUID(doc_id)]
    again = await api.post(f"/documents/{doc_id}/process", headers=auth(A))
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "already_processing"
    assert queue.jobs == [UUID(doc_id)]


async def test_paste_notes(api: httpx.AsyncClient, queue: FakeQueue) -> None:
    """BE-DOC-10, BE-DOC-11"""
    ok = await api.post(
        "/documents/text", headers=auth(A), json={"title": "Notes", "text": "a" * 1500}
    )
    assert ok.status_code == 201
    assert ok.json()["source_type"] == "text"
    assert queue.jobs == [UUID(ok.json()["id"])]
    for text in ("a" * 199, "a" * 100_001):
        bad = await api.post("/documents/text", headers=auth(A), json={"title": "N", "text": text})
        assert bad.status_code == 422
        assert bad.json()["error"]["code"] == "validation_error"
    process_text = await api.post(f"/documents/{ok.json()['id']}/process", headers=auth(A))
    assert process_text.json()["error"]["code"] == "already_processing"


async def test_daily_upload_limit(api: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """BE-DOC-12 (limit lowered to 3 to keep the test fast)"""
    monkeypatch.setenv("UPLOADS_PER_DAY", "3")
    get_settings.cache_clear()
    try:
        for _ in range(3):
            assert (
                await api.post("/documents", headers=auth(A), json=_create())
            ).status_code == 201
        resp = await api.post("/documents", headers=auth(A), json=_create())
        assert resp.status_code == 429
        assert resp.json()["error"]["code"] == "upload_limit_reached"
        text = await api.post(
            "/documents/text", headers=auth(A), json={"title": "N", "text": "a" * 300}
        )
        assert text.status_code == 429
    finally:
        get_settings.cache_clear()


async def test_list_own_documents_newest_first(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """BE-DOC-13"""
    now = datetime.now(UTC)
    old = await seed.document(db, A, title="Old", created_at=now - timedelta(days=2))
    new = await seed.document(db, A, title="New", created_at=now - timedelta(days=1))
    await seed.document(db, B, title="Theirs")
    due = await seed.card(db, new.id)
    await seed.state(db, A, due.id, due_in=timedelta(hours=-1))
    later = await seed.card(db, new.id)
    await seed.state(db, A, later.id, due_in=timedelta(days=3), interval_days=30)
    mcq = await seed.card(db, new.id, type="mcq")
    await seed.state(db, A, mcq.id)  # due, but MCQs aren't in the review due list
    await seed.card(db, new.id, flagged=True)

    resp = await api.get("/documents", headers=auth(A))
    items = resp.json()["items"]
    assert [d["title"] for d in items] == ["New", "Old"]
    first = items[0]
    assert first["card_counts"] == {"flashcard": 2, "mcq": 1, "problem": 0}
    assert first["due_count"] == 1
    assert first["mastery_pct"] == 33  # 1 of 3 states with interval >= 21
    assert items[1]["id"] == str(old.id)


async def test_rename(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """BE-DOC-14"""
    doc = await seed.document(db, A, created_at=datetime(2026, 1, 1, tzinfo=UTC))
    resp = await api.patch(f"/documents/{doc.id}", headers=auth(A), json={"title": "  Cells "})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Cells"
    assert datetime.fromisoformat(resp.json()["updated_at"]) > datetime(2026, 1, 1, tzinfo=UTC)


async def test_delete_deck(api: httpx.AsyncClient, db: AsyncSession, storage: FakeStorage) -> None:
    """BE-DOC-15"""
    doc = await seed.document(db, A)
    c = await seed.card(db, doc.id, chunk_id=(await seed.chunk(db, doc.id)).id)
    await seed.state(db, A, c.id)
    storage.put(f"{A}/{doc.id}.pdf", b"%PDF-1.7")
    resp = await api.delete(f"/documents/{doc.id}", headers=auth(A))
    assert resp.status_code == 204
    assert ("delete", [f"{A}/{doc.id}.pdf"]) in storage.calls
    for model, col in (
        (models.Document, models.Document.id),
        (models.Chunk, models.Chunk.document_id),
        (models.Card, models.Card.document_id),
    ):
        n = (
            await db.execute(select(func.count()).select_from(model).where(col == doc.id))
        ).scalar_one()
        assert n == 0, model
    left = select(func.count()).select_from(models.CardState).where(models.CardState.user_id == A)
    assert (await db.execute(left)).scalar_one() == 0


async def test_delete_keeps_rows_when_storage_fails(
    api: httpx.AsyncClient, db: AsyncSession, storage: FakeStorage
) -> None:
    doc_id = (await seed.document(db, A)).id
    storage.fail_with = httpx.ConnectError("down")
    resp = await api.delete(f"/documents/{doc_id}", headers=auth(A))
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "upstream_unavailable"
    assert (await api.get(f"/documents/{doc_id}", headers=auth(A))).status_code == 200


async def test_retry(api: httpx.AsyncClient, db: AsyncSession, queue: FakeQueue) -> None:
    """BE-DOC-17 (API side), BE-DOC-18"""
    failed = await seed.document(db, A, status="failed", error_code="ai_unavailable", page_count=3)
    resp = await api.post(f"/documents/{failed.id}/retry", headers=auth(A))
    assert resp.status_code == 202
    assert resp.json()["status"] == "queued"
    assert resp.json()["error_code"] is None
    assert queue.jobs == [failed.id]

    ready = await seed.document(db, A, status="ready", page_count=3)
    r = await api.post(f"/documents/{ready.id}/retry", headers=auth(A))
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "invalid_state"
    generating = await seed.document(db, A, status="generating", page_count=3)
    g = await api.post(f"/documents/{generating.id}/retry", headers=auth(A))
    assert g.json()["error"]["code"] == "already_processing"


async def test_show_source(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """BE-DOC-19"""
    doc = await seed.document(db, A)
    chunk = await seed.chunk(db, doc.id)
    resp = await api.get(f"/documents/{doc.id}/chunks/{chunk.id}", headers=auth(A))
    assert resp.status_code == 200
    assert resp.json() | {"id": None} == {
        "id": None,
        "document_id": str(doc.id),
        "idx": 0,
        "heading": "Light reactions",
        "content": "Chlorophyll absorbs light.",
        "page_start": 3,
        "page_end": 4,
    }
    other = await api.get(f"/documents/{doc.id}/chunks/{chunk.id}", headers=auth(B))
    assert other.status_code == 404


async def test_other_users_document_is_404(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """BE-AUTH-16"""
    doc = await seed.document(db, A)
    for method, path, body in (
        ("GET", f"/documents/{doc.id}", None),
        ("PATCH", f"/documents/{doc.id}", {"title": "Mine now"}),
        ("POST", f"/documents/{doc.id}/process", None),
        ("POST", f"/documents/{doc.id}/retry", None),
        ("DELETE", f"/documents/{doc.id}", None),
        ("GET", f"/documents/{doc.id}/cards", None),
        ("GET", f"/documents/{uuid4()}", None),
    ):
        resp = await api.request(method, path, headers=auth(B), json=body)
        assert resp.status_code == 404, (method, path)
        assert resp.json()["error"]["code"] == "not_found"


async def test_sql_injection_title_is_plain_text(api: httpx.AsyncClient) -> None:
    """BE-SEC-02"""
    title = "'); drop table app.cards; --"
    resp = await api.post("/documents", headers=auth(A), json=_create(title=title))
    assert resp.status_code == 201
    assert resp.json()["document"]["title"] == title
    assert (await api.get("/documents", headers=auth(A))).status_code == 200
