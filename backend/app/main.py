"""FastAPI application: routers, middleware, error handlers.

Middleware, outermost first: CORS (only the web app's origins), then request id + access log +
catch-all error envelope. Route errors go through the handlers in ``app.errors``.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from pydantic import BaseModel

from app import webhooks
from app.config import get_settings
from app.db.session import dispose_engine
from app.errors import error_response, install_error_handlers
from app.jobs.queue import close_job_queue
from app.observability import REQUEST_ID_HEADER, RequestIdMiddleware, configure_logging
from app.routers import cards, documents, me
from app.services.storage import close_storage


def _operation_id(route: APIRoute) -> str:
    """Stable operationIds for the generated frontend client: the route function's name."""
    return route.name


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await close_job_queue()
    await close_storage()
    await dispose_engine()


settings = get_settings()
configure_logging(settings)

app = FastAPI(
    title="Kabisado API",
    version="0.1.0",
    generate_unique_id_function=_operation_id,
    lifespan=lifespan,
)

install_error_handlers(app)
app.add_middleware(RequestIdMiddleware, on_error=error_response)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.authorized_parties,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", REQUEST_ID_HEADER],
    expose_headers=[REQUEST_ID_HEADER, "Retry-After"],
)


@app.get("/health", response_model=HealthResponse, tags=["account"])
async def health() -> HealthResponse:
    """Liveness check."""
    return HealthResponse()


app.include_router(me.router)
app.include_router(webhooks.router)
app.include_router(documents.router)
app.include_router(cards.router)
