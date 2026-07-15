"""Async SQLAlchemy connection — supports DATABASE_URL (local) and Cloud SQL Connector (Cloud Run).

Adapted from anyplot's `core/database/connection.py`. Same dual-mode pattern:
prefer `DATABASE_URL` (asyncpg), fall back to the async Cloud SQL Connector
(asyncpg) if only `INSTANCE_CONNECTION_NAME` is set. Graceful no-op if neither
is configured.
"""

import asyncio
import logging
import os
import re
import threading
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool


logger = logging.getLogger(__name__)

INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "kurrentschrift")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

DEFAULT_POOL_SIZE = 5
DEFAULT_MAX_OVERFLOW = 10

engine = None
AsyncSessionLocal: async_sessionmaker | None = None
_connector = None

_async_init_lock: asyncio.Lock | None = None
_sync_init_lock = threading.Lock()


def _get_async_lock() -> asyncio.Lock:
    global _async_init_lock
    if _async_init_lock is None:
        _async_init_lock = asyncio.Lock()
    return _async_init_lock


class Base(DeclarativeBase):
    """Base for all SQLAlchemy models."""


def _normalize_db_url(url: str, target_driver: str) -> str:
    return re.sub(r"^postgres(?:ql)?(?:\+\w+)?://", f"postgresql+{target_driver}://", url)


async def _create_cloud_sql_engine():
    """Async engine using the async Cloud SQL Python Connector with asyncpg."""
    global _connector

    from google.cloud.sql.connector import IPTypes, create_async_connector

    _connector = await create_async_connector()

    async def get_conn():
        return await _connector.connect_async(
            INSTANCE_CONNECTION_NAME, "asyncpg", user=DB_USER, password=DB_PASS, db=DB_NAME, ip_type=IPTypes.PUBLIC
        )

    cloud_engine = create_async_engine(
        "postgresql+asyncpg://",
        async_creator=get_conn,
        pool_size=DEFAULT_POOL_SIZE,
        max_overflow=DEFAULT_MAX_OVERFLOW,
        pool_pre_ping=True,
        echo=ENVIRONMENT == "development",
    )

    logger.info("Created Cloud SQL async engine: %s (PUBLIC IP)", INSTANCE_CONNECTION_NAME)
    return cloud_engine


def _create_direct_engine():
    """Async engine using DATABASE_URL (asyncpg)."""
    url = _normalize_db_url(DATABASE_URL, "asyncpg")

    poolclass = NullPool if ENVIRONMENT == "test" else None
    engine_kwargs = {"echo": ENVIRONMENT == "development"}
    if poolclass:
        engine_kwargs["poolclass"] = poolclass
    else:
        engine_kwargs["pool_size"] = DEFAULT_POOL_SIZE
        engine_kwargs["max_overflow"] = DEFAULT_MAX_OVERFLOW
        engine_kwargs["pool_pre_ping"] = True

    direct_engine = create_async_engine(url, **engine_kwargs)
    safe_url = url.split("@")[-1] if "@" in url else "local"
    logger.info("Created direct async database engine: %s", safe_url)
    return direct_engine


async def init_db() -> None:
    """Initialise async engine + session factory. Idempotent."""
    global engine, AsyncSessionLocal

    if engine is not None:
        return

    if DATABASE_URL:
        engine = _create_direct_engine()
    elif INSTANCE_CONNECTION_NAME:
        engine = await _create_cloud_sql_engine()
    else:
        logger.warning("No database configuration found — running without database")
        return

    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def close_db() -> None:
    """Dispose engine + close connector. Idempotent."""
    global engine, AsyncSessionLocal, _connector

    if engine is not None:
        await engine.dispose()
        engine = None
        AsyncSessionLocal = None
        logger.info("Database engine disposed")

    if _connector is not None:
        await _connector.close_async()
        _connector = None
        logger.info("Cloud SQL connector closed")


async def get_db() -> AsyncGenerator[AsyncSession | None, None]:
    """FastAPI dependency. Yields a session, or None if DB is not configured
    or initialisation failed (require_db turns None into a clean 503)."""
    if engine is None:
        async with _get_async_lock():
            if engine is None:
                try:
                    await init_db()
                except Exception:
                    logger.exception("Database initialisation failed")

    if AsyncSessionLocal is None:
        yield None
        return

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for scripts."""
    if engine is None:
        async with _get_async_lock():
            if engine is None:
                await init_db()

    if AsyncSessionLocal is None:
        raise RuntimeError("Database not configured")

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def is_db_configured() -> bool:
    return bool(INSTANCE_CONNECTION_NAME or DATABASE_URL)
