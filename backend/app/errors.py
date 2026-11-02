"""Global error utility: one error type, one translation table, one response shape.

Every layer raises (or lets through) exceptions; this module turns them into a response that
both a student and a developer can use:

    {"error": {"code": "upload_missing",
               "message": "We couldn't find your uploaded file. Please upload it again.",
               "details": [...],            # optional, e.g. field errors on 422
               "request_id": "3f2a...",     # same as the X-Request-ID header and the log line
               "debug": {...}}}             # only when APP_ENV is not "production"

- ``message`` is written for the end user: plain words, no internals, and what to do next.
- ``code`` is stable; clients switch on it (MDs/04-frontend.md maps codes to friendly text).
- Developer context (exception type, chained cause, operation, resource ids, SQLSTATE,
  constraint name) goes to the structured log and Sentry, never into the response.
  ``debug`` (exception type and message) is added only outside production.
- No note text anywhere (03 section 9): validation details drop the submitted input, and the
  SQLAlchemy engine runs with ``hide_parameters=True``.

Use ``guard("storage.create_signed_upload_url", document_id=...)`` around calls to the database
or external services to attach the operation and ids to whatever goes wrong inside.

Error codes
-----------

| code                    | HTTP | when |
| ----------------------- | ---- | ---- |
| ``bad_request``         | 400  | Malformed request the other codes don't cover |
| ``invalid_signature``   | 400  | Clerk webhook whose Svix signature doesn't verify |
| ``card_not_in_attempt`` | 400  | Quiz answer for a card that isn't in the attempt (3c) |
| ``not_a_mistake``       | 400  | "Explain my mistake" on a correct answer (3f) |
| ``unauthenticated``     | 401  | Missing, expired or invalid session token |
| ``not_found``           | 404  | Unknown id, or a resource that belongs to another user |
| ``topic_not_found``     | 404  | Topic generation found no relevant notes (3f) |
| ``method_not_allowed``  | 405  | Wrong HTTP method for the path |
| ``conflict``            | 409  | Unique or foreign-key violation (e.g. a concurrent change) |
| ``upload_missing``      | 409  | ``/process`` before the PDF reached Storage |
| ``already_processing``  | 409  | Document already queued or generating |
| ``invalid_state``       | 409  | Action not allowed in the document's current state |
| ``already_answered``    | 409  | Question or problem instance already answered (3c/3e) |
| ``validation_error``    | 422  | Request body/query failed validation; ``details`` lists fields |
| ``invalid_file``        | 422  | Not a PDF (extension or magic bytes) |
| ``file_too_large``      | 422  | File over ``MAX_UPLOAD_MB`` |
| ``page_limit_exceeded`` | 422  | PDF over ``MAX_PDF_PAGES`` pages |
| ``not_editable``        | 422  | Card type can't be edited yet (problem templates until 3e) |
| ``no_quiz_questions``   | 422  | Deck has no MCQs (3c) |
| ``no_problems``         | 422  | Deck has no problem templates (3e) |
| ``upload_limit_reached``| 429  | Daily upload limit (``UPLOADS_PER_DAY``) |
| ``rate_limited``        | 429  | Per-user request rate limit; ``Retry-After`` header set |
| ``internal_error``      | 500  | Anything unexpected |
| ``upstream_error``      | 502  | An external service answered with an error |
| ``service_unavailable`` | 503  | Database unreachable or a service not configured |
| ``upstream_timeout``    | 503  | An external service timed out |
| ``upstream_unavailable``| 503  | An external service couldn't be reached |
| ``auth_unavailable``    | 503  | Clerk's signing keys couldn't be fetched |
| ``ai_unavailable``      | 503  | All AI providers failed (3f) |
| ``enqueue_failed``      | 503  | Deck saved but its generation job couldn't be queued; Retry |

Document ``error_code`` values (``documents.error_code``, shown with a failed deck):

| error_code              | set by | Retry allowed |
| ----------------------- | ------ | ------------- |
| ``page_limit_exceeded`` | ``/process`` (and the job, as a backstop) | no: upload a new file |
| ``invalid_file``        | the job, if the file can't be read as a PDF | no: upload a new file |
| ``enqueue_failed``      | process, pasted text or retry, when queueing fails | yes |
| ``scanned_pdf``         | the job | yes (it will fail again; paste the text instead) |
| ``encrypted_pdf``       | the job | yes (it will fail again) |
| ``no_study_content``    | the job | yes |
| ``ai_unavailable``      | the job | yes |

Request validation (422) on an authenticated route is reported only after the session token
has been checked: a request with a missing or invalid token gets 401 ``unauthenticated`` even
if its body or query is also invalid. Field ``details`` never contain submitted values, and a
client-supplied key name appears in ``loc`` only if it is a short safe identifier
(``^[A-Za-z_][A-Za-z0-9_]{0,63}$``); otherwise it is shown as ``<unknown field>``.

Lower-level failures are translated in ``to_app_error``:

- ``AppError`` -> itself
- ``RequestValidationError`` -> ``validation_error`` with field ``details``
- Starlette ``HTTPException`` -> by status (404 ``not_found``, 405 ``method_not_allowed``, ...)
- SQLAlchemy ``NoResultFound`` -> ``not_found``
- ``IntegrityError``: unique (23505) and foreign key (23503) -> 409 ``conflict``;
  check (23514) and not-null (23502) -> 422 ``validation_error``
- SQLAlchemy ``OperationalError``/``InterfaceError``, ``OSError`` -> 503 ``service_unavailable``
- ``httpx.TimeoutException``, ``TimeoutError`` -> 503 ``upstream_timeout``
- ``httpx.TransportError`` -> 503 ``upstream_unavailable``
- ``httpx.HTTPStatusError``, Supabase ``StorageApiError`` -> 502 ``upstream_error``
- anything else -> 500 ``internal_error``
"""

