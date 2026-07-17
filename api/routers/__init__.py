"""Routers exposed by the FastAPI service."""

from api.routers.bboxes import router as bboxes_router
from api.routers.chart import router as chart_router
from api.routers.hands import router as hands_router
from api.routers.health import router as health_router
from api.routers.quiz_words import router as quiz_words_router
from api.routers.sources import router as sources_router
from api.routers.styles import router as styles_router
from api.routers.templates import router as templates_router
from api.routers.word_samples import router as word_samples_router
from api.routers.write import router as write_router


__all__ = [
    "bboxes_router",
    "chart_router",
    "hands_router",
    "health_router",
    "quiz_words_router",
    "sources_router",
    "styles_router",
    "templates_router",
    "word_samples_router",
    "write_router",
]
