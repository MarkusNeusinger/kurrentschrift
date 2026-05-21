"""Source CRUD (read-only in v1)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import require_db, require_source
from api.schemas import SourceOut
from core.database import Source, SourceRepository


router = APIRouter(prefix="/sources", tags=["sources"])


def _to_out(source: Source) -> SourceOut:
    return SourceOut(
        id=source.id,
        title=source.title,
        license=source.license,
        chart_path=source.chart_path,
        chart_size=source.chart_size,
        style_ratio=list(source.style_ratio),
        slant_deg=source.slant_deg,
        attribution=source.attribution,
    )


@router.get("", response_model=list[SourceOut])
async def list_sources(db: AsyncSession = Depends(require_db)) -> list[SourceOut]:
    rows = await SourceRepository(db).list()
    return [_to_out(s) for s in rows]


@router.get("/{source_id}", response_model=SourceOut)
async def get_source(source: Source = Depends(require_source)) -> SourceOut:
    return _to_out(source)
