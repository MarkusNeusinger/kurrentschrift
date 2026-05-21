"""Health and info endpoints."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse


router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    """Root endpoint — points to /docs and /health."""
    return {"message": "kurrentschrift admin API", "docs": "/docs", "health": "/health"}


@router.get("/health")
async def health_check():
    """Health check endpoint (Cloud Run readiness probe)."""
    return JSONResponse(content={"status": "healthy", "service": "kurrentschrift-api"}, status_code=200)
