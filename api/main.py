"""FastAPI app for the kurrentschrift canonical-extraction admin tool.

Same scaffolding pattern as anyplot: lifespan context, CORS, router
registration. No DB, no auth in v1 — local dev only.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.settings import settings
from api.routers import bboxes_router, canonical_router, chart_router, health_router


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Sanity-check critical paths at startup and log them once."""
    logger.info("kurrentschrift admin API starting")
    logger.info("  chart_path    : %s (%s)", settings.chart_path, "ok" if settings.chart_path.exists() else "MISSING")
    logger.info("  bboxes_json   : %s (%s)", settings.bboxes_json, "ok" if settings.bboxes_json.exists() else "MISSING")
    logger.info("  canonical_dir : %s", settings.canonical_dir)
    yield
    logger.info("kurrentschrift admin API stopping")


app = FastAPI(
    title="kurrentschrift admin API",
    description="Canonical-extraction backend for the Loth 1866 chart and (later) own-hand strokes.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chart_router)
app.include_router(bboxes_router)
app.include_router(canonical_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
