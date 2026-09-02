"""Health + root endpoints."""

from fastapi import APIRouter, Request

from api.origin_gate import header_verdict
from api.version import APP_VERSION
from core.database import is_db_configured


router = APIRouter(tags=["health"])


@router.get("/")
async def root() -> dict:
    return {"name": "kurrentschrift admin API", "version": APP_VERSION, "docs": "/docs"}


@router.get("/health")
async def health(request: Request) -> dict:
    """Cloud Run's health probe — the deploy's version check, and the one place
    the origin gate can be observed.

    `version` is `pyproject.toml`'s, i.e. what the candidate revision was built
    from. The pre-traffic smoke in `api/cloudbuild.yaml` asserts it equals the
    version in the build's own checkout: without it a smoke passes happily
    against an image that is not the one this build produced.

    `origin_gate` reports what `api/origin_gate.py` makes of THIS request —
    `off` · `off-seen` · `ok` · `missing` · `mismatch`. `/health` is exempt from
    the gate, so the answer comes back on every route into the service: the
    `api.` host, the apex `/api/*` behind Cloudflare Access, the site's nginx,
    the raw `run.app`. That is what makes the rollout measurable instead of a
    leap: with the edge already stamping but the gate still off, every path that
    must keep working has to answer `off-seen` before the switch is thrown —
    which is how the admin route was caught still answering `off`, its Worker
    subrequest skipping the zone's Transform Rules (`infra/cloudflare/`). It
    reports the verdict, never the value, and tells a caller nothing about its
    own request it did not already know.
    """
    return {
        "status": "healthy",
        "database_configured": is_db_configured(),
        "version": APP_VERSION,
        "origin_gate": header_verdict(request),
    }
