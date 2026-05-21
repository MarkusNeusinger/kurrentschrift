"""Health + root endpoints."""

from fastapi import APIRouter

from core.database import is_db_configured


router = APIRouter(tags=["health"])


@router.get("/")
async def root() -> dict:
    return {"name": "kurrentschrift admin API", "docs": "/docs"}


@router.get("/health")
async def health() -> dict:
    return {"status": "healthy", "database_configured": is_db_configured()}
