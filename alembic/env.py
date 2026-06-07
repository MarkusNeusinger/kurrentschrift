"""Alembic environment — async migrations with DATABASE_URL / Cloud SQL fallback.

Adapted 1:1 from anyplot's `alembic/env.py`. Two run modes:
1. `DATABASE_URL` (local) → async asyncpg
2. `INSTANCE_CONNECTION_NAME` (CI / Cloud Run) → sync pg8000 via Cloud SQL Connector
"""

import asyncio
import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context


load_dotenv()

# Import models so Base.metadata is populated for autogenerate
from core.database import (  # noqa: E402, F401
    Aggregate,
    Base,
    Bbox,
    Hand,
    Instance,
    Source,
    Style,
    Template,
)


config = context.config

DATABASE_URL = os.getenv("DATABASE_URL", "")
INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME", "")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "kurrentschrift")

if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"}
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_with_cloud_sql() -> None:
    from google.cloud.sql.connector import Connector, IPTypes
    from sqlalchemy import create_engine

    connector = Connector()

    def get_conn():
        return connector.connect(
            INSTANCE_CONNECTION_NAME, "pg8000", user=DB_USER, password=DB_PASS, db=DB_NAME, ip_type=IPTypes.PUBLIC
        )

    cloud_engine = create_engine("postgresql+pg8000://", creator=get_conn, poolclass=pool.NullPool)
    try:
        with cloud_engine.connect() as connection:
            do_run_migrations(connection)
    finally:
        cloud_engine.dispose()
        connector.close()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await connectable.dispose()


def run_migrations_online() -> None:
    if INSTANCE_CONNECTION_NAME and not DATABASE_URL:
        run_migrations_with_cloud_sql()
    else:
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
