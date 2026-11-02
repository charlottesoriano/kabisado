"""Write the API's OpenAPI schema to ``backend/openapi.json`` (the frontend client is generated
from it)::

    uv run python -m app.export_openapi

``tests/api/test_openapi.py`` fails when the committed file is stale.
"""

import json
from pathlib import Path
from typing import Any

from app.config import BACKEND_DIR

OPENAPI_PATH = BACKEND_DIR / "openapi.json"


def render(schema: dict[str, Any]) -> str:
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


def export(path: Path = OPENAPI_PATH) -> Path:
    from app.main import app

    path.write_text(render(app.openapi()), encoding="utf-8", newline="\n")
    return path


if __name__ == "__main__":
    print(f"Wrote {export()}")
