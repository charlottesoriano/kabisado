# Kabisado backend

FastAPI API + Procrastinate worker. Specs live in `../MDs/` (03-backend.md is the main one).

```
uv sync                                   # install deps (Python 3.12, uv-managed)
uv run uvicorn app.main:app --reload --loop asyncio:SelectorEventLoop   # API on http://127.0.0.1:8000 (/health, /docs)
# --loop: on Windows uvicorn defaults to the Proactor loop, which psycopg (job enqueue) can't use
uv run pytest                             # tests
uv run ruff check . && uv run mypy app    # lint / type-check
uv run alembic upgrade head               # migrations (needs DATABASE_URL)
```

Copy `.env.example` to `.env` and fill in values. Never commit `.env`.

## Database and migrations

Schema source of truth: `../MDs/05-database-schema.md`. The twelve tables live in the private
`app` schema with RLS enabled and no policies; `anon`/`authenticated` get no grants (the revokes
are skipped on plain Postgres, where those roles don't exist). Models: `app/db/models.py`;
migrations: `migrations/versions/` (sequential ids: `0001_initial_schema.py`, `0002_...`).

```
uv run alembic upgrade head               # apply (uses DATABASE_URL)
uv run alembic downgrade base             # drop the app tables (extensions and schema are kept)
DATABASE_URL=postgresql+asyncpg://u:p@localhost/db uv run alembic upgrade head --sql
                                          # print the SQL without connecting
```

Constraint names come from the naming convention in `app/db/base.py`; in migrations wrap
explicit names in `op.f(...)` so the convention isn't applied twice. Autogenerate only looks at
schema `app`.

## Integration tests (real Postgres)

Tests marked `integration` are skipped unless `TEST_DATABASE_URL` points at a **disposable**
Postgres with pgvector (the migration test downgrades to base, dropping every table in `app`).
Either form works: `postgresql://...` or `postgresql+asyncpg://...`.

Local Supabase (`supabase start`, needs the Supabase CLI and Docker):

```
TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres uv run pytest -m integration
```

Plain pgvector container (any pgvector image, e.g. `pgvector/pgvector:pg16`, on port 5432):

```
TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/postgres uv run pytest -m integration
```

In PowerShell set it first: `$env:TEST_DATABASE_URL = "postgresql://..."`.

## API (build step 3a: account, documents, cards)

```
uv run python -m app.export_openapi              # regenerate openapi.json (a test fails if stale)
uv run python -m app.services.storage --ensure-bucket
                                                 # create/update the private `uploads` bucket
                                                 # (PDF only, MAX_UPLOAD_MB) with the service key
```

- **Errors** always look like `{"error": {"code", "message", "details"?, "request_id", "debug"?}}`.
  The code table and the translation rules are in `app/errors.py`. `request_id` equals the
  `X-Request-ID` response header and the `request_id` field of the JSON log lines. `debug`
  (exception type and message) appears only when `APP_ENV` is not `production`, which is the
  default, so set `APP_ENV=local` in your `.env` for development only.
- **Job queue:** Procrastinate's tables live in the private `procrastinate` schema (migration
  `0002`, SQL vendored in `migrations/sql/`). Upgrading Procrastinate needs a new migration that
  applies its bundled migrations. Worker: `uv run procrastinate --app=app.jobs.app.app worker`.
- **Tests:** API tests use a real database (`TEST_DATABASE_URL`), fake Storage and job queue
  (`tests/fakes.py`), test-signed Clerk tokens (`tests/conftest.py::token_for`) and a mocked
  JWKS. The developer `.env` is never read by tests.
