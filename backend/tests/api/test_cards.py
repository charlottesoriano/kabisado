"""BE-CRD-01..04, 06: card list, edit, flag."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests import seed
from tests.conftest import auth, needs_db

pytestmark = [pytest.mark.api, needs_db]

A, B = "user_A", "user_B"


async def test_flag(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """BE-CRD-01 (flag + hidden from deck due count), BE-CRD-02"""
    doc = await seed.document(db, A)
    card = await seed.card(db, doc.id)
    await seed.state(db, A, card.id)
    resp = await api.post(
        f"/cards/{card.id}/flag", headers=auth(A), json={"reason": "wrong_answer"}
    )
    assert resp.status_code == 200
    assert resp.json()["flagged"] is True
    assert resp.json()["flag_reason"] == "wrong_answer"
    deck = (await api.get(f"/documents/{doc.id}", headers=auth(A))).json()
    assert deck["due_count"] == 0
    assert deck["card_counts"]["flashcard"] == 0
    bad = await api.post(f"/cards/{card.id}/flag", headers=auth(A), json={"reason": "boring"})
    assert bad.status_code == 422


async def test_edit_flashcard_clears_flag(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """BE-CRD-03"""
    doc = await seed.document(db, A)
    card = await seed.card(db, doc.id, flagged=True)
    new = {"front": "What does chlorophyll absorb?", "back": "Light"}
    resp = await api.patch(f"/cards/{card.id}", headers=auth(A), json={"payload": new})
    assert resp.status_code == 200
    body = resp.json()
    assert body["payload"] == new
    assert body["edited"] is True
    assert body["flagged"] is False
    assert body["flag_reason"] is None


async def test_edit_mcq_invalid(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """BE-CRD-04"""
    doc = await seed.document(db, A)
    card = await seed.card(db, doc.id, type="mcq")
    for payload in (
        {**seed.MCQ, "options": ["Same", "same", "B", "C"]},
        {**seed.MCQ, "answer_index": 5},
    ):
        resp = await api.patch(f"/cards/{card.id}", headers=auth(A), json={"payload": payload})
        assert resp.status_code == 422
        err = resp.json()["error"]
        assert err["code"] == "validation_error"
        assert err["details"]


async def test_edit_type_mismatch_and_problem(api: httpx.AsyncClient, db: AsyncSession) -> None:
    doc_id = (await seed.document(db, A)).id
    mcq_id = (await seed.card(db, doc_id, type="mcq")).id
    problem_id = (await seed.card(db, doc_id, type="problem")).id
    resp = await api.patch(f"/cards/{mcq_id}", headers=auth(A), json={"payload": seed.FLASHCARD})
    assert resp.status_code == 422
    assert resp.json()["error"]["details"][0]["loc"] == ["body", "payload"]
    p = await api.patch(f"/cards/{problem_id}", headers=auth(A), json={"payload": seed.FLASHCARD})
    assert p.json()["error"]["code"] == "not_editable"


async def test_pagination(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """BE-CRD-06: 120 cards, page size 50 -> 3 pages, no duplicates or gaps"""
    doc = await seed.document(db, A)
    base = datetime(2026, 10, 1, tzinfo=UTC)
    ids = set()
    for i in range(120):
        # pairs share a timestamp to exercise the id tie-break
        c = await seed.card(db, doc.id, created_at=base + timedelta(seconds=i // 2))
        ids.add(str(c.id))
    seen: list[str] = []
    cursor = None
    pages = 0
    while True:
        params: dict[str, str] = {"cursor": cursor} if cursor else {}
        resp = await api.get(f"/documents/{doc.id}/cards", headers=auth(A), params=params)
        assert resp.status_code == 200
        page = resp.json()
        seen += [c["id"] for c in page["items"]]
        pages += 1
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert pages == 3
    assert len(seen) == len(set(seen)) == 120
    assert set(seen) == ids

    only_mcq = await api.get(f"/documents/{doc.id}/cards?type=mcq", headers=auth(A))
    assert only_mcq.json() == {"items": [], "next_cursor": None}
    bad = await api.get(f"/documents/{doc.id}/cards?cursor=garbage!", headers=auth(A))
    assert bad.status_code == 422


async def test_other_users_card_is_404(api: httpx.AsyncClient, db: AsyncSession) -> None:
    doc = await seed.document(db, A)
    card = await seed.card(db, doc.id)
    for method, path, body in (
        ("PATCH", f"/cards/{card.id}", {"payload": seed.FLASHCARD}),
        ("POST", f"/cards/{card.id}/flag", {"reason": "unclear"}),
        ("POST", f"/cards/{uuid4()}/flag", {"reason": "unclear"}),
    ):
        resp = await api.request(method, path, headers=auth(B), json=body)
        assert resp.status_code == 404
