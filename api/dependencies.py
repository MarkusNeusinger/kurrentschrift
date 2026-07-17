"""FastAPI dependencies — DB session + source-by-id loader."""

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import Source, SourceRepository, db_init_failed, get_db, is_db_configured


async def require_db(db: AsyncSession | None = Depends(get_db)) -> AsyncSession:
    if db is None:
        # Distinguish "never configured" from "configured but broken" — telling
        # an operator to set DATABASE_URL when it IS set (and the connection
        # failed) sends them down the wrong path.
        if is_db_configured() or db_init_failed():
            detail = "Database initialisation failed — check the server logs for the connection error."
        else:
            detail = "Database not configured. Set DATABASE_URL or INSTANCE_CONNECTION_NAME."
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
    return db


async def require_source(source_id: str, db: AsyncSession = Depends(require_db)) -> Source:
    source = await SourceRepository(db).get(source_id)
    if source is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"source {source_id!r} not found")
    return source
