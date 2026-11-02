"""SupabaseStorage against a mocked Storage API (respx); no real Supabase calls."""

import time

import httpx
import jwt
import pytest
import respx

from app.errors import UpstreamTimeout
from app.services.storage import SupabaseStorage

BASE = "https://sb.test/storage/v1"


def _storage() -> SupabaseStorage:
    return SupabaseStorage("https://sb.test", "service-key", "uploads", timeout=5)


@pytest.mark.unit
async def test_signed_upload_url_reads_expiry_from_token(mock_http: respx.MockRouter) -> None:
    exp = int(time.time()) + 7200
    token = jwt.encode({"exp": exp, "url": "uploads/u/d.pdf"}, "x" * 32, algorithm="HS256")
    route = mock_http.post(f"{BASE}/object/upload/sign/uploads/u/d.pdf").mock(
        return_value=httpx.Response(
            200, json={"url": f"/object/upload/sign/uploads/u/d.pdf?token={token}"}
        )
    )
    storage = _storage()
    upload = await storage.create_signed_upload_url("u/d.pdf")
    await storage.aclose()
    assert int(upload.expires_at.timestamp()) == exp
    assert upload.token == token
    assert upload.url.startswith(f"{BASE}/object/upload/sign/uploads/u/d.pdf?token=")
    sent = route.calls.last.request
    assert sent.headers["x-upsert"] == "true"
    assert sent.headers["authorization"] == "Bearer service-key"


@pytest.mark.unit
async def test_stat_missing_and_present(mock_http: respx.MockRouter) -> None:
    mock_http.get(f"{BASE}/object/info/uploads/u/missing.pdf").mock(
        return_value=httpx.Response(
            400, json={"statusCode": "404", "error": "not_found", "message": "Object not found"}
        )
    )
    mock_http.get(f"{BASE}/object/info/uploads/u/d.pdf").mock(
        return_value=httpx.Response(200, json={"name": "u/d.pdf", "size": 1234})
    )
    storage = _storage()
    assert await storage.stat("u/missing.pdf") is None
    found = await storage.stat("u/d.pdf")
    await storage.aclose()
    assert found is not None and found.size == 1234


@pytest.mark.unit
async def test_timeout_is_translated(mock_http: respx.MockRouter) -> None:
    mock_http.get(f"{BASE}/object/info/uploads/u/d.pdf").mock(side_effect=httpx.ReadTimeout)
    storage = _storage()
    with pytest.raises(UpstreamTimeout) as info:
        await storage.stat("u/d.pdf")
    await storage.aclose()
    assert info.value.operation == "storage.stat"


@pytest.mark.unit
async def test_delete_prefix_lists_then_removes(mock_http: respx.MockRouter) -> None:
    listing = mock_http.post(f"{BASE}/object/list/uploads").mock(
        side_effect=[
            httpx.Response(200, json=[{"name": "a.pdf", "id": "1"}, {"name": "b.pdf", "id": "2"}]),
            httpx.Response(200, json=[]),
        ]
    )
    remove = mock_http.delete(f"{BASE}/object/uploads").mock(
        return_value=httpx.Response(200, json=[])
    )
    storage = _storage()
    assert await storage.delete_prefix("user_1") == 2
    await storage.aclose()
    assert listing.call_count == 2
    assert b'"user_1/a.pdf"' in remove.calls.last.request.content


@pytest.mark.unit
async def test_ensure_bucket_creates_when_missing(mock_http: respx.MockRouter) -> None:
    mock_http.get(f"{BASE}/bucket/uploads").mock(
        return_value=httpx.Response(
            400, json={"statusCode": "404", "error": "not_found", "message": "Bucket not found"}
        )
    )
    create = mock_http.post(f"{BASE}/bucket").mock(
        return_value=httpx.Response(200, json={"name": "uploads"})
    )
    storage = _storage()
    assert await storage.ensure_bucket(20 * 1024 * 1024) == "created"
    await storage.aclose()
    sent = create.calls.last.request.content
    assert b'"public": false' in sent or b'"public":false' in sent
    assert b"application/pdf" in sent
    assert b"20971520" in sent
