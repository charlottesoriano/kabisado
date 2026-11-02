"""QA edge cases for BE-CRD-01..04 and 06."""

from datetime import timedelta
from typing import Any
from uuid import UUID

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models
from tests import seed
from tests.conftest import auth, needs_db

pytestmark = [pytest.mark.api, needs_db]

A, B = "user_A", "user_B"


async def _deck_with(db: AsyncSession, type: str = "flashcard", **kw: Any) -> tuple[UUID, UUID]:
    doc_id = (await seed.document(db, A)).id
    card_id = (await seed.card(db, doc_id, type=type, **kw)).id
    return doc_id, card_id


async def _payload(db: AsyncSession, card_id: UUID) -> dict[str, Any]:
    stmt = select(models.Card.payload).where(models.Card.id == card_id)
    value: dict[str, Any] = (await db.execute(stmt)).scalar_one()
    return value


def _locs(resp: httpx.Response) -> list[str]:
    return [".".join(str(p) for p in d["loc"]) for d in resp.json()["error"].get("details", [])]


async def test_mcq_field_errors_point_at_the_field(
    api: httpx.AsyncClient, db: AsyncSession
) -> None:
    """BE-CRD-04: 422 with field errors naming options / answer_index; payload unchanged."""
    _, card_id = await _deck_with(db, "mcq")
    dup = await api.patch(
        f"/cards/{card_id}",
        headers=auth(A),
        json={"payload": {**seed.MCQ, "options": ["Same", " same ", "B", "C"]}},
    )
    assert dup.status_code == 422
    assert any("options" in loc for loc in _locs(dup)), _locs(dup)
    idx = await api.patch(
        f"/cards/{card_id}", headers=auth(A), json={"payload": {**seed.MCQ, "answer_index": 5}}
    )
    assert idx.status_code == 422
    assert any("answer_index" in loc for loc in _locs(idx)), _locs(idx)
    assert await _payload(db, card_id) == seed.MCQ


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({**seed.MCQ, "options": ["A", "B", "C"]}, id="3 options"),
        pytest.param({**seed.MCQ, "options": ["A", "B", "C", "D", "E"]}, id="5 options"),
        pytest.param({**seed.MCQ, "options": ["A", "B", "C", "  "]}, id="blank option"),
        pytest.param({**seed.MCQ, "answer_index": -1}, id="negative index"),
        pytest.param({**seed.MCQ, "question": "Short?"}, id="question < 10"),
        pytest.param({**seed.MCQ, "explanation": "x" * 601}, id="explanation > 600"),
    ],
)
async def test_mcq_edit_rules(
    api: httpx.AsyncClient, db: AsyncSession, payload: dict[str, Any]
) -> None:
    """BE-CRD-04 variants: the same rules as the AI output schema (03 section 5.3)."""
    _, card_id = await _deck_with(db, "mcq")
    resp = await api.patch(f"/cards/{card_id}", headers=auth(A), json={"payload": payload})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"front": "Hi?", "back": "x"}, id="front < 5"),
        pytest.param({"front": "What is ATP?", "back": ""}, id="empty back"),
        pytest.param({"front": "What is ATP?", "back": "   "}, id="blank back"),
        pytest.param({"front": "x" * 301, "back": "y"}, id="front > 300"),
        pytest.param({"front": "What is ATP?"}, id="missing back"),
    ],
)
async def test_flashcard_edit_rules(
    api: httpx.AsyncClient, db: AsyncSession, payload: dict[str, Any]
) -> None:
    _, card_id = await _deck_with(db)
    resp = await api.patch(f"/cards/{card_id}", headers=auth(A), json={"payload": payload})
    assert resp.status_code == 422
    assert await _payload(db, card_id) == seed.FLASHCARD


async def test_edit_rejects_extra_top_level_fields(
    api: httpx.AsyncClient, db: AsyncSession
) -> None:
    """Clients can't set flagged/edited/type/document_id through PATCH."""
    _, card_id = await _deck_with(db)
    for extra in ({"type": "mcq"}, {"flagged": True}, {"document_id": str(card_id)}):
        resp = await api.patch(
            f"/cards/{card_id}", headers=auth(A), json={"payload": seed.FLASHCARD, **extra}
        )
        assert resp.status_code == 422, extra


