"""API routers."""

from api.routers.bboxes import router as bboxes_router
from api.routers.canonical import router as canonical_router
from api.routers.chart import router as chart_router
from api.routers.health import router as health_router
from api.routers.render import router as render_router


__all__ = ["bboxes_router", "canonical_router", "chart_router", "health_router", "render_router"]