import re
import traceback
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any, ClassVar

import httpx
import structlog
from fastapi import FastAPI, Request
from fastapi.dependencies.models import Dependant
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field
from sqlalchemy.exc import (
    DBAPIError,
    IntegrityError,
    InterfaceError,
    NoResultFound,
    OperationalError,
)
from starlette.exceptions import HTTPException as StarletteHTTPException
from storage3.exceptions import StorageApiError

from app.config import get_settings
from app.observability import REQUEST_ID_HEADER, current_request_id

log = structlog.get_logger("app.errors")


# Response models (OpenAPI) ----------------------------------------------------------------------
class ErrorDetail(BaseModel):
    loc: list[str | int] | None = Field(
        default=None, description="Where the problem is, e.g. ['body', 'title']."
    )
    msg: str
    type: str | None = None


class ErrorDebug(BaseModel):
    """Only present outside production."""

    type: str
    message: str
    operation: str | None = None


class ErrorBody(BaseModel):
    code: str = Field(description="Stable machine-readable code; see the error code table.")
    message: str = Field(description="Plain-language message that can be shown to the user.")
    details: list[ErrorDetail] | None = None
    request_id: str = Field(description="Same as the X-Request-ID header; quote it in reports.")
    debug: ErrorDebug | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


_DESCRIPTIONS = {
    400: "Bad request",
    401: "Missing or invalid session token (`unauthenticated`)",
    404: "Not found, or not yours (`not_found`)",
    405: "Method not allowed",
    409: "Conflict with the current state",
    422: "Validation failed (`validation_error` with `details`, or a specific code)",
    429: "Too many requests (`rate_limited`, `upload_limit_reached`)",
    500: "Unexpected error (`internal_error`)",
    502: "An external service failed (`upstream_error`)",
    503: "A service is unavailable; try again shortly",
}


def error_responses(*statuses: int) -> dict[int | str, dict[str, Any]]:
    """``responses=`` for a route: typed error bodies for the given statuses (always + 500)."""
    codes = sorted({*statuses, 500})
    return {
        s: {"model": ErrorResponse, "description": _DESCRIPTIONS.get(s, "Error")} for s in codes
    }


# Error classes ----------------------------------------------------------------------------------
class AppError(Exception):
    """Base for every error the API returns. Subclasses fix ``code``/``status_code`` and a
    default user-facing ``message``; callers may pass a more specific message."""

    code: ClassVar[str] = "internal_error"
    status_code: ClassVar[int] = 500
    default_message: ClassVar[str] = (
        "Something went wrong on our side. Please try again; if it keeps happening, "
        "contact support with the request id."
    )

    def __init__(
        self,
        message: str | None = None,
        *,
        details: Sequence[ErrorDetail] | None = None,
        operation: str | None = None,
        context: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)
        self.details = list(details) if details else None
        self.operation = operation
        self.context = dict(context or {})
        self.headers = dict(headers or {})


class InternalError(AppError):
    pass


class BadRequest(AppError):
    code = "bad_request"
    status_code = 400
    default_message = "The request couldn't be understood. Please check it and try again."


