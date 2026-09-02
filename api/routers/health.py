"""Health + root endpoints."""

from fastapi import APIRouter

from api.version import APP_VERSION
from core.database import is_db_configured


router = APIRouter(tags=["health"])


@router.get("/")
async def root() -> dict:
    return {"name": "kurrentschrift admin API", "version": APP_VERSION, "docs": "/docs"}


@router.get("/health")
async def health() -> dict:
    """Cloud Run's health probe — and the deploy's version check.

    `version` is `pyproject.toml`'s, i.e. what the candidate revision was built
    from. The pre-traffic smoke in `api/cloudbuild.yaml` asserts it equals the
    version in the build's own checkout: without it a smoke passes happily
    against an image that is not the one this build produced.
    """
    return {"status": "healthy", "database_configured": is_db_configured(), "version": APP_VERSION}
