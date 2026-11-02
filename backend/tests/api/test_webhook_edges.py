"""QA edge cases for BE-AUTH-11..15: the Clerk webhook (Svix-signed with the test secret)."""

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from svix.webhooks import Webhook

from app.config import get_settings
from app.db import models
from tests import seed
from tests.api.test_me_and_webhooks import _signed, _user_event
from tests.conftest import WEBHOOK_SECRET, auth, needs_db
from tests.fakes import FakeStorage
from tests.seed_extra import count, deck_row_counts, full_deck

pytestmark = [pytest.mark.api, needs_db]


def _signed_raw(body: bytes, msg_id: str, at: datetime) -> dict[str, str]:
    signature = Webhook(WEBHOOK_SECRET).sign(msg_id, at, body.decode())
    return {
        "svix-id": msg_id,
        "svix-timestamp": str(int(at.timestamp())),
        "svix-signature": signature,
        "content-type": "application/json",
    }


async def _events(db: AsyncSession) -> int:
    return await count(db, models.WebhookEvent)


async def test_bad_signature_records_nothing(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """BE-AUTH-12: tampered body -> 400 and no DB change at all (not even the event row)."""
    before = await _events(db)
    body, headers = _signed(_user_event("user.created", "user_X"))
    resp = await api.post("/webhooks/clerk", content=body + b" ", headers=headers)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "invalid_signature"
    assert await _events(db) == before
    assert await count(db, models.Profile, models.Profile.id == "user_X") == 0


@pytest.mark.parametrize(
    "drop", ["svix-id", "svix-timestamp", "svix-signature"], ids=lambda h: f"missing {h}"
)
async def test_missing_svix_header_is_400(
    api: httpx.AsyncClient, db: AsyncSession, drop: str
) -> None:
    body, headers = _signed(_user_event("user.created", "user_H"))
    del headers[drop]
    resp = await api.post("/webhooks/clerk", content=body, headers=headers)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "invalid_signature"
    assert await count(db, models.Profile, models.Profile.id == "user_H") == 0


async def test_stale_timestamp_is_rejected(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """A captured delivery replayed after Svix's tolerance window is rejected."""
    body = json.dumps(_user_event("user.created", "user_old")).encode()
    headers = _signed_raw(body, "msg_stale", datetime.now(UTC) - timedelta(minutes=30))
    resp = await api.post("/webhooks/clerk", content=body, headers=headers)
    assert resp.status_code == 400
    assert await count(db, models.Profile, models.Profile.id == "user_old") == 0


async def test_signed_but_malformed_json_is_400(api: httpx.AsyncClient) -> None:
    body = b"{not json"
    headers = _signed_raw(body, "msg_bad_json", datetime.now(UTC))
    resp = await api.post("/webhooks/clerk", content=body, headers=headers)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "bad_request"


async def test_replay_with_same_svix_id_changes_nothing(
    api: httpx.AsyncClient, db: AsyncSession
) -> None:
    """BE-AUTH-13: a second delivery with the same svix-id is ignored even if its payload
    differs (it must not overwrite the email)."""
    body, headers = _signed(_user_event("user.created", "user_R2", email="a@x.test"), "msg_r2")
    assert (await api.post("/webhooks/clerk", content=body, headers=headers)).status_code == 200
    body2, headers2 = _signed(_user_event("user.updated", "user_R2", email="b@x.test"), "msg_r2")
    again = await api.post("/webhooks/clerk", content=body2, headers=headers2)
    assert again.status_code == 200
    assert again.json() == {"status": "duplicate"}
    p = await db.get(models.Profile, "user_R2", populate_existing=True)
    assert p is not None and p.email == "a@x.test"


async def test_user_updated_changes_email(api: httpx.AsyncClient, db: AsyncSession) -> None:
    await api.get("/me", headers=auth("user_U"))
    body, headers = _signed(_user_event("user.updated", "user_U", email="new@x.test"))
    resp = await api.post("/webhooks/clerk", content=body, headers=headers)
    assert resp.json() == {"status": "processed"}
    p = await db.get(models.Profile, "user_U", populate_existing=True)
    assert p is not None and p.email == "new@x.test"


async def test_user_deleted_full_cascade_keeps_other_users(
    api: httpx.AsyncClient, db: AsyncSession, storage: FakeStorage
) -> None:
    """BE-AUTH-15 as written: 2 decks, reviews and attempts; every related row gone; Storage
    delete covers both files; another user's data is untouched."""
    decks = [await full_deck(db, "user_D", title=t) for t in ("Bio", "Chem")]
    other = await full_deck(db, "user_E")
    for d in (*decks, other):
        storage.put(f"{d.document.user_id}/{d.document.id}.pdf", b"%PDF-1.7")
    before_other = await deck_row_counts(db, other, "user_E")

    body, headers = _signed(_user_event("user.deleted", "user_D"))
    resp = await api.post("/webhooks/clerk", content=body, headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"status": "processed"}

    assert await count(db, models.Profile, models.Profile.id == "user_D") == 0
    for d in decks:
        assert set((await deck_row_counts(db, d, "user_D")).values()) == {0}
        assert f"user_D/{d.document.id}.pdf" not in storage.objects
    assert await count(db, models.Review, models.Review.user_id == "user_D") == 0
    assert await count(db, models.Attempt, models.Attempt.user_id == "user_D") == 0
    assert await deck_row_counts(db, other, "user_E") == before_other
    assert f"user_E/{other.document.id}.pdf" in storage.objects


async def test_user_deleted_for_unknown_user_is_ok(
    api: httpx.AsyncClient, storage: FakeStorage
) -> None:
    body, headers = _signed(_user_event("user.deleted", "user_never_seen"))
    resp = await api.post("/webhooks/clerk", content=body, headers=headers)
    assert resp.status_code == 200
    assert ("delete_prefix", "user_never_seen") in storage.calls


async def test_missing_webhook_secret_fails_closed(
    api: httpx.AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CLERK_WEBHOOK_SECRET", "")
    get_settings.cache_clear()
    try:
        body, headers = _signed(_user_event("user.created", "user_NS"))
        resp = await api.post("/webhooks/clerk", content=body, headers=headers)
        assert resp.status_code == 503
        assert resp.json()["error"]["code"] == "service_unavailable"
        assert await count(db, models.Profile, models.Profile.id == "user_NS") == 0
    finally:
        get_settings.cache_clear()


async def test_webhook_does_not_trust_a_bearer_token(
    api: httpx.AsyncClient, db: AsyncSession
) -> None:
    """A valid Clerk session token is no substitute for the Svix signature."""
    await seed.profile(db, "user_T")
    payload: dict[str, Any] = _user_event("user.deleted", "user_T")
    resp = await api.post("/webhooks/clerk", json=payload, headers=auth("user_T"))
    assert resp.status_code == 400
    assert await count(db, models.Profile, models.Profile.id == "user_T") == 1