class InvalidSignature(AppError):
    code = "invalid_signature"
    status_code = 400
    default_message = "The webhook signature is invalid."


class CardNotInAttempt(AppError):
    code = "card_not_in_attempt"
    status_code = 400
    default_message = "That question isn't part of this quiz."


class NotAMistake(AppError):
    code = "not_a_mistake"
    status_code = 400
    default_message = "That answer was correct, so there's no mistake to explain."


class Unauthenticated(AppError):
    code = "unauthenticated"
    status_code = 401
    default_message = "Your session has expired or is invalid. Please sign in again."


class NotFound(AppError):
    code = "not_found"
    status_code = 404
    default_message = "We couldn't find that. It may have been deleted."


class TopicNotFound(AppError):
    code = "topic_not_found"
    status_code = 404
    default_message = "We couldn't find that topic in your notes. Try different words."


class MethodNotAllowed(AppError):
    code = "method_not_allowed"
    status_code = 405
    default_message = "This action isn't supported here."


class Conflict(AppError):
    code = "conflict"
    status_code = 409
    default_message = "This changed while you were working on it. Refresh and try again."


class UploadMissing(AppError):
    code = "upload_missing"
    status_code = 409
    default_message = "We couldn't find your uploaded file. Please upload the PDF again."


class AlreadyProcessing(AppError):
    code = "already_processing"
    status_code = 409
    default_message = "This deck is already being generated. It will appear when it's ready."


class InvalidState(AppError):
    code = "invalid_state"
    status_code = 409
    default_message = "That isn't possible right now. Refresh the page and try again."


class AlreadyAnswered(AppError):
    code = "already_answered"
    status_code = 409
    default_message = "You've already answered this one."


class ValidationFailed(AppError):
    code = "validation_error"
    status_code = 422
    default_message = "Some of the information isn't valid. Please check the highlighted fields."


class InvalidFile(AppError):
    code = "invalid_file"
    status_code = 422
    default_message = "This file isn't a PDF. Please choose a PDF file."


class FileTooLarge(AppError):
    code = "file_too_large"
    status_code = 422
    default_message = "This PDF is too large. Please choose a smaller file."


class PageLimitExceeded(AppError):
    code = "page_limit_exceeded"
    status_code = 422
    default_message = "This PDF has too many pages. Split it into smaller parts and try again."


class NotEditable(AppError):
    code = "not_editable"
    status_code = 422
    default_message = "This kind of card can't be edited yet."


class NoQuizQuestions(AppError):
    code = "no_quiz_questions"
    status_code = 422
    default_message = "This deck has no quiz questions yet."


class NoProblems(AppError):
    code = "no_problems"
    status_code = 422
    default_message = "This deck has no practice problems yet."


class UploadLimitReached(AppError):
    code = "upload_limit_reached"
    status_code = 429
    default_message = "You've reached today's upload limit. You can add more notes tomorrow."


class RateLimited(AppError):
    code = "rate_limited"
    status_code = 429
    default_message = "You're going a little fast. Please wait a moment and try again."


class UpstreamError(AppError):
    code = "upstream_error"
    status_code = 502
    default_message = "A service we rely on had a problem. Please try again in a minute."


class ServiceUnavailable(AppError):
    code = "service_unavailable"
    status_code = 503
    default_message = "The service is temporarily unavailable. Please try again in a minute."


class UpstreamTimeout(AppError):
    code = "upstream_timeout"
    status_code = 503
    default_message = "A service we rely on is responding slowly. Please try again in a minute."


class UpstreamUnavailable(AppError):
    code = "upstream_unavailable"
    status_code = 503
    default_message = "We couldn't reach a service we rely on. Please try again in a minute."


class AuthUnavailable(AppError):
    code = "auth_unavailable"
    status_code = 503
    default_message = "We couldn't check your sign-in right now. Please try again in a minute."


class AiUnavailable(AppError):
    code = "ai_unavailable"
    status_code = 503
    default_message = "The AI service is busy right now. Please try again in a minute."


class EnqueueFailed(AppError):
    code = "enqueue_failed"
    status_code = 503
    default_message = (
        "Your deck was saved, but we couldn't start generating it. "
        "Please press Retry on the deck in a minute."
    )


def _all_subclasses(cls: type[AppError]) -> list[type[AppError]]:
    out: list[type[AppError]] = []
    for sub in cls.__subclasses__():
        out += [sub, *_all_subclasses(sub)]
    return out


_CLASSES: list[type[AppError]] = [AppError, *_all_subclasses(AppError)]
ERROR_CLASSES: dict[str, type[AppError]] = {c.code: c for c in _CLASSES if c is not InternalError}

