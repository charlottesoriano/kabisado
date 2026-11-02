"""BE-SEC-01 / BE-AUTH-16 sweep: every 3a endpoint with an id, called by user B with user A's
ids, is 404 ``not_found``, leaks nothing, and changes nothing.

The sweep is driven by the OpenAPI schema, so a new id-bearing route fails this test until it
is added to ``CALLS``."""

from typing import Any

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models
from app.main import app
from tests import seed
from tests.conftest import auth, needs_db
from tests.fakes import FakeQueue, FakeStorage
from tests.unit.test_services_3a import make_pdf

pytestmark = [pytest.mark.security, pytest.mark.api, needs_db]

A, B = "user_A", "user_B"
SECRET_TITLE = "Alice private deck"  # noqa: S105 (not a password)

# (method, template) -> request body
CALLS: dict[tuple[str, str], dict[str, Any] | None] = {
    ("GET", "/documents/{document_id}"): None,
    ("PATCH", "/documents/{document_id}"): {"title": "Mine now"},
    ("DELETE", "/documents/{document_id}"): None,
    ("POST", "/documents/{document_id}/process"): None,
    ("POST", "/documents/{document_id}/retry"): None,
    ("GET", "/documents/{document_id}/chunks/{chunk_id}"): None,
    ("GET", "/documents/{document_id}/cards"): None,
    ("PATCH", "/cards/{card_id}"): {"payload": {"front": "Overwritten by B?", "back": "Yes"}},
    ("POST", "/cards/{card_id}/flag"): {"reason": "wrong_answer"},
}


def _id_routes() -> set[tuple[str, str]]:
    return {
        (method.upper(), path)
        for path, ops in app.openapi()["paths"].items()
        if "{" in path
        for method in ops
    }


async def test_sweep_covers_every_id_route() -> None:
    assert _id_routes() == set(CALLS), "add new id routes to the isolation sweep"


@pytest.mark.parametrize("status", ["queued", "failed"])
async def test_other_users_ids_are_404_and_change_nothing(
    api: httpx.AsyncClient,
    db: AsyncSession,
    storage: FakeStorage,
    queue: FakeQueue,
    status: str,
) -> None:
    """``queued`` with the PDF uploaded (so /process would succeed for the owner) and
    ``failed`` (so /retry would succeed for the owner)."""
    doc_id = (await seed.document(db, A, title=SECRET_TITLE, status=status)).id
    ids = {"document_id": str(doc_id)}
    ids["chunk_id"] = str((await seed.chunk(db, doc_id)).id)
    ids["card_id"] = str((await seed.card(db, doc_id, type="mcq")).id)
    storage.put(f"{A}/{doc_id}.pdf", make_pdf(3))
    await seed.profile(db, B)

    for (method, template), body in CALLS.items():
        path = template.format(**ids)
        resp = await api.request(method, path, headers=auth(B), json=body)
        assert resp.status_code == 404, (method, template, resp.status_code, resp.text)
        err = resp.json()["error"]
        assert err["code"] == "not_found", (method, template)
        for leaked in (SECRET_TITLE, "Chlorophyll", "Mitochondrion", A):
            assert leaked not in resp.text, (method, template, leaked)

    stored = (
        await db.execute(
            select(models.Document.title, models.Document.status, models.Document.page_count).where(
                models.Document.id == doc_id
            )
        )
    ).one()
    assert tuple(stored) == (SECRET_TITLE, status, None)
    card = (
        await db.execute(
            select(models.Card.payload, models.Card.flagged, models.Card.edited).where(
                models.Card.document_id == doc_id
            )
        )
    ).one()
    assert tuple(card) == (seed.MCQ, False, False)
    assert queue.jobs == []
    assert [c for c in storage.names() if c in ("delete", "download", "stat")] == []


async def test_same_answer_for_missing_and_foreign_ids(
    api: httpx.AsyncClient, db: AsyncSession
) -> None:
    """A foreign id and a non-existent id are indistinguishable (no probing)."""
    doc_id = (await seed.document(db, A)).id
    foreign = await api.get(f"/documents/{doc_id}", headers=auth(B))
    missing = await api.get("/documents/00000000-0000-4000-8000-000000000000", headers=auth(B))
    assert foreign.status_code == missing.status_code == 404
    strip = ("request_id", "debug")
    a = {k: v for k, v in foreign.json()["error"].items() if k not in strip}
    b = {k: v for k, v in missing.json()["error"].items() if k not in strip}
    assert a == b
