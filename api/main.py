"""FastAPI entry point — lifespan-managed DB + router registration.

Load `.env` FIRST so all subsequent imports see DATABASE_URL etc.
"""

from dotenv import load_dotenv  # noqa: I001


load_dotenv()

import logging  # noqa: E402
from contextlib import asynccontextmanager  # noqa: E402

from fastapi import FastAPI, Request, Response  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.middleware.gzip import GZipMiddleware  # noqa: E402

from api.analytics import classify_asset, track_asset_fetch, track_bot_fetch  # noqa: E402
from api.origin_gate import OriginSecretMiddleware  # noqa: E402
from api.rate_limit import RateLimitMiddleware  # noqa: E402
from api.routers import (  # noqa: E402
    aggregates_router,
    bboxes_router,
    chart_router,
    eigenhand_router,
    hands_router,
    health_router,
    instances_router,
    lesarten_router,
    pair_aggregates_router,
    pairs_router,
    quiz_words_router,
    seo_router,
    sources_router,
    styles_router,
    templates_router,
    word_samples_router,
    work_items_router,
    work_items_session_router,
    write_router,
)
from api.version import APP_VERSION  # noqa: E402
from core.config import settings  # noqa: E402
from core.database import close_db, init_db, is_db_configured  # noqa: E402


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class HeadAsGetMiddleware:
    """Answer HEAD with the matching GET route's status and headers, no body.

    Taken from the sister project anyplot (`api/main.py`). FastAPI's
    `@router.get` registers GET-only routes — Starlette's plain `Route` would
    add HEAD itself — so every HEAD probe answered 405 across the whole API:
    link checkers, and the assistants that preflight a URL before fetching it.
    That hit the two SVG assets `llms.txt` advertises; they only looked healthy
    from outside because Cloudflare answers HEAD from a cached GET.

    An ASGI rewrite rather than adding HEAD to `route.methods`: the latter also
    emits a `head` operation per path into openapi.json and doubles the
    documented surface. Content-Length from the GET response is kept — that is
    what HEAD promises.

    Placement differs from anyplot's, deliberately: this app is wrapped as the
    INNERMOST user middleware, so the analytics middleware above it still sees
    the real `HEAD` and does not count a probe as a page read or an asset
    fetch. anyplot wraps outermost because it has no such counter.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "HEAD":
            await self.app(scope, receive, send)
            return
        scope = {**scope, "method": "GET"}

        # Body chunks are emptied but their `more_body` sequencing is kept —
        # forcing an early end while a streaming response keeps sending would
        # violate the ASGI message protocol.
        async def send_without_body(message):
            if message["type"] == "http.response.body":
                message = {**message, "body": b""}
            await send(message)

        await self.app(scope, receive, send_without_body)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("kurrentschrift API starting (env=%s)", settings.environment)
    if is_db_configured():
        try:
            await init_db()
            logger.info("Database connection initialised")
        except Exception:
            logger.exception("Failed to initialise database")
    else:
        logger.warning("No DATABASE_URL / INSTANCE_CONNECTION_NAME — running without DB")
    yield
    await close_db()
    logger.info("kurrentschrift API stopped")


app = FastAPI(
    title="kurrentschrift admin API",
    description="Canonical ductus-template extraction for normed pre-1900 German Kurrent script.",
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# The middleware stack, written innermost-first because `add_middleware`
# PREPENDS — the last one added is the outermost. Reading the calls below from
# the bottom up gives the order a request actually travels:
#
#   CORS → origin gate → bot counter → gzip → rate limit → HEAD-as-GET → router
#
# Every position in it is load-bearing:
#
# * CORS outermost, so a refusal from either gate still carries the headers a
#   browser needs to READ it as a 403/429 rather than as an opaque network
#   error — and so a preflight, which can never carry a custom header, is
#   answered before the origin gate sees it.
# * The origin gate directly inside CORS: a caller that never came through the
#   edge is refused before ANY of the work below runs. That includes the bot
#   counter — otherwise a direct caller with a crawler User-Agent would turn
#   each of its own refusals into an outbound Plausible request, unthrottled,
#   because the rate limiter sits further in (Copilot review, PR #493).
# * The rate limiter outside HeadAsGet, so a HEAD probe spends a token exactly
#   like the GET it stands for.
app.add_middleware(HeadAsGetMiddleware)
app.add_middleware(RateLimitMiddleware)
# Geometry payloads (diagnostic ~15–22 KB, write batches) compress ~4–8×.
# GZip has no content-type filter, so admin chart/crop images get a useless
# recompress pass too — a few ms on rare admin loads, accepted for the public
# JSON win.
# Level 6 over the default 9: large geometry JSON compresses ~2-3x faster for ~1-2% more bytes.
app.add_middleware(GZipMiddleware, minimum_size=1024, compresslevel=6)


# Record which AI or search agent requested which page. A middleware rather
# than a router dependency: a dependency runs BEFORE the handler and cannot
# see the response, so every 404 would be recorded as a successful read. The
# status matters — an assistant asking for a URL that does not exist is a
# signal worth keeping, it just is not a page view.
@app.middleware("http")
async def record_bot_fetch(request: Request, call_next):
    """Report crawler page requests (/seo-proxy) and single-asset fetches (a
    letter or word as image/JSON, a chart crop) to the bot site.

    Requests, not reads: the status is recorded rather than filtered on. The
    machine files (/robots.txt), the inventory and the batch reads are not
    recorded.
    """
    response: Response = await call_next(request)
    path = request.url.path
    if path.startswith("/seo-proxy"):
        # The public URL, never this router's internal prefix. A HEAD probe
        # (link checkers, crawlers before the GET) is answered but not counted
        # — it fetches no page, and counting it would double the read.
        if request.method == "GET":
            track_bot_fetch(request, path.removeprefix("/seo-proxy").rstrip("/") or "/", response.status_code)
        return response
    asset = classify_asset(path, request.query_params.get("text"))
    # Same rule as the page reads above: a HEAD probe fetches no bytes and is
    # not a read. It reaches a route at all only since HeadAsGetMiddleware, so
    # without this line the new 200s would inflate the asset counts.
    if asset is not None and request.method == "GET":
        kind, source, key = asset
        track_asset_fetch(request, asset=kind, source=source, key=key, status=response.status_code)
    return response


# The two outermost layers, registered AFTER the decorator above so they end up
# outside it — see the stack comment where the inner ones are added. Dormant
# until ORIGIN_SECRET is set; CORS wraps everything so every refusal stays
# readable in a browser.
app.add_middleware(OriginSecretMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health_router)
app.include_router(seo_router)
app.include_router(styles_router)
app.include_router(hands_router)
app.include_router(aggregates_router)
app.include_router(pair_aggregates_router)
app.include_router(sources_router)
app.include_router(chart_router)
app.include_router(bboxes_router)
app.include_router(templates_router)
app.include_router(pairs_router)
app.include_router(instances_router)
app.include_router(word_samples_router)
app.include_router(work_items_router)
app.include_router(work_items_session_router)
app.include_router(write_router)
app.include_router(quiz_words_router)
app.include_router(lesarten_router)
app.include_router(eigenhand_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.port)
