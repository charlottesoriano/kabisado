"""QA edge cases for BE-DOC-01..19 (API side; the generation job body is out of scope)."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models
from app.services.stats import today_bounds
from tests import seed
from tests.conftest import auth, needs_db
from tests.fakes import FakeQueue, FakeStorage
from tests.seed_extra import count, deck_row_counts, full_deck
from tests.unit.test_services_3a import make_pdf

pytestmark = [pytest.mark.api, needs_db]

A, B = "user_A", "user_B"
MIB = 1024 * 1024
TEXT = "Cells are the basic unit of life. " * 10  # 340 chars


def _create(**overrides: Any) -> dict[str, Any]:
    return {"title": "Biology", "filename": "notes.pdf", "size_bytes": 2 * MIB} | overrides


async def _created(api: httpx.AsyncClient, user: str = A) -> dict[str, Any]:
    resp = await api.post("/documents", headers=auth(user), json=_create())
    assert resp.status_code == 201, resp.text
    body: dict[str, Any] = resp.json()
    return body


async def _uploaded(api: httpx.AsyncClient, storage: FakeStorage, data: bytes) -> str:
    body = await _created(api)
    storage.put(body["upload"]["path"], data)
    return str(body["document"]["id"])


# BE-DOC-01 ------------------------------------------------------------------------------------
async def test_create_response_shape_and_two_hour_url(api: httpx.AsyncClient) -> None:
    """BE-DOC-01: 201, queued, upload URL for {user}/{doc}.pdf expiring ~2 h ahead."""
    body = await _created(api)
    doc, upload = body["document"], body["upload"]
    assert doc["status"] == "queued"
    assert doc["page_count"] is None
    assert doc["progress"] == {"done": 0, "total": 0}
    assert doc["card_counts"] == {"flashcard": 0, "mcq": 0, "problem": 0}
    assert doc["due_count"] == 0 and doc["mastery_pct"] == 0
    assert upload["path"] == f"{A}/{doc['id']}.pdf"
    assert upload["path"] in upload["url"]
    assert upload["token"]
    ahead = datetime.fromisoformat(upload["expires_at"]) - datetime.now(UTC)
    assert timedelta(hours=1, minutes=55) < ahead <= timedelta(hours=2, minutes=1)


@pytest.mark.parametrize(
    ("filename", "status", "code"),
    [
        ("NOTES.PDF", 201, None),
        ("lecture 5.final.pdf", 201, None),
        ("notes.pdf.docx", 422, "invalid_file"),
        ("notes", 422, "invalid_file"),
        ("notes.pdfx", 422, "invalid_file"),
    ],
)
async def test_filename_extension(
    api: httpx.AsyncClient, filename: str, status: int, code: str | None
) -> None:
    """BE-DOC-03 variants."""
    resp = await api.post("/documents", headers=auth(A), json=_create(filename=filename))
    assert resp.status_code == status, resp.text
    if code:
        assert resp.json()["error"]["code"] == code


@pytest.mark.parametrize(
    ("size", "status", "code"),
    [
        (20 * MIB, 201, None),
        (20 * MIB + 1, 422, "file_too_large"),
        (0, 422, "validation_error"),
        (-5, 422, "validation_error"),
    ],
)
async def test_size_boundaries(
    api: httpx.AsyncClient, size: int, status: int, code: str | None
) -> None:
    """BE-DOC-02 boundary: 20 MB is allowed, one byte more is not."""
    resp = await api.post("/documents", headers=auth(A), json=_create(size_bytes=size))
    assert resp.status_code == status, resp.text
    if code:
        assert resp.json()["error"]["code"] == code


@pytest.mark.security
async def test_client_cannot_choose_owner_or_status(
    api: httpx.AsyncClient, db: AsyncSession
) -> None:
    """The user id comes only from the token: extra fields are rejected, nothing is created."""
    for extra in ({"user_id": B}, {"status": "ready"}, {"file_path": "user_B/x.pdf"}):
        resp = await api.post("/documents", headers=auth(A), json=_create(**extra))
        assert resp.status_code == 422, extra
        assert resp.json()["error"]["code"] == "validation_error"
    assert await count(db, models.Document) == 0


async def test_generate_kinds_are_stored(api: httpx.AsyncClient) -> None:
    resp = await api.post("/documents", headers=auth(A), json=_create(generate_kinds=["flashcard"]))
    assert resp.json()["document"]["generate_kinds"] == ["flashcard"]
    bad = await api.post("/documents", headers=auth(A), json=_create(generate_kinds=["essay"]))
    assert bad.status_code == 422


@pytest.mark.parametrize("bad_id", ["not-a-uuid", "1", "00000000-0000-0000-0000-00000000000g"])
async def test_malformed_ids_are_422_not_500(api: httpx.AsyncClient, bad_id: str) -> None:
    resp = await api.get(f"/documents/{bad_id}", headers=auth(A))
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


async def test_new_user_has_empty_list(api: httpx.AsyncClient) -> None:
    resp = await api.get("/documents", headers=auth("user_brand_new"))
    assert resp.status_code == 200
    assert resp.json() == {"items": []}


# /process -------------------------------------------------------------------------------------
async def test_process_rejects_oversized_stored_file(
    api: httpx.AsyncClient, storage: FakeStorage, queue: FakeQueue
) -> None:
    """BE-DOC-02 server side: the declared size can lie; /process re-checks the real size."""
    doc_id = await _uploaded(api, storage, b"%PDF-1.7\n" + b"0" * (20 * MIB))
    resp = await api.post(f"/documents/{doc_id}/process", headers=auth(A))
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "file_too_large"
    assert queue.jobs == []


@pytest.mark.parametrize(
    "data",
    [
        pytest.param(b"", id="empty"),
        pytest.param(b"%PDF-1.7\n this is not really a pdf", id="magic but corrupt"),
        pytest.param(b"PK\x03\x04" + b"0" * 300, id="docx renamed"),
        pytest.param(b"<html><body>%PDF-</body></html>", id="magic later in file"),
    ],
)
async def test_process_rejects_non_pdfs(
    api: httpx.AsyncClient, storage: FakeStorage, queue: FakeQueue, data: bytes
) -> None:
    """BE-DOC-06 variants."""
    doc_id = await _uploaded(api, storage, data)
    resp = await api.post(f"/documents/{doc_id}/process", headers=auth(A))
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_file"
    assert queue.jobs == []


async def test_process_accepts_exactly_50_pages(
    api: httpx.AsyncClient, storage: FakeStorage, queue: FakeQueue
) -> None:
    """BE-DOC-07 boundary."""
    doc_id = await _uploaded(api, storage, make_pdf(50))
    resp = await api.post(f"/documents/{doc_id}/process", headers=auth(A))
    assert resp.status_code == 202
    assert resp.json()["page_count"] == 50
    assert queue.jobs == [UUID(doc_id)]


async def test_process_queues_encrypted_pdf_for_the_job(
    api: httpx.AsyncClient, storage: FakeStorage, queue: FakeQueue
) -> None:
    """UC-02 5d: an encrypted PDF is accepted by /process; the job reports encrypted_pdf."""
    doc_id = await _uploaded(api, storage, make_pdf(2, encrypted=True))
    resp = await api.post(f"/documents/{doc_id}/process", headers=auth(A))
    assert resp.status_code == 202
    assert queue.jobs == [UUID(doc_id)]


async def test_process_after_invalid_file_can_be_retried_with_a_new_upload(
    api: httpx.AsyncClient, storage: FakeStorage, queue: FakeQueue
) -> None:
    """UC-02 4a: an invalid upload doesn't burn the document; re-upload and process again."""
    doc_id = await _uploaded(api, storage, b"\x89PNG\r\n\x1a\n" + b"0" * 200)
    assert (await api.post(f"/documents/{doc_id}/process", headers=auth(A))).status_code == 422
    storage.put(f"{A}/{doc_id}.pdf", make_pdf(3))
    resp = await api.post(f"/documents/{doc_id}/process", headers=auth(A))
    assert resp.status_code == 202
    assert queue.jobs == [UUID(doc_id)]


