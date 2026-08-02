"""Routers exposed by the FastAPI service."""

from api.routers.aggregates import pair_router as pair_aggregates_router
from api.routers.aggregates import router as aggregates_router
from api.routers.bboxes import router as bboxes_router
from api.routers.chart import router as chart_router
from api.routers.hands import router as hands_router
from api.routers.health import router as health_router
from api.routers.instances import router as instances_router
from api.routers.pairs import router as pairs_router
from api.routers.quiz_words import router as quiz_words_router
from api.routers.sources import router as sources_router
from api.routers.styles import router as styles_router
from api.routers.templates import router as templates_router
from api.routers.word_samples import router as word_samples_router
from api.routers.work_items import router as work_items_router
from api.routers.work_items import session_router as work_items_session_router
from api.routers.write import router as write_router


__all__ = [
    "aggregates_router",
    "bboxes_router",
    "chart_router",
    "hands_router",
    "health_router",
    "instances_router",
    "pair_aggregates_router",
    "pairs_router",
    "quiz_words_router",
    "sources_router",
    "styles_router",
    "templates_router",
    "word_samples_router",
    "work_items_router",
    "work_items_session_router",
    "write_router",
]
