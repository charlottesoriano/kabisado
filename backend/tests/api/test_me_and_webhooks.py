"""BE-AUTH-09..15: /me and the Clerk webhook (Svix-signed with a test secret)."""

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from svix.webhooks import Webhook

from app.db import models
from tests import seed
from tests.conftest import WEBHOOK_SECRET, auth, needs_db
from tests.fakes import FakeStorage

pytestmark = [pytest.mark.api, needs_db]


def _user_event(
    kind: str, user_id: str, email: str = "ana@example.com", **extra: Any
) -> dict[str, Any]:
    data: dict[str, Any] = {"id": user_id}
    if kind != "user.deleted":
        data.update(
            email_addresses=[{"id": "em_1", "email_address": email}],
            primary_email_address_id="em_1",
            first_name="Ana",
            last_name="Reyes",
            **extra,
        )
    return {"type": kind, "data": data}


def _signed(event: dict[str, Any], svix_id: str | None = None) -> tuple[bytes, dict[str, str]]:
    body = json.dumps(event)
    msg_id = svix_id or f"msg_{uuid4().hex}"
    now = datetime.now(UTC)
    signature = Webhook(WEBHOOK_SECRET).sign(msg_id, now, body)
    headers = {
        "svix-id": msg_id,
        "svix-timestamp": str(int(now.timestamp())),
        "svix-signature": signature,
        "content-type": "application/json",
    }
    return body.encode(), headers


async def _count(db: AsyncSession, model: Any, *where: Any) -> int:
    return int(
        (await db.execute(select(func.count()).select_from(model).where(*where))).scalar_one()
    )


async def test_me_creates_profile_once(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """BE-AUTH-09, BE-AUTH-10"""
    first = await api.get("/me", headers=auth("user_new"))
    assert first.status_code == 200
    assert first.json()["id"] == "user_new"
    assert first.json()["timezone"] == "Asia/Manila"
    assert (await api.get("/me", headers=auth("user_new"))).status_code == 200
    assert await _count(db, models.Profile, models.Profile.id == "user_new") == 1


async def test_patch_me(api: httpx.AsyncClient) -> None:
    resp = await api.patch(
        "/me",
        headers=auth("user_A"),
        json={"display_name": "Ana", "timezone": "Europe/Berlin", "reminder_time": "19:30:00"},
    )
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Ana"
    assert resp.json()["timezone"] == "Europe/Berlin"
    assert resp.json()["reminder_time"] == "19:30:00"

    bad = await api.patch("/me", headers=auth("user_A"), json={"timezone": "Mars/Base"})
    assert bad.status_code == 422
    assert bad.json()["error"]["details"][0]["loc"] == ["body", "timezone"]
    null_tz = await api.patch("/me", headers=auth("user_A"), json={"timezone": None})
    assert null_tz.status_code == 422


async def test_webhook_user_created(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """BE-AUTH-11"""
    body, headers = _signed(_user_event("user.created", "user_W"))
    resp = await api.post("/webhooks/clerk", content=body, headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"status": "processed"}
    p = await db.get(models.Profile, "user_W")
    assert p is not None and p.email == "ana@example.com" and p.display_name == "Ana Reyes"


async def test_webhook_bad_signature(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """BE-AUTH-12"""
    body, headers = _signed(_user_event("user.created", "user_X"))
    tampered = body.replace(b"user_X", b"user_Y")
    resp = await api.post("/webhooks/clerk", content=tampered, headers=headers)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "invalid_signature"
    assert await _count(db, models.Profile, models.Profile.id.in_(["user_X", "user_Y"])) == 0


async def test_webhook_replay_is_ignored(api: httpx.AsyncClient, db: AsyncSession) -> None:
    """BE-AUTH-13"""
    body, headers = _signed(_user_event("user.created", "user_R"), svix_id="msg_replay")
    assert (await api.post("/webhooks/clerk", content=body, headers=headers)).status_code == 200
    again = await api.post("/webhooks/clerk", content=body, headers=headers)
    assert again.status_code == 200
    assert again.json() == {"status": "duplicate"}
    assert await _count(db, models.WebhookEvent, models.WebhookEvent.svix_id == "msg_replay") == 1


async def test_webhook_after_me_updates_email_keeps_name(
    api: httpx.AsyncClient, db: AsyncSession
) -> None:
    """BE-AUTH-14 (+ a name set with PATCH /me survives)"""
    await api.patch("/me", headers=auth("user_M"), json={"display_name": "Mia"})
    body, headers = _signed(_user_event("user.created", "user_M", email="mia@example.com"))
    assert (await api.post("/webhooks/clerk", content=body, headers=headers)).status_code == 200
    assert await _count(db, models.Profile, models.Profile.id == "user_M") == 1
    p = await db.get(models.Profile, "user_M", populate_existing=True)
    assert p is not None and p.email == "mia@example.com" and p.display_name == "Mia"


async def test_webhook_user_deleted_cascades(
    api: httpx.AsyncClient, db: AsyncSession, storage: FakeStorage
) -> None:
    """BE-AUTH-15"""
    docs = [await seed.document(db, "user_D", title=t) for t in ("Bio", "Chem")]
    c = await seed.card(db, docs[0].id)
    await seed.state(db, "user_D", c.id)
    for d in docs:
        storage.put(f"user_D/{d.id}.pdf", b"%PDF-1.7")
    body, headers = _signed(_user_event("user.deleted", "user_D"))
    resp = await api.post("/webhooks/clerk", content=body, headers=headers)
    assert resp.status_code == 200
    assert ("delete_prefix", "user_D") in storage.calls
    assert storage.objects == {}
    assert await _count(db, models.Profile, models.Profile.id == "user_D") == 0
    assert await _count(db, models.Document, models.Document.user_id == "user_D") == 0
    assert await _count(db, models.CardState, models.CardState.user_id == "user_D") == 0


async def test_webhook_storage_failure_is_retryable(
    api: httpx.AsyncClient, db: AsyncSession, storage: FakeStorage
) -> None:
    await seed.profile(db, "user_F")
    storage.fail_with = httpx.ConnectError("down")
    body, headers = _signed(_user_event("user.deleted", "user_F"))
    resp = await api.post("/webhooks/clerk", content=body, headers=headers)
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "upstream_unavailable"
    assert await _count(db, models.Profile, models.Profile.id == "user_F") == 1
    svix_id = headers["svix-id"]
    assert await _count(db, models.WebhookEvent, models.WebhookEvent.svix_id == svix_id) == 0


async def test_unhandled_event_type_is_recorded(api: httpx.AsyncClient) -> None:
    body, headers = _signed({"type": "session.created", "data": {"id": "sess_1"}})
    resp = await api.post("/webhooks/clerk", content=body, headers=headers)
    assert resp.json() == {"status": "ignored"}
