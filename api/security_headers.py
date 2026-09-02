"""Two response headers on everything this API answers.

The site's nginx carries six of them (`app/security-headers.conf`), but that
file governs `kurrentschrift.ink` only. `api.kurrentschrift.ink` is a second
public host with its own responses — the `/write` renders, the SVG assets
`llms.txt` advertises, the crop images, `/docs` — and the audit of 2026-09-02
measured it answering with none (finding 6).

**Two headers, deliberately, not six.**

* `X-Content-Type-Options: nosniff` — this host hands out SVG, JSON and PNG to
  callers that are frequently not browsers. Content sniffing is how a payload
  served as one type gets executed as another.
* `Referrer-Policy: strict-origin-when-cross-origin` — the same value the site
  uses, so a link out of an API-served page cannot leak a full path.

The other four are left off on purpose:

* **No CSP.** `/docs` and `/redoc` are Swagger UI and ReDoc, which load their
  bundles from `cdn.jsdelivr.net` and run inline scripts. A policy strict
  enough to be worth setting would break the API's own documentation; a policy
  loose enough to keep it working would say nothing. The reserved data behind
  this host is protected by `api/auth.py`, not by a CSP.
* **No HSTS.** It belongs to the host that terminates TLS for browsers, and
  Cloudflare fronts both names; adding a second, differently-scoped copy here
  buys nothing and makes the policy two-headed.
* **No X-Frame-Options / frame-ancestors.** Nothing on this host is a page
  worth framing, and the site's own shell already refuses.

An ASGI middleware rather than `@app.middleware("http")`: it only rewrites the
header list of `http.response.start`, so it costs no request/response object,
and it sits high enough in the stack (`api/main.py`) that a refusal from the
origin gate or the rate limiter carries the headers too.
"""

from __future__ import annotations


# Lowercase, because ASGI header names are byte strings and compared as such.
SECURITY_HEADERS: tuple[tuple[bytes, bytes], ...] = (
    (b"x-content-type-options", b"nosniff"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
)


class SecurityHeadersMiddleware:
    """Add `SECURITY_HEADERS` to every HTTP response that lacks them."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                # A route that sets one itself keeps its value — a duplicate
                # header is worse than the one already there, and this
                # middleware is a floor, not an override.
                present = {name.lower() for name, _ in headers}
                headers += [(name, value) for name, value in SECURITY_HEADERS if name not in present]
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_headers)
