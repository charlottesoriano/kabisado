"""FastAPI application: routers, middleware, error handlers.

Routers, CORS, the error envelope, request-id logging and Sentry are wired in during build step 1.
"""

from typing import Literal

from fastapi import FastAPI
from fastapi.routing import APIRoute
from pydantic import BaseModel


def _operation_id(route: APIRoute) -> str:
    """Stable operationIds for the generated frontend client: the route function's name."""
    return route.name


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


app = FastAPI(
    title="Kabisado API",
    version="0.1.0",
    generate_unique_id_function=_operation_id,
)


@app.get("/health", response_model=HealthResponse, tags=["account"])
async def health() -> HealthResponse:
    """Liveness check."""
    return HealthResponse()
