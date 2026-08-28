"""Admin auth — Cloudflare Access JWT verification + X-Admin-Token fallback.

Mirrors the pattern in ~/anyplot/api/routers/debug.py: Cloudflare Access
verifies a Google identity at the edge and forwards `Cf-Access-Jwt-Assertion`
to Cloud Run; we verify the JWT against the team's JWKS and check the email
against `ADMIN_ALLOWED_EMAILS`. `X-Admin-Token` is a shared-secret fallback
for CI, local dev, and break-glass access via the *.run.app direct URL.
"""

from __future__ import annotations

import secrets
from functools import lru_cache

import jwt as pyjwt
from fastapi import Header, HTTPException, Response, status

from api.http import NO_STORE
from core.config import settings


@lru_cache(maxsize=1)
def _jwks_client() -> pyjwt.PyJWKClient | None:
    if not settings.cf_access_team_domain:
        return None
    return pyjwt.PyJWKClient(f"https://{settings.cf_access_team_domain}/cdn-cgi/access/certs")


def _verify_cf_access_jwt(token: str) -> str | None:
    client = _jwks_client()
    if client is None or not settings.cf_access_aud:
        return None
    try:
        signing_key = client.get_signing_key_from_jwt(token)
        claims = pyjwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.cf_access_aud,
            issuer=f"https://{settings.cf_access_team_domain}",
        )
    except pyjwt.PyJWTError:
        return None
    email = claims.get("email")
    return email.lower() if isinstance(email, str) else None


def require_admin(
    response: Response,
    x_admin_token: str | None = Header(default=None),
    cf_access_jwt: str | None = Header(default=None, alias="Cf-Access-Jwt-Assertion"),
) -> None:
    """Gate admin endpoints — writes and the reserved-dataset reads — behind
    Cloudflare Access OR a shared secret.

    Without `settings.admin_token` AND without working Cloudflare Access config,
    every protected request gets 503 — a misconfigured prod deploy fails closed.

    The gate also stamps every gated response `Cache-Control: private,
    no-store` (api/http.py). A `public` directive on an authenticated answer is
    how a shared cache serves the admin's rows to the next anonymous request
    for the same URL, and a route that forgets the header is the likeliest way
    to get one — so the header lives in the one dependency every gated route
    already carries, not in each handler. (FastAPI merges the headers set here
    into the handler's response; a handler that returns a `Response` object
    directly bypasses that merge and sets its own — the eigenhand binaries do.)
    """
    response.headers["Cache-Control"] = NO_STORE
    if cf_access_jwt:
        email = _verify_cf_access_jwt(cf_access_jwt)
        if email and email in settings.admin_allowed_emails:
            return
        if email:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"User {email} not authorized")
        # Invalid JWT — fall through to the token path so a misconfigured edge
        # never strands the operator without break-glass access.

    expected = settings.admin_token
    if not expected:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Admin auth not configured")
    if not secrets.compare_digest(x_admin_token or "", expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")
