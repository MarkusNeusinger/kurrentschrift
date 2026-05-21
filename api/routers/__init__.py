"""Routers exposed by the FastAPI service."""

from api.routers.bboxes import router as bboxes_router
from api.routers.chart import router as chart_router
from api.routers.glyphs import router as glyphs_router
from api.routers.health import router as health_router
from api.routers.sources import router as sources_router


__all__ = ["bboxes_router", "chart_router", "glyphs_router", "health_router", "sources_router"]
