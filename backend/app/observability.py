"""Request ids, structured JSON logs and Sentry (MDs/03-backend.md section 10).

Every request gets a request id: the client's ``X-Request-ID`` if it is a short safe token,
otherwise a new one. It is bound to the structlog context (so every log line of the request
carries it), returned in the ``X-Request-ID`` response header and put in every error body, so
an id a user reports leads straight to the log lines.

Logs never contain note text, card content or answers (section 9): ids, lengths, codes only.
"""

import logging
import re
import time
import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from typing import Any

import structlog
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import Settings

REQUEST_ID_HEADER = "X-Request-ID"
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

log = structlog.get_logger("app")


def current_request_id() -> str:
    """The id of the request being handled (a fresh one outside a request)."""
    rid = request_id_var.get()
    if rid is None:
        rid = new_request_id()
        request_id_var.set(rid)
    return rid


def new_request_id() -> str:
    return uuid.uuid4().hex


def configure_logging(settings: Settings) -> None:
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    if settings.sentry_dsn:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.app_env,
            send_default_pii=False,
            traces_sample_rate=0.0,
        )


ErrorResponder = Callable[[Request, Exception], Awaitable[Response]]


class RequestIdMiddleware:
    """Pure ASGI middleware: assigns the request id, logs one line per request, and turns any
    exception the inner handlers didn't handle into the error envelope (via ``on_error``)."""

    def __init__(self, app: ASGIApp, on_error: ErrorResponder) -> None:
        self.app = app
        self.on_error = on_error

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = _header(scope, REQUEST_ID_HEADER.lower())
        rid = incoming if incoming and _SAFE_REQUEST_ID.match(incoming) else new_request_id()
        token = request_id_var.set(rid)
        scope.setdefault("state", {})["request_id"] = rid
        structlog.contextvars.bind_contextvars(request_id=rid)
        started = time.perf_counter()
        status: dict[str, int] = {"code": 500}
        started_response = {"value": False}

        async def send_with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                started_response["value"] = True
                status["code"] = message["status"]
                headers = [
                    (k, v) for k, v in message.get("headers", []) if k.lower() != b"x-request-id"
                ]
                headers.append((b"x-request-id", rid.encode()))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        except Exception as exc:
            if started_response["value"]:
                raise  # too late to send an error body
            response = await self.on_error(Request(scope, receive), exc)
            await response(scope, receive, send_with_id)
        finally:
            log.info(
                "request",
                method=scope.get("method"),
                path=scope.get("path"),
                status=status["code"],
                duration_ms=round((time.perf_counter() - started) * 1000, 1),
            )
            structlog.contextvars.unbind_contextvars("request_id", "user_id")
            request_id_var.reset(token)


def bind_user(user_id: str) -> None:
    """Add the authenticated user id to every later log line of this request."""
    structlog.contextvars.bind_contextvars(user_id=user_id)


def _header(scope: Scope, name: str) -> str | None:
    for key, value in scope.get("headers", []):
        if key.decode("latin-1").lower() == name:
            decoded: str = value.decode("latin-1")
            return decoded
    return None


def log_fields(**fields: Any) -> dict[str, Any]:
    """Drop ``None`` values so log lines stay compact."""
    return {k: v for k, v in fields.items() if v is not None}
