"""Clerk session JWT verification dependency (MDs/03-backend.md section 9).

Verifies signature against Clerk's JWKS (fetched with httpx and cached, refetched once on an
unknown ``kid``), ``exp``/``nbf`` with a small clock-skew allowance, ``iss`` and ``azp``. The
user id is the token's ``sub`` and comes only from the token."""
