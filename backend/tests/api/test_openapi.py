"""The OpenAPI schema the frontend client is generated from: fresh, stable, typed errors."""

import json

import pytest

from app.export_openapi import OPENAPI_PATH, render
from app.main import app

pytestmark = pytest.mark.api

EXPECTED_OPERATIONS = {
    ("get", "/health"): "health",
    ("get", "/me"): "get_me",
    ("patch", "/me"): "update_me",
    ("post", "/webhooks/clerk"): "clerk_webhook",
    ("post", "/documents"): "create_document",
    ("get", "/documents"): "list_documents",
    ("post", "/documents/text"): "create_text_document",
    ("post", "/documents/{document_id}/process"): "process_document",
    ("get", "/documents/{document_id}"): "get_document",
    ("patch", "/documents/{document_id}"): "rename_document",
    ("delete", "/documents/{document_id}"): "delete_document",
    ("post", "/documents/{document_id}/retry"): "retry_document",
    ("get", "/documents/{document_id}/chunks/{chunk_id}"): "get_chunk",
    ("get", "/documents/{document_id}/cards"): "list_cards",
    ("patch", "/cards/{card_id}"): "update_card",
    ("post", "/cards/{card_id}/flag"): "flag_card",
}


def test_committed_openapi_is_current() -> None:
    committed = OPENAPI_PATH.read_text(encoding="utf-8")
    assert json.loads(committed) == json.loads(render(app.openapi())), (
        "openapi.json is stale: run `uv run python -m app.export_openapi`"
    )


def test_operation_ids_are_the_function_names() -> None:
    schema = app.openapi()
    found = {
        (method, path): op["operationId"]
        for path, ops in schema["paths"].items()
        for method, op in ops.items()
    }
    assert found == EXPECTED_OPERATIONS


def test_errors_are_typed_and_fastapi_defaults_are_gone() -> None:
    schema = app.openapi()
    assert "HTTPValidationError" not in schema["components"]["schemas"]
    assert "ValidationError" not in schema["components"]["schemas"]
    for path, ops in schema["paths"].items():
        if path == "/health":
            continue
        for method, op in ops.items():
            errors = {s: r for s, r in op["responses"].items() if s.startswith(("4", "5"))}
            assert "500" in errors, (method, path)
            for status, resp in errors.items():
                ref = resp["content"]["application/json"]["schema"]["$ref"]
                assert ref.endswith("/ErrorResponse"), (method, path, status)
