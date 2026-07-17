"""Database package: connection + models + repositories."""

from core.database.connection import (
    AsyncSessionLocal,
    Base,
    close_db,
    db_init_failed,
    engine,
    get_db,
    get_db_context,
    init_db,
    is_db_configured,
)
from core.database.models import Aggregate, Bbox, Hand, Instance, QuizWord, Source, Style, Template
from core.database.repositories import (
    AggregateRepository,
    BboxRepository,
    HandRepository,
    InstanceRepository,
    QuizWordRepository,
    SourceRepository,
    StyleRepository,
    TemplateRepository,
)


__all__ = [
    "Aggregate",
    "AggregateRepository",
    "AsyncSessionLocal",
    "Base",
    "Bbox",
    "BboxRepository",
    "Hand",
    "HandRepository",
    "Instance",
    "InstanceRepository",
    "QuizWord",
    "QuizWordRepository",
    "Source",
    "SourceRepository",
    "Style",
    "StyleRepository",
    "Template",
    "TemplateRepository",
    "close_db",
    "db_init_failed",
    "engine",
    "get_db",
    "get_db_context",
    "init_db",
    "is_db_configured",
]
