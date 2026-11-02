"""Clerk session JWT verification dependency (MDs/03-backend.md section 9).

Verifies signature against Clerk's JWKS (fetched with httpx and cached, refetched once on an
unknown ``kid``), ``exp``/``nbf`` with a small clock-skew allowance, ``iss`` and ``azp``. The
user id is the token's ``sub`` and comes only from the token.

Fails closed: without ``CLERK_ISSUER``, ``CLERK_JWKS_URL`` or ``CLERK_AUTHORIZED_PARTIES`` every
token is rejected. If Clerk's keys can't be fetched at all the answer is 503
``auth_unavailable`` (not 401, which would sign the user out for Clerk's outage).
"""

import asyncio
import time
from typing import Annotated, Any

import httpx
import jwt
from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Profile
from app.db.session import get_session
from app.errors import AuthUnavailable, Unauthenticated, guard
from app.observability import bind_user

ALGORITHMS = ["RS256"]


class JwksCache:
    """Clerk's public keys by ``kid``. Refreshed when stale; an unknown ``kid`` triggers one
    refetch (throttled by ``CLERK_JWKS_MIN_REFETCH_SECONDS``)."""

    def __init__(self) -> None:
        self._keys: dict[str, Any] = {}
        self._fetched_at: float | None = None
        self._lock = asyncio.Lock()

    def clear(self) -> None:
        self._keys = {}
        self._fetched_at = None

    async def _fetch(self) -> None:
        settings = get_settings()
        try:
            async with httpx.AsyncClient(timeout=settings.clerk_jwks_timeout_seconds) as client:
                resp = await client.get(settings.clerk_jwks_url)
                resp.raise_for_status()
                jwks = jwt.PyJWKSet.from_dict(resp.json())
        except Exception as exc:
            raise AuthUnavailable(operation="clerk.fetch_jwks") from exc
        self._keys = {k.key_id: k.key for k in jwks.keys if k.key_id}
        self._fetched_at = time.monotonic()

    async def get(self, kid: str) -> Any | None:
        settings = get_settings()
        async with self._lock:
            now = time.monotonic()
            fetched_now = False
            if (
                self._fetched_at is None
                or now - self._fetched_at > settings.clerk_jwks_cache_seconds
            ):
                await self._fetch()
                fetched_now = True
            if kid not in self._keys and not fetched_now and self._fetched_at is not None:
                if now - self._fetched_at >= settings.clerk_jwks_min_refetch_seconds:
                    await self._fetch()
            return self._keys.get(kid)


jwks_cache = JwksCache()


async def verify_token(token: str) -> str:
    """Return the Clerk user id (``sub``) of a valid session token, else raise 401."""
    settings = get_settings()
    parties = settings.authorized_parties
    if not (settings.clerk_issuer and settings.clerk_jwks_url and parties):
        raise Unauthenticated(
            operation="auth.verify_token", context={"reason": "auth_not_configured"}
        )
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise Unauthenticated(context={"reason": "malformed_token"}) from exc
    kid = header.get("kid")
    if header.get("alg") not in ALGORITHMS or not isinstance(kid, str):
        raise Unauthenticated(context={"reason": "unsupported_header"})
    key = await jwks_cache.get(kid)
    if key is None:
        raise Unauthenticated(context={"reason": "unknown_kid"})
    try:
        claims = jwt.decode(
            token,
            key=key,
            algorithms=ALGORITHMS,
            issuer=settings.clerk_issuer,
            leeway=settings.clerk_clock_skew_seconds,
            options={"require": ["exp", "iss", "sub"], "verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        raise Unauthenticated(context={"reason": type(exc).__name__}) from exc
    if claims.get("azp") not in parties:
        raise Unauthenticated(context={"reason": "unauthorized_party"})
    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub:
        raise Unauthenticated(context={"reason": "missing_sub"})
    return sub


async def current_user_id(request: Request) -> str:
    """Dependency: the verified Clerk user id. Every query is scoped to it."""
    auth = request.headers.get("authorization", "")
    scheme, _, token = auth.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise Unauthenticated(context={"reason": "missing_token"})
    user_id = await verify_token(token.strip())
    request.state.user_id = user_id
    bind_user(user_id)
    return user_id


CurrentUserId = Annotated[str, Depends(current_user_id)]


async def ensure_profile(session: AsyncSession, user_id: str) -> Profile:
    """Create the profile row if the Clerk webhook hasn't yet (part of the caller's
    transaction), and return it."""
    with guard("db.ensure_profile", user_id=user_id):
        await session.execute(insert(Profile).values(id=user_id).on_conflict_do_nothing())
        profile = (await session.execute(select(Profile).where(Profile.id == user_id))).scalar_one()
    return profile


async def current_profile(
    user_id: CurrentUserId, session: Annotated[AsyncSession, Depends(get_session)]
) -> Profile:
    """Dependency for endpoints that insert rows owned by the user (profile FK)."""
    return await ensure_profile(session, user_id)


CurrentProfile = Annotated[Profile, Depends(current_profile)]
