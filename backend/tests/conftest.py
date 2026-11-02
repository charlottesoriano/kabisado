"""Shared fixtures. External services (JWKS, Svix, LiteLLM, Storage, Judge0) are always mocked.

Settings never come from the developer's ``backend/.env`` here: env-file loading is switched off
and every relevant variable is set to a test value before the app is imported.

Database-backed tests need ``TEST_DATABASE_URL`` (a disposable Postgres with pgvector, e.g. the
local Supabase). Migrations run once per session; each test runs in a transaction that is
rolled back (route ``commit()``s only release a savepoint).
"""

import os
import time
from collections.abc import AsyncIterator, Callable, Iterator
from typing import Any

import httpx
import jwt
import pytest
import respx
from alembic import command
from alembic.config import Config
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import BACKEND_DIR, Settings, get_settings
from app.jobs.app import _libpq_url, use_selector_loop_on_windows

JWKS_URL = "https://clerk.test/.well-known/jwks.json"
ISSUER = "https://clerk.test"
AZP = "http://localhost:3000"
WEBHOOK_SECRET = "whsec_" + "dGVzdC1zZWNyZXQtZm9yLWthYmlzYWRvLXdlYmhvb2tz"
KID = "test-kid"

Settings.model_config["env_file"] = None
os.environ.update(
    {
        "APP_ENV": "test",
        "DATABASE_URL": "",
        "WORKER_DATABASE_URL": "",
        "SUPABASE_URL": "",
        "SUPABASE_SERVICE_ROLE_KEY": "",
        "CLERK_SECRET_KEY": "",
        "CLERK_JWKS_URL": JWKS_URL,
        "CLERK_ISSUER": ISSUER,
        "CLERK_AUTHORIZED_PARTIES": AZP,
        "CLERK_WEBHOOK_SECRET": WEBHOOK_SECRET,
        "SENTRY_DSN": "",
    }
)
get_settings.cache_clear()
use_selector_loop_on_windows()

from app.auth import jwks_cache  # noqa: E402
from app.db.session import get_session  # noqa: E402
from app.jobs.queue import get_job_queue  # noqa: E402
from app.main import app  # noqa: E402
from app.services.ratelimit import limiter  # noqa: E402
from app.services.storage import get_storage  # noqa: E402
from tests.fakes import FakeQueue, FakeStorage  # noqa: E402

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "")
needs_db = pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL is not set")

PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def public_jwk(key: rsa.RSAPrivateKey = PRIVATE_KEY, kid: str = KID) -> dict[str, Any]:
    jwk: dict[str, Any] = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
    return {**jwk, "kid": kid, "use": "sig", "alg": "RS256"}


_UNSET: Any = object()


def token_for(
    user_id: str,
    *,
    exp: int | None = _UNSET,
    nbf: int | None = None,
    iss: str = ISSUER,
    azp: str | None = AZP,
    key: rsa.RSAPrivateKey = PRIVATE_KEY,
    kid: str = KID,
) -> str:
    """A Clerk-like session token. ``exp``/``nbf`` are absolute epoch seconds."""
    now = int(time.time())
    claims: dict[str, Any] = {"sub": user_id, "iss": iss, "iat": now - 1}
    claims["exp"] = now + 300 if exp is _UNSET else exp
    if claims["exp"] is None:
        del claims["exp"]
    if nbf is not None:
        claims["nbf"] = nbf
    if azp is not None:
        claims["azp"] = azp
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": kid})


def auth(user_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_for(user_id)}"}


def with_driver(url: str, driver: str) -> str:
    return f"postgresql+{driver}://" + _libpq_url(url).removeprefix("postgresql://")


@pytest.fixture(autouse=True)
def mock_http() -> Iterator[respx.MockRouter]:
    """All outgoing httpx calls are mocked; unmatched calls fail the test. Clerk's JWKS is
    served from the test key."""
    jwks_cache.clear()
    limiter.reset()
    with respx.mock(assert_all_called=False, assert_all_mocked=True) as router:
        router.get(JWKS_URL, name="jwks").mock(
            return_value=httpx.Response(200, json={"keys": [public_jwk()]})
        )
        yield router
    jwks_cache.clear()
    limiter.reset()
    app.dependency_overrides.clear()


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def alembic_config(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[[str], Config]]:
    """Build an Alembic config whose env.py sees ``url`` as DATABASE_URL.

    No ini file is passed, so env.py skips ``fileConfig`` and leaves pytest's logging alone.
    """

    def make(url: str) -> Config:
        monkeypatch.setenv("DATABASE_URL", url)
        get_settings.cache_clear()
        cfg = Config()
        cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
        return cfg

    yield make
    get_settings.cache_clear()


@pytest.fixture(scope="session")
def migrated_db() -> str:
    """Apply migrations once per session; returns the asyncpg URL."""
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL is not set")
    url = with_driver(TEST_DATABASE_URL, "asyncpg")
    previous = os.environ.get("DATABASE_URL", "")
    os.environ["DATABASE_URL"] = url
    get_settings.cache_clear()
    try:
        cfg = Config()
        cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
        command.upgrade(cfg, "head")
    finally:
        os.environ["DATABASE_URL"] = previous
        get_settings.cache_clear()
    return url


@pytest.fixture
async def db(migrated_db: str) -> AsyncIterator[AsyncSession]:
    """A session inside an outer transaction that is rolled back after the test."""
    engine = create_async_engine(migrated_db, poolclass=NullPool)
    async with engine.connect() as conn:
        outer = await conn.begin()
        session = AsyncSession(
            bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        try:
            yield session
        finally:
            await session.close()
            await outer.rollback()
    await engine.dispose()


@pytest.fixture
def storage() -> FakeStorage:
    return FakeStorage()


@pytest.fixture
def queue() -> FakeQueue:
    return FakeQueue()


@pytest.fixture
async def api(
    db: AsyncSession, storage: FakeStorage, queue: FakeQueue
) -> AsyncIterator[httpx.AsyncClient]:
    """Client wired to the test transaction, the fake storage and the fake job queue."""

    async def session_override() -> AsyncIterator[AsyncSession]:
        # Like production, where a failed request's session closes without committing.
        try:
            yield db
        except Exception:
            await db.rollback()
            raise

    app.dependency_overrides[get_session] = session_override
    app.dependency_overrides[get_storage] = lambda: storage
    app.dependency_overrides[get_job_queue] = lambda: queue
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
