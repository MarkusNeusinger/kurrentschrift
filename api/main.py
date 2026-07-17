"""FastAPI entry point — lifespan-managed DB + router registration.

Load `.env` FIRST so all subsequent imports see DATABASE_URL etc.
"""

from dotenv import load_dotenv  # noqa: I001


load_dotenv()

import logging  # noqa: E402
import tomllib  # noqa: E402
from contextlib import asynccontextmanager  # noqa: E402
from pathlib import Path  # noqa: E402

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.middleware.gzip import GZipMiddleware  # noqa: E402

from api.routers import (  # noqa: E402
    bboxes_router,
    chart_router,
    hands_router,
    health_router,
    quiz_words_router,
    sources_router,
    styles_router,
    templates_router,
    write_router,
)
from core.config import settings  # noqa: E402
from core.database import close_db, init_db, is_db_configured  # noqa: E402


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _project_version() -> str:
    """The one version source: pyproject.toml (shipped in the image next to
    api/). The project is an uv workspace, not an installed distribution, so
    importlib.metadata has no record — read the file instead of keeping a
    second hardcoded string here that drifts (it sat at 0.2.0 for epochs)."""
    try:
        pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
        return str(tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"])
    except (OSError, KeyError, tomllib.TOMLDecodeError):  # pragma: no cover — packaging error, not runtime
        # A cosmetic version must never keep the API from starting, but a
        # missing/unparsable pyproject in the image is a packaging bug —
        # scream in the logs instead of failing silently.
        logger.exception("could not read project.version from pyproject.toml — check the image contents")
        return "0.0.0"


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
    version=_project_version(),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Geometry payloads (diagnostic ~15–22 KB, write batches) compress ~4–8×.
# GZip has no content-type filter, so admin chart/crop images get a useless
# recompress pass too — a few ms on rare admin loads, accepted for the public
# JSON win.
app.add_middleware(GZipMiddleware, minimum_size=1024)

app.include_router(health_router)
app.include_router(styles_router)
app.include_router(hands_router)
app.include_router(sources_router)
app.include_router(chart_router)
app.include_router(bboxes_router)
app.include_router(templates_router)
app.include_router(write_router)
app.include_router(quiz_words_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.port)