@pytest.mark.parametrize("status", ["ready", "failed"])
async def test_process_in_final_states_is_409(
    api: httpx.AsyncClient, db: AsyncSession, queue: FakeQueue, status: str
) -> None:
    doc = await seed.document(db, A, status=status, page_count=3)
    resp = await api.post(f"/documents/{doc.id}/process", headers=auth(A))
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "invalid_state"
    assert queue.jobs == []


async def test_process_enqueue_conflict_keeps_committed_state(
    api: httpx.AsyncClient, storage: FakeStorage, queue: FakeQueue, db: AsyncSession
) -> None:
    """Fix 3 (commit, then enqueue): if a job is already waiting for the document, the
    committed page count stays (that job will process it) and the answer is 409."""
    doc_id = await _uploaded(api, storage, make_pdf(3))
    queue.waiting.add(UUID(doc_id))
    resp = await api.post(f"/documents/{doc_id}/process", headers=auth(A))
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "already_processing"
    stmt = select(models.Document.page_count, models.Document.status).where(
        models.Document.id == UUID(doc_id)
    )
    assert tuple((await db.execute(stmt)).one()) == (3, "queued")
    assert queue.discarded == []  # the waiting job is the real one: keep it


# Pasted text ----------------------------------------------------------------------------------
@pytest.mark.parametrize("length", [200, 100_000])
async def test_paste_length_boundaries_accepted(
    api: httpx.AsyncClient, queue: FakeQueue, length: int
) -> None:
    """BE-DOC-11 boundaries: exactly 200 and exactly 100,000 characters are valid."""
    resp = await api.post(
        "/documents/text", headers=auth(A), json={"title": "N", "text": "a" * length}
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["source_type"] == "text"
    assert resp.json()["status"] == "queued"
    assert len(queue.jobs) == 1


async def test_paste_stores_raw_text_and_no_file(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """BE-DOC-10: the document keeps raw_text and has no file path."""
    resp = await api.post("/documents/text", headers=auth(A), json={"title": "N", "text": TEXT})
    row = (
        await db.execute(
            select(models.Document.raw_text, models.Document.file_path).where(
                models.Document.id == UUID(resp.json()["id"])
            )
        )
    ).one()
    assert row == (TEXT.strip(), None)  # fix 4: stored trimmed


# Daily upload limit ---------------------------------------------------------------------------
async def test_daily_limit_is_20_mixed_pdf_and_text(
    api: httpx.AsyncClient, queue: FakeQueue
) -> None:
    """BE-DOC-12 with the real default: 20 uploads (PDF + pasted), the 21st is 429; another
    user is unaffected."""
    for i in range(20):
        if i % 2:
            r = await api.post("/documents", headers=auth(A), json=_create())
        else:
            r = await api.post(
                "/documents/text", headers=auth(A), json={"title": "N", "text": TEXT}
            )
        assert r.status_code == 201, (i, r.text)
    resp = await api.post("/documents", headers=auth(A), json=_create())
    assert resp.status_code == 429
    assert resp.json()["error"]["code"] == "upload_limit_reached"
    assert (await api.post("/documents", headers=auth(B), json=_create())).status_code == 201


async def test_daily_limit_counts_by_local_day(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """Uploads from yesterday (user's timezone) don't count toward today."""
    start, _ = today_bounds("Asia/Manila")
    for _ in range(20):
        await seed.document(db, A, created_at=start - timedelta(minutes=1))
    assert (await api.post("/documents", headers=auth(A), json=_create())).status_code == 201


async def test_daily_limit_not_reset_by_deleting(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """BE-DOC-12 / 03 section 5.9: the cap protects the shared free AI quota, so the 21st
    upload of the day is refused even if earlier decks were deleted in between."""
    ids = []
    for _ in range(20):
        ids.append((await _created(api))["document"]["id"])
    assert (await api.delete(f"/documents/{ids[0]}", headers=auth(A))).status_code == 204
    resp = await api.post("/documents", headers=auth(A), json=_create())
    assert resp.status_code == 429, "deleting a deck re-opened an upload slot"


# Rename / delete / retry / chunks -------------------------------------------------------------
@pytest.mark.parametrize("title", ["", "   ", "x" * 121])
async def test_rename_validation(api: httpx.AsyncClient, db: AsyncSession, title: str) -> None:
    """BE-DOC-04 for PATCH."""
    doc = await seed.document(db, A, title="Keep")
    resp = await api.patch(f"/documents/{doc.id}", headers=auth(A), json={"title": title})
    assert resp.status_code == 422
    stmt = select(models.Document.title).where(models.Document.id == doc.id)
    assert (await db.execute(stmt)).scalar_one() == "Keep"


async def test_delete_full_deck_removes_every_dependent_row(
    api: httpx.AsyncClient, db: AsyncSession, storage: FakeStorage
) -> None:
    """BE-DOC-15 as written: chunks, cards, states, reviews, attempts (with questions and
    answers) and generation runs are all gone; the user's other deck is untouched."""
    deck = await full_deck(db, A, title="Doomed")
    keep = await full_deck(db, A, title="Keep")
    storage.put(f"{A}/{deck.document.id}.pdf", b"%PDF-1.7")
    before_keep = await deck_row_counts(db, keep, A)
    resp = await api.delete(f"/documents/{deck.document.id}", headers=auth(A))
    assert resp.status_code == 204
    assert resp.content == b""
    assert set((await deck_row_counts(db, deck, A)).values()) == {0}
    assert ("delete", [f"{A}/{deck.document.id}.pdf"]) in storage.calls
    assert await deck_row_counts(db, keep, A) == before_keep
    again = await api.delete(f"/documents/{deck.document.id}", headers=auth(A))
    assert again.status_code == 404


async def test_delete_text_deck_skips_storage(
    api: httpx.AsyncClient, db: AsyncSession, storage: FakeStorage
) -> None:
    doc = await seed.document(db, A, source_type="text")
    resp = await api.delete(f"/documents/{doc.id}", headers=auth(A))
    assert resp.status_code == 204
    assert [c for c in storage.calls if c[0] == "delete"] == []


async def test_retry_keeps_finished_chunks_and_cards(
    api: httpx.AsyncClient, db: AsyncSession, queue: FakeQueue
) -> None:
    """BE-DOC-17 (API side): retry re-queues without touching the 3 done chunks or their
    cards; the job then processes only the 2 failed ones."""
    doc = await seed.document(db, A, status="failed", error_code="ai_unavailable", page_count=3)
    chunks = [await seed.chunk(db, doc.id, idx=i) for i in range(5)]
    for i, c in enumerate(chunks):
        c.gen_status = "done" if i < 3 else "failed"
    await db.commit()
    for c in chunks[:3]:
        await seed.card(db, doc.id, chunk_id=c.id)
    resp = await api.post(f"/documents/{doc.id}/retry", headers=auth(A))
    assert resp.status_code == 202
    assert queue.jobs == [doc.id]
    statuses = (
        (
            await db.execute(
                select(models.Chunk.gen_status)
                .where(models.Chunk.document_id == doc.id)
                .order_by(models.Chunk.idx)
            )
        )
        .scalars()
        .all()
    )
    assert statuses == ["done", "done", "done", "failed", "failed"]
    assert await count(db, models.Card, models.Card.document_id == doc.id) == 3


async def test_retry_enqueue_conflict_keeps_committed_state(
    api: httpx.AsyncClient, db: AsyncSession, queue: FakeQueue
) -> None:
    doc_id = (
        await seed.document(db, A, status="failed", error_code="ai_unavailable", page_count=3)
    ).id
    queue.waiting.add(doc_id)
    resp = await api.post(f"/documents/{doc_id}/retry", headers=auth(A))
    assert resp.status_code == 409
    row = (
        await db.execute(
            select(models.Document.status, models.Document.error_code).where(
                models.Document.id == doc_id
            )
        )
    ).one()
    # Fix 3: retry committed first; a job is already waiting, so the deck stays queued.
    assert tuple(row) == ("queued", None)


async def test_chunk_must_belong_to_the_document_in_the_path(
    api: httpx.AsyncClient, db: AsyncSession
) -> None:
    """BE-DOC-19: a chunk is only reachable under its own document, and only by its owner."""
    doc1 = (await seed.document(db, A)).id
    doc2 = (await seed.document(db, A)).id
    chunk_id = (await seed.chunk(db, doc1)).id
    theirs = (await seed.document(db, B)).id
    for doc_id, user in ((doc2, A), (theirs, B), (doc1, B)):
        resp = await api.get(f"/documents/{doc_id}/chunks/{chunk_id}", headers=auth(user))
        assert resp.status_code == 404, (doc_id, user)
        assert "Chlorophyll" not in resp.text


async def test_progress_is_reported(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """GET /documents/{id} exposes status and progress for polling."""
    doc = await seed.document(db, A, status="generating", page_count=3)
    await db.execute(
        update(models.Document)
        .where(models.Document.id == doc.id)
        .values(progress_done=2, progress_total=5)
    )
    await db.commit()
    body = (await api.get(f"/documents/{doc.id}", headers=auth(A))).json()
    assert body["status"] == "generating"
    assert body["progress"] == {"done": 2, "total": 5}
