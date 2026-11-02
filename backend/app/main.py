"""FastAPI application: routers, middleware, error handlers.

Routers, CORS, the error envelope, request-id logging and Sentry are wired in during build step 1.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI
from fastapi.routing import APIRoute
from pydantic import BaseModel

from app.db.session import dispose_engine


def _operation_id(route: APIRoute) -> str:
    """Stable operationIds for the generated frontend client: the route function's name."""
    return route.name


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await dispose_engine()


app = FastAPI(
    title="Kabisado API",
    version="0.1.0",
    generate_unique_id_function=_operation_id,
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["account"])
async def health() -> HealthResponse:
    """Liveness check."""
    return HealthResponse()