_HTTP_STATUS_ERRORS: dict[int, type[AppError]] = {
    400: BadRequest,
    401: Unauthenticated,
    404: NotFound,
    405: MethodNotAllowed,
    409: Conflict,
    422: ValidationFailed,
    429: RateLimited,
}

# Translation ------------------------------------------------------------------------------------
_UNIQUE, _FOREIGN_KEY, _CHECK, _NOT_NULL = "23505", "23503", "23514", "23502"


def _sqlstate(exc: DBAPIError) -> str | None:
    for candidate in (exc.orig, getattr(exc.orig, "__cause__", None)):
        for attr in ("sqlstate", "pgcode"):
            value = getattr(candidate, attr, None)
            if isinstance(value, str):
                return value
    return None


def _constraint(exc: DBAPIError) -> str | None:
    for candidate in (exc.orig, getattr(exc.orig, "__cause__", None)):
        name = getattr(candidate, "constraint_name", None)
        if isinstance(name, str):
            return name
        diag = getattr(candidate, "diag", None)
        if diag is not None and isinstance(getattr(diag, "constraint_name", None), str):
            return str(diag.constraint_name)
    return None


SAFE_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
UNKNOWN_FIELD = "<unknown field>"
# Error types whose last ``loc`` element is a key the client chose (not one of our field names).
_CLIENT_KEY_ERRORS = {"extra_forbidden"}
_FRIENDLY_MESSAGES = {
    "extra_forbidden": "Unknown field. Remove it and try again.",
    "json_invalid": "The request body isn't valid JSON.",
}


def _safe_loc(loc: Sequence[Any], error_type: str | None) -> list[str | int]:
    parts: list[str | int] = [p if isinstance(p, int) else str(p) for p in loc]
    for i, part in enumerate(parts):
        client_key = (error_type in _CLIENT_KEY_ERRORS and i == len(parts) - 1) or (
            i + 1 < len(parts) and parts[i + 1] == "[key]"  # dict keys
        )
        if client_key and isinstance(part, str) and not SAFE_KEY.match(part):
            parts[i] = UNKNOWN_FIELD
    return parts


def validation_details(errors: Sequence[Any]) -> list[ErrorDetail]:
    """Field errors without the submitted input (it may be note text). Client-chosen key
    names are kept only when they are short safe identifiers."""
    out = []
    for e in errors:
        error_type = e.get("type")
        loc = _safe_loc(e.get("loc", ()), error_type)
        msg = _FRIENDLY_MESSAGES.get(error_type or "", str(e.get("msg", "")))
        out.append(ErrorDetail(loc=loc or None, msg=msg, type=error_type))
    return out


def to_app_error(exc: BaseException) -> AppError:
    """Map any exception to an ``AppError`` (see the table in the module docstring)."""
    if isinstance(exc, AppError):
        return exc
    if isinstance(exc, RequestValidationError):
        return ValidationFailed(details=validation_details(exc.errors()))
    if isinstance(exc, StarletteHTTPException):
        cls = _HTTP_STATUS_ERRORS.get(exc.status_code)
        if cls is None:
            cls = InternalError if exc.status_code >= 500 else BadRequest
        return cls(headers=dict(exc.headers or {}))
    if isinstance(exc, NoResultFound):
        return NotFound()
    if isinstance(exc, IntegrityError):
        state = _sqlstate(exc)
        ctx = {"sqlstate": state, "constraint": _constraint(exc)}
        if state in (_CHECK, _NOT_NULL):
            return ValidationFailed(context=ctx)
        return Conflict(context=ctx)
    if isinstance(exc, (OperationalError, InterfaceError)) or (
        isinstance(exc, DBAPIError) and exc.connection_invalidated
    ):
        return ServiceUnavailable(context={"sqlstate": _sqlstate(exc)})
    if isinstance(exc, httpx.TimeoutException | TimeoutError):
        return UpstreamTimeout()
    if isinstance(exc, httpx.TransportError):
        return UpstreamUnavailable()
    if isinstance(exc, httpx.HTTPStatusError):
        return UpstreamError(context={"upstream_status": exc.response.status_code})
    if isinstance(exc, StorageApiError):
        return UpstreamError(context={"upstream_status": exc.status, "upstream_code": exc.code})
    if isinstance(exc, OSError):  # e.g. database connection refused
        return ServiceUnavailable()
    return InternalError()