async def test_edit_is_trimmed_and_keeps_schedule(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """BE-CRD-03: the edit is saved normalised; the card's SM-2 state is not reset."""
    _, card_id = await _deck_with(db)
    await seed.state(db, A, card_id, due_in=timedelta(days=5), interval_days=30)
    resp = await api.patch(
        f"/cards/{card_id}",
        headers=auth(A),
        json={"payload": {"front": "  What is ATP?  ", "back": " Energy currency "}},
    )
    assert resp.status_code == 200
    assert resp.json()["payload"] == {"front": "What is ATP?", "back": "Energy currency"}
    interval = (
        await db.execute(
            select(models.CardState.interval_days).where(models.CardState.card_id == card_id)
        )
    ).scalar_one()
    assert interval == 30


async def test_flag_hides_and_edit_restores(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """BE-CRD-01 + BE-CRD-03: flagging removes the card from counts/due; editing brings it
    back. The deck view still lists the flagged card so it can be fixed."""
    doc_id, card_id = await _deck_with(db)
    await seed.state(db, A, card_id, due_in=timedelta(hours=-1))
    flag = await api.post(f"/cards/{card_id}/flag", headers=auth(A), json={"reason": "unclear"})
    assert flag.status_code == 200
    deck = (await api.get(f"/documents/{doc_id}", headers=auth(A))).json()
    assert (deck["due_count"], deck["card_counts"]["flashcard"]) == (0, 0)
    listed = (await api.get(f"/documents/{doc_id}/cards", headers=auth(A))).json()["items"]
    assert [(c["id"], c["flagged"]) for c in listed] == [(str(card_id), True)]

    again = await api.post(f"/cards/{card_id}/flag", headers=auth(A), json={"reason": "off_topic"})
    assert again.status_code == 200
    assert again.json()["flag_reason"] == "off_topic"

    edit = await api.patch(
        f"/cards/{card_id}",
        headers=auth(A),
        json={"payload": {"front": "What is ATP?", "back": "Energy"}},
    )
    assert edit.json()["flagged"] is False
    deck = (await api.get(f"/documents/{doc_id}", headers=auth(A))).json()
    assert (deck["due_count"], deck["card_counts"]["flashcard"]) == (1, 1)


@pytest.mark.parametrize(
    "body", [{}, {"reason": ""}, {"reason": "WRONG_ANSWER"}, {"reason": "unclear", "x": 1}]
)
async def test_flag_body_validation(
    api: httpx.AsyncClient, db: AsyncSession, body: dict[str, Any]
) -> None:
    """BE-CRD-02 variants."""
    _, card_id = await _deck_with(db)
    resp = await api.post(f"/cards/{card_id}/flag", headers=auth(A), json=body)
    assert resp.status_code == 422
    flagged = (
        await db.execute(select(models.Card.flagged).where(models.Card.id == card_id))
    ).scalar_one()
    assert flagged is False


async def test_problem_cards_can_be_flagged_but_not_edited(
    api: httpx.AsyncClient, db: AsyncSession
) -> None:
    _, card_id = await _deck_with(db, "problem")
    edit = await api.patch(f"/cards/{card_id}", headers=auth(A), json={"payload": seed.FLASHCARD})
    assert edit.status_code == 422
    assert edit.json()["error"]["code"] == "not_editable"
    flag = await api.post(f"/cards/{card_id}/flag", headers=auth(A), json={"reason": "unclear"})
    assert flag.status_code == 200


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "type=essay", "cursor=", "cursor=%%%"])
async def test_card_list_query_validation(
    api: httpx.AsyncClient, db: AsyncSession, query: str
) -> None:
    doc_id = (await seed.document(db, A)).id
    resp = await api.get(f"/documents/{doc_id}/cards?{query}", headers=auth(A))
    assert resp.status_code == 422, (query, resp.text)
    assert resp.json()["error"]["code"] == "validation_error"


async def test_card_list_type_filter_and_small_pages(
    api: httpx.AsyncClient, db: AsyncSession
) -> None:
    """BE-CRD-06 with a filter: the type filter holds across pages."""
    doc_id = (await seed.document(db, A)).id
    mcqs = {str((await seed.card(db, doc_id, type="mcq")).id) for _ in range(3)}
    for _ in range(2):
        await seed.card(db, doc_id)
    seen: list[str] = []
    cursor = None
    while True:
        params: dict[str, Any] = {"type": "mcq", "limit": 1}
        if cursor:
            params["cursor"] = cursor
        page = (await api.get(f"/documents/{doc_id}/cards", headers=auth(A), params=params)).json()
        seen += [c["id"] for c in page["items"]]
        assert all(c["type"] == "mcq" for c in page["items"])
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert sorted(seen) == sorted(mcqs)


async def test_exactly_one_full_page_has_no_next_cursor(
    api: httpx.AsyncClient, db: AsyncSession
) -> None:
    doc_id = (await seed.document(db, A)).id
    for _ in range(50):
        await seed.card(db, doc_id)
    page = (await api.get(f"/documents/{doc_id}/cards", headers=auth(A))).json()
    assert len(page["items"]) == 50
    assert page["next_cursor"] is None


async def test_card_of_deleted_deck_is_404(api: httpx.AsyncClient, db: AsyncSession) -> None:
    doc_id, card_id = await _deck_with(db)
    assert (await api.delete(f"/documents/{doc_id}", headers=auth(A))).status_code == 204
    resp = await api.post(f"/cards/{card_id}/flag", headers=auth(A), json={"reason": "unclear"})
    assert resp.status_code == 404
