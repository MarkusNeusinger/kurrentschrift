"""Shared-secret gate that closes the direct `*.run.app` door.

Both Cloud Run services stand with `ingress=all` — there is no load balancer,
and putting one in front would cost more per month than the whole project. So
the service answers on two addresses: `https://api.kurrentschrift.ink`, which
is proxied by Cloudflare, and the raw `*.run.app` URL, which is not. Everything
Cloudflare enforces — the rate-limiting rule, the WAF, the cache — is one URL
away from being bypassed, and the audit of 2026-09-02 measured exactly that:
the `run.app` address answered without a single `cf-` header.

A Cloudflare Transform Rule stamps `X-Origin-Secret: <secret>` onto every
request it proxies for `api.kurrentschrift.ink`. This middleware requires that
header, so a caller who skips the edge is refused with 403 before the request
costs anything. It is not authentication — it says "you came through the front
door", nothing about who you are; `api/auth.py` still decides what a caller may
do.

**The check is OFF unless `ORIGIN_SECRET` is set.** That is the whole rollback
story: unset the environment variable on the Cloud Run service and the gate
disappears without a deploy. Local development and the test suite therefore
never see it, and the rollout can put the code in production long before the
rule and the secret exist (see the checklist in the PR of `origin-secret-gate`).

Exempt by path, and only these two:

* `/health` — the deploy's pre-traffic smoke and any uptime probe reach the
  candidate revision on its `run.app` tag URL, which by definition never passes
  the edge. Gating it would make every deploy fail closed.
* `/seo-proxy/…` — belt and braces. The site's nginx fetches the prerendered
  pages over `https://api.kurrentschrift.ink` (`app/nginx.conf` `@seo_proxy`),
  so they DO pass the edge and DO carry the header; the exemption exists
  because the cost of being wrong there is every crawler seeing a 403, and the
  path is a static file read with no DB and no reserved data behind it.

`OPTIONS` never reaches the gate in the shipped stack — `CORSMiddleware` sits
outside it and answers a preflight itself — but it is let through explicitly
anyway: a browser cannot attach a custom header to a preflight, so a gate that
refused one would break every cross-origin call on the site rather than
protecting anything.

**Break-glass changes shape.** `X-Admin-Token` was documented as the way in
over the direct `run.app` URL when Cloudflare Access is unavailable
(`api/auth.py`). With the gate on, that call needs BOTH headers — the admin
token and the origin secret, both readable from Secret Manager by whoever is
holding the glass. Documented in `docs/reference/frontend-stack.md`.
"""

from __future__ import annotations

import secrets

from fastapi import Request
from fastapi.responses import JSONResponse

from api.http import NO_STORE
from core.config import settings


ORIGIN_SECRET_HEADER = "x-origin-secret"

# Same shape as the rate limiter's exemptions, and for overlapping reasons —
# see the module docstring for what each one buys. The `/seo-proxy` prefix
# keeps its slash so it cannot also swallow a future `/seo-proxy-admin`.
EXEMPT_PATHS = frozenset({"/health", "/seo-proxy"})
EXEMPT_PREFIXES = ("/seo-proxy/",)


def gate_is_armed() -> bool:
    """Whether a secret is configured at all. Read per call, not at import —
    the tests flip the setting and expect the next request to notice."""
    return bool(settings.origin_secret)


def is_exempt(path: str, method: str) -> bool:
    """Paths and methods the gate never refuses."""
    if method == "OPTIONS":
        return True
    return path in EXEMPT_PATHS or path.startswith(EXEMPT_PREFIXES)


def header_verdict(request: Request) -> str:
    """What the gate makes of this request. Five values, in two groups:

    * armed — `ok` · `missing` · `mismatch`
    * not armed — `off` (no header arrived) · `off-seen` (one did)

    `off-seen` is the one that makes the rollout safe rather than brave. The
    riskiest unknown is whether a path that is not a plain browser request
    carries the header at all — above all the admin route, where the apex
    `/api/*` reaches this service through a Cloudflare Worker, and a Worker
    subrequest is not obviously subject to the same zone's Transform Rules. So
    the order is: put the rule live while the gate is still off, then ask each
    path in turn — the `api.` host, the apex behind Cloudflare Access, the
    site's nginx, the raw `run.app` — and only arm the gate once every path
    that must keep working answers `off-seen`. Collapsing that into a bare
    `off` would have made the switch a leap.

    It reports the verdict, never the value, and tells a caller on `run.app`
    only what it already knows about its own request.
    """
    presented = request.headers.get(ORIGIN_SECRET_HEADER)
    if not gate_is_armed():
        return "off-seen" if presented else "off"
    if not presented:
        return "missing"
    return "ok" if secrets.compare_digest(presented, settings.origin_secret or "") else "mismatch"


class OriginSecretMiddleware:
    """Require the edge's shared header on every request that is not exempt.

    Placed (`api/main.py`) INSIDE `CORSMiddleware`, so a 403 still carries the
    CORS headers a browser needs to read it as a 403 rather than as an opaque
    network error, and OUTSIDE the rate limiter, so a request that never came
    through the edge is refused before it spends anyone's token.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not gate_is_armed() or is_exempt(scope["path"], scope["method"]):
            await self.app(scope, receive, send)
            return
        presented = Request(scope).headers.get(ORIGIN_SECRET_HEADER)
        # compare_digest needs two str: an absent header is not a mismatch to
        # measure, it is simply the wrong door.
        if presented and secrets.compare_digest(presented, settings.origin_secret or ""):
            await self.app(scope, receive, send)
            return
        response = JSONResponse(
            {"detail": "this API is reached through https://api.kurrentschrift.ink"},
            status_code=403,
            headers={"Cache-Control": NO_STORE},
        )
        await response(scope, receive, send)
