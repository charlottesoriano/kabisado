import httpx
import pytest

from app.main import app


@pytest.mark.api
async def test_health_ok(client: httpx.AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.api
def test_openapi_has_stable_operation_id() -> None:
    schema = app.openapi()
    assert schema["paths"]["/health"]["get"]["operationId"] == "health"
    assert "HealthResponse" in schema["components"]["schemas"]
