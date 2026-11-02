"""The global error utility: translations, envelope, request id, debug object, docs table."""

from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError, NoResultFound, OperationalError
from storage3.exceptions import StorageApiError

import app.errors as errors_module
from app.config import get_settings
from app.errors import (
    ERROR_CLASSES,
    AppError,
    Conflict,
    InternalError,
    NotFound,
    ServiceUnavailable,
    UpstreamError,
    UpstreamTimeout,
    UpstreamUnavailable,
    ValidationFailed,
    error_response,
    guard,
    install_error_handlers,
    to_app_error,
)
from app.observability import RequestIdMiddleware


class _PgError(Exception):
    def __init__(self, sqlstate: str, constraint: str | None = None) -> None:
        super().__init__("pg error")
        self.sqlstate = sqlstate
        self.constraint_name = constraint


def _integrity(sqlstate: str) -> IntegrityError:
    return IntegrityError("INSERT ...", None, _PgError(sqlstate, "uq_x"))


@pytest.mark.unit
@pytest.mark.parametrize(
    ("exc", "cls", "status"),
    [
        (_integrity("23505"), Conflict, 409),
        (_integrity("23503"), Conflict, 409),
        (_integrity("23514"), ValidationFailed, 422),
        (_integrity("23502"), ValidationFailed, 422),
        (NoResultFound(), NotFound, 404),
        (OperationalError("SELECT 1", None, _PgError("08006")), ServiceUnavailable, 503),
        (httpx.ReadTimeout("slow"), UpstreamTimeout, 503),
        (TimeoutError(), UpstreamTimeout, 503),
        (httpx.ConnectError("refused"), UpstreamUnavailable, 503),
        (
            httpx.HTTPStatusError(
                "boom",
                request=httpx.Request("GET", "https://x.test"),
                response=httpx.Response(500),
            ),
            UpstreamError,
            502,
        ),
        (StorageApiError("bad", "InternalError", 500), UpstreamError, 502),
        (ConnectionRefusedError(), ServiceUnavailable, 503),
        (RuntimeError("bug"), InternalError, 500),
    ],
)
def test_translations(exc: Exception, cls: type[AppError], status: int) -> None:
    err = to_app_error(exc)
    assert type(err) is cls
    assert err.status_code == status


@pytest.mark.unit
def test_integrity_context_keeps_sqlstate_and_constraint() -> None:
    err = to_app_error(_integrity("23505"))
    assert err.context == {"sqlstate": "23505", "constraint": "uq_x"}


@pytest.mark.unit
def test_guard_adds_operation_ids_and_cause() -> None:
    cause = httpx.ConnectError("refused")
    with pytest.raises(UpstreamUnavailable) as info, guard("storage.stat", path="u/d.pdf"):
        raise cause
    assert info.value.operation == "storage.stat"
    assert info.value.context["path"] == "u/d.pdf"
    assert info.value.__cause__ is cause


@pytest.mark.unit
def test_guard_keeps_app_errors() -> None:
    with pytest.raises(NotFound) as info, guard("db.get_card", card_id="c1"):
        raise NotFound()
    assert info.value.operation == "db.get_card"
    assert info.value.context == {"card_id": "c1"}


@pytest.mark.unit
def test_every_code_is_documented_and_messages_are_plain() -> None:
    doc = errors_module.__doc__ or ""
    for code, cls in ERROR_CLASSES.items():
        assert f"``{code}``" in doc, code
        msg = cls.default_message
        assert msg.endswith((".", "!")), code
        for jargon in ("exception", "sql", "traceback", "null", "None"):
            assert jargon not in msg.lower().split(), (code, jargon)


# Envelope through a tiny app ------------------------------------------------------------------
class Body(BaseModel):
    title: str = Field(min_length=1)


