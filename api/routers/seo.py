"""Machine-facing surface of the API host: `robots.txt` and the crawler pages.

Same slot as `api/routers/seo.py` in the sister project anyplot. The SITE's
crawler policy is the static `app/public/robots.txt` with its doctrine in
docs/reference/crawler-richtlinie.md; this module states the policy of
`api.kurrentschrift.ink` (the host llms.txt advertises as the machine
interface: /docs, /openapi.json, the /write renders) and serves the pages a
mapped crawler gets instead of the SPA shell.

`/seo-proxy/{route}` — the prerendered page of a public route. The site's
nginx (app/nginx.conf, `$is_bot` map shared verbatim with anyplot) proxies a
crawler user agent here; the files were rendered at BUILD time from the locale
catalogue (app/src/lib/seo/prerender.ts → app/prerender/, committed and
shipped in this image by api/Dockerfile), so this handler is a file lookup,
never a render: no DB, no template engine, nothing a crawler can make
expensive. Unknown routes get the prerendered 404 (noindex) with status 404 —
a soft-404 with status 200 is exactly what the SPA shell used to hand out.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from api.http import CACHE_CONTROL, NO_STORE
from core.config import settings


logger = logging.getLogger(__name__)

router = APIRouter(tags=["seo"])

# Nothing on this host is off-limits by robots rule — a robots line protects
# nothing and only stops the compliant assistants that llms.txt invites (the
# lesson anyplot's AI-access audit of 2026-08-19 drew from its old blanket
# Disallow). Everything reserved — the authored templates, the occurrences,
# the bboxes, the hands, the own-hand strips — is gated by AUTHENTICATION
# (`require_admin`), so a crawler gets 401 there whatever this file says.
#
# The one signal that differs from the site's robots.txt: `ai-train=no`. The
# composed geometry the public /write endpoints return is derived from the
# reserved dataset — it is product surface to retrieve and cite, not training
# material (README "License", docs/reference/quellen-und-rechte.md §5). The
# site's own text is open to training; this host's payloads are not.
ROBOTS_TXT = (
    "# api.kurrentschrift.ink — the open read API of kurrentschrift.ink.\n"
    "# Reserved data is gated by authentication, not by this file; the public\n"
    "# /write renders derive from that data and stay out of model training.\n"
    "# Machine guide with every retrieval path and full example URLs:\n"
    "# https://kurrentschrift.ink/llms.txt — OpenAPI: /openapi.json\n"
    "User-agent: *\n"
    "Content-Signal: search=yes,ai-input=yes,ai-train=no\n"
    "Allow: /\n"
)


@router.get("/robots.txt", include_in_schema=False)
async def get_robots() -> Response:
    return Response(
        content=ROBOTS_TXT, media_type="text/plain; charset=utf-8", headers={"Cache-Control": CACHE_CONTROL}
    )


@router.get("/llms.txt", include_in_schema=False)
async def get_llms_txt() -> Response:
    """Redirect to the site's machine guide.

    The guide lives on the site host (app/public/llms.txt, one source of
    truth), but agents that land on this host — the README and both robots.txt
    name it — guess /llms.txt here too. A redirect beats a 404 and beats a
    served copy that would drift."""
    return RedirectResponse(
        "https://kurrentschrift.ink/llms.txt", status_code=302, headers={"Cache-Control": CACHE_CONTROL}
    )


# ---------------------------------------------------------------- crawler pages

# A public route is lowercase path segments — nothing else reaches the disk.
# Dots are excluded deliberately: no `..`, and no `/schriftkunde.html` alias
# of a page that would be a self-made duplicate URL.
_ROUTE_RE = re.compile(r"^[a-z0-9-]+(/[a-z0-9-]+)*$")
_INDEX = "index"
_NOT_FOUND = "404"

_FALLBACK_404 = (
    '<!DOCTYPE html><html lang="de"><head><meta charset="utf-8">'
    '<meta name="robots" content="noindex,follow"><title>Seite nicht gefunden</title></head>'
    "<body><h1>Seite nicht gefunden</h1></body></html>"
)


@lru_cache(maxsize=64)
def _page(name: str) -> str | None:
    """The prerendered file for a route name, read once per process.

    The files change only with a deploy (a new image, a new process), so a
    cache without invalidation is exactly right; the bound keeps a scan of
    invented routes from growing it (each miss caches a None)."""
    path: Path = settings.prerender_dir / f"{name}.html"
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def _not_found() -> HTMLResponse:
    body = _page(_NOT_FOUND)
    if body is None:
        # The prerender directory is missing altogether (a dev checkout before
        # `npm run prerender`, or a broken image) — say so once per process,
        # answer a minimal noindex 404 so the crawler still gets the right
        # status.
        logger.warning("prerender directory has no 404 page: %s", settings.prerender_dir)
        body = _FALLBACK_404
    return HTMLResponse(body, status_code=404, headers={"Cache-Control": NO_STORE})


@router.get("/seo-proxy/", include_in_schema=False)
@router.get("/seo-proxy/{route:path}", include_in_schema=False)
async def seo_proxy(route: str = "") -> HTMLResponse:
    """The prerendered page of a public route, or the prerendered 404."""
    raw = route.strip("/")
    # Only the EMPTY route is the home page. The two file names that are not
    # routes (`index`, `404`) must not become pages of their own — a 200 on
    # /seo-proxy/index would be a duplicate of the home page, a 200 on
    # /seo-proxy/404 an indexable copy of the error page.
    if raw in (_INDEX, _NOT_FOUND) or (raw and not _ROUTE_RE.match(raw)):
        return _not_found()
    body = _page(raw or _INDEX)
    if body is None:
        return _not_found()
    # Never edge-cached: Cloudflare caches this host's responses by rule, and
    # a cached page never reaches the middleware that counts the read
    # (api/analytics.py) — verified 2026-08-28: `cf-cache-status: HIT` and a
    # single bot_fetch for twenty crawler requests. The page is an 8 KB file
    # lookup; a crawler paying the API round trip is the price of the count.
    return HTMLResponse(body, headers={"Cache-Control": NO_STORE})