@contextmanager
def guard(operation: str, **ids: Any) -> Iterator[None]:
    """Attach ``operation`` and resource ids to any error raised inside, translated to an
    ``AppError`` with the original chained as its cause. Works around ``await`` calls too."""
    try:
        yield
    except AppError as err:
        err.operation = err.operation or operation
        err.context = {**ids, **err.context}
        raise
    except Exception as exc:
        translated = to_app_error(exc)
        translated.operation = operation
        translated.context = {**ids, **translated.context}
        raise translated from exc


# Response ---------------------------------------------------------------------------------------
def _origin(exc: BaseException) -> BaseException:
    """The exception that really happened: the cause of a translated error, if any."""
    if isinstance(exc, AppError) and exc.__cause__ is not None:
        return exc.__cause__
    return exc


def _type_name(exc: BaseException) -> str:
    cls = type(exc)
    return f"{cls.__module__}.{cls.__qualname__}"


def _cause_chain(exc: BaseException) -> list[str]:
    chain, seen, cur = [], set(), exc.__cause__ or exc.__context__
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        chain.append(_type_name(cur))
        cur = cur.__cause__ or cur.__context__
    return chain


def build_error_response(request: Request | None, exc: BaseException) -> JSONResponse:
    err = to_app_error(exc)
    origin = _origin(exc) if err is exc else exc
    state_rid = getattr(request.state, "request_id", None) if request is not None else None
    request_id = state_rid or current_request_id()

    fields = {
        "code": err.code,
        "status": err.status_code,
        "error_type": _type_name(origin),
        "cause_chain": _cause_chain(origin) or None,
        "operation": err.operation,
        "context": {k: v for k, v in err.context.items() if v is not None} or None,
        "path": request.url.path if request is not None else None,
    }
    fields = {k: v for k, v in fields.items() if v is not None}
    if err.status_code >= 500:
        log.error(
            "request_failed",
            **fields,
            traceback="".join(traceback.format_exception(origin)),
        )
        _report_to_sentry(origin, err, request_id)
    else:
        log.warning("request_rejected", **fields)

    body: dict[str, Any] = {"code": err.code, "message": err.message}
    if err.details:
        body["details"] = [d.model_dump(exclude_none=True) for d in err.details]
    body["request_id"] = request_id
    if not get_settings().is_production and not isinstance(origin, RequestValidationError):
        debug = {"type": _type_name(origin), "message": str(origin)[:1000]}
        if err.operation:
            debug["operation"] = err.operation
        body["debug"] = debug

    headers = {**err.headers, REQUEST_ID_HEADER: request_id}
    if err.status_code == 401:
        headers.setdefault("WWW-Authenticate", "Bearer")
    return JSONResponse(status_code=err.status_code, content={"error": body}, headers=headers)


def _requires_auth(dependant: Dependant) -> bool:
    from app.auth import current_user_id

    return dependant.call is current_user_id or any(
        _requires_auth(d) for d in dependant.dependencies
    )


async def _auth_error(request: Request) -> AppError | None:
    """For a request that failed validation on an authenticated route: the auth error it
    would have got, if any (the token is checked before the body or query is reported)."""
    route = request.scope.get("route")
    if not isinstance(route, APIRoute) or not _requires_auth(route.dependant):
        return None
    from app.auth import current_user_id

    try:
        await current_user_id(request)
    except AppError as err:
        return err
    return None


async def error_response(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, RequestValidationError):
        auth_error = await _auth_error(request)
        if auth_error is not None:
            return build_error_response(request, auth_error)
    return build_error_response(request, exc)


def _report_to_sentry(origin: BaseException, err: AppError, request_id: str) -> None:
    try:
        import sentry_sdk

        if sentry_sdk.get_client().is_active():
            with sentry_sdk.new_scope() as scope:
                scope.set_tag("error_code", err.code)
                scope.set_tag("request_id", request_id)
                if err.operation:
                    scope.set_tag("operation", err.operation)
                scope.set_context("resource", {k: str(v) for k, v in err.context.items()})
                sentry_sdk.capture_exception(origin)
    except Exception:  # pragma: no cover - reporting must never break the response
        log.warning("sentry_report_failed")


def install_error_handlers(app: FastAPI) -> None:
    """Errors raised inside routes/dependencies. Anything else is caught by the request-id
    middleware (``on_error=error_response``) so it gets the same envelope."""
    app.add_exception_handler(AppError, error_response)
    app.add_exception_handler(StarletteHTTPException, error_response)
    app.add_exception_handler(RequestValidationError, error_response)