def _app() -> FastAPI:
    test_app = FastAPI()
    install_error_handlers(test_app)
    test_app.add_middleware(RequestIdMiddleware, on_error=error_response)

    @test_app.get("/missing")
    async def missing() -> None:
        with guard("db.get_document", document_id="d1"):
            raise NoResultFound()

    @test_app.get("/crash")
    async def crash() -> None:
        raise RuntimeError("secret internals")

    @test_app.post("/validate")
    async def validate(body: Body) -> dict[str, Any]:
        return {}

    return test_app


async def _get(method: str, path: str, **kw: Any) -> httpx.Response:
    transport = httpx.ASGITransport(app=_app(), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        return await c.request(method, path, **kw)


@pytest.mark.unit
async def test_envelope_has_request_id_matching_header() -> None:
    resp = await _get("GET", "/missing")
    assert resp.status_code == 404
    body = resp.json()["error"]
    assert body["code"] == "not_found"
    assert body["request_id"] == resp.headers["x-request-id"]
    assert body["message"] == NotFound.default_message


@pytest.mark.unit
async def test_client_request_id_is_echoed_if_safe() -> None:
    resp = await _get("GET", "/missing", headers={"X-Request-ID": "client-req-12345"})
    assert resp.headers["x-request-id"] == "client-req-12345"
    assert resp.json()["error"]["request_id"] == "client-req-12345"
    unsafe = await _get("GET", "/missing", headers={"X-Request-ID": "<script>"})
    assert unsafe.headers["x-request-id"] != "<script>"


@pytest.mark.unit
async def test_unhandled_error_is_500_envelope_without_internals_in_message() -> None:
    resp = await _get("GET", "/crash")
    assert resp.status_code == 500
    body = resp.json()["error"]
    assert body["code"] == "internal_error"
    assert "secret internals" not in body["message"]
    assert body["request_id"] == resp.headers["x-request-id"]


@pytest.mark.unit
async def test_debug_only_outside_production(monkeypatch: pytest.MonkeyPatch) -> None:
    resp = await _get("GET", "/crash")
    assert resp.json()["error"]["debug"] == {
        "type": "builtins.RuntimeError",
        "message": "secret internals",
    }

    missing = await _get("GET", "/missing")
    assert missing.json()["error"]["debug"]["operation"] == "db.get_document"

    monkeypatch.setenv("APP_ENV", "production")
    get_settings.cache_clear()
    try:
        prod = await _get("GET", "/crash")
        assert "debug" not in prod.json()["error"]
    finally:
        monkeypatch.setenv("APP_ENV", "test")
        get_settings.cache_clear()


@pytest.mark.unit
async def test_validation_details_without_submitted_input() -> None:
    resp = await _get("POST", "/validate", json={"title": ""})
    assert resp.status_code == 422
    body = resp.json()["error"]
    assert body["code"] == "validation_error"
    assert body["details"][0]["loc"] == ["body", "title"]
    assert "input" not in body["details"][0]
    assert "debug" not in body  # the validation error's text would include the input


@pytest.mark.unit
async def test_unknown_route_and_method() -> None:
    assert (await _get("GET", "/nope")).json()["error"]["code"] == "not_found"
    assert (await _get("DELETE", "/missing")).json()["error"]["code"] == "method_not_allowed"


@pytest.mark.unit
def test_validation_details_sanitize_client_keys() -> None:
    from app.errors import UNKNOWN_FIELD, validation_details

    details = validation_details(
        [
            {"type": "extra_forbidden", "loc": ("body", "ok_name"), "msg": "x", "input": 1},
            {"type": "extra_forbidden", "loc": ("body", "bad key!"), "msg": "x", "input": 1},
            {"type": "int_parsing", "loc": ("body", "scores", "évil", "[key]"), "msg": "m"},
            {"type": "string_too_short", "loc": ("body", "title"), "msg": "too short"},
        ]
    )
    assert details[0].loc == ["body", "ok_name"]
    assert details[0].msg == "Unknown field. Remove it and try again."
    assert details[1].loc == ["body", UNKNOWN_FIELD]
    assert details[2].loc == ["body", "scores", UNKNOWN_FIELD, "[key]"]
    assert details[3].loc == ["body", "title"] and details[3].msg == "too short"
