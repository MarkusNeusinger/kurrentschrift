"""Three response headers on everything this API answers.

The site's nginx carries its own set (`app/security-headers.conf`), but that
file governs `kurrentschrift.ink` only. `api.kurrentschrift.ink` is a second
public host with its own responses — the `/write` renders, the SVG assets
`llms.txt` advertises, the crop images, `/docs` — and the audit of 2026-09-02
measured it answering with none (finding 6).

**Three headers, deliberately, not six.**

* `X-Content-Type-Options: nosniff` — this host hands out SVG, JSON and PNG to
  callers that are frequently not browsers. Content sniffing is how a payload
  served as one type gets executed as another.
* `Referrer-Policy: strict-origin-when-cross-origin` — the same value the site
  uses, so a link out of an API-served page cannot leak a full path.
* `Strict-Transport-Security` — the same 180 days without `includeSubDomains`
  and without `preload` the author approved for the apex. It has to be repeated
  here precisely BECAUSE that decision left `includeSubDomains` off: HSTS is
  keyed to the hostname of the response that carried it, so the apex's header
  says nothing about this host, sibling or not, and Cloudflare terminating TLS
  for both names does not change that (Copilot review, PR #497). `app/nginx.conf`
  hides this copy on the crawler proxy, where the site sets its own.

The other three are left off on purpose:

* **No CSP.** `/docs` and `/redoc` are Swagger UI and ReDoc, which load their
  bundles from `cdn.jsdelivr.net` and run inline scripts. A policy strict
  enough to be worth setting would break the API's own documentation; a policy
  loose enough to keep it working would say nothing. The reserved data behind
  this host is protected by `api/auth.py`, not by a CSP.
* **No X-Frame-Options / frame-ancestors.** Nothing on this host is a page
  worth framing, and the site's own shell already refuses.

An ASGI middleware rather than `@app.middleware("http")`: it only rewrites the
header list of `http.response.start`, so it costs no request/response object,
and it sits high enough in the stack (`api/main.py`) that a refusal from the
origin gate or the rate limiter carries the headers too.

**One response never passes through here, and it is handled next door.**
Starlette builds `ServerErrorMiddleware` OUTSIDE every user middleware, so the
500 it writes for an unhandled exception is already on the wire before this
layer would see it. `api/main.py` therefore registers an `Exception` handler,
which is the response that middleware sends — and stamps `SECURITY_HEADERS`
onto it there (Copilot review, PR #497).
"""

from __future__ import annotations


# Lowercase, because ASGI header names are byte strings and compared as such.
SECURITY_HEADERS: tuple[tuple[bytes, bytes], ...] = (
    (b"x-content-type-options", b"nosniff"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (b"strict-transport-security", b"max-age=15552000"),
)

# The same pairs as `str`, for the places that build a `Response` rather than an
# ASGI message — one source, two shapes, so they cannot drift apart.
SECURITY_HEADERS_STR: dict[str, str] = {name.decode(): value.decode() for name, value in SECURITY_HEADERS}


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
