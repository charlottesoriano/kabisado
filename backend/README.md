# Kabisado backend

FastAPI API + Procrastinate worker. Specs live in `../MDs/` (03-backend.md is the main one).

```
uv sync                                   # install deps (Python 3.12, uv-managed)
uv run uvicorn app.main:app --reload      # API on http://127.0.0.1:8000 (/health, /docs)
uv run pytest                             # tests
uv run ruff check . && uv run mypy app    # lint / type-check
uv run alembic upgrade head               # migrations (needs DATABASE_URL)
```

Copy `.env.example` to `.env` and fill in values. Never commit `.env`.
