"""Source CRUD (read-only in v1)."""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import require_db, require_source
from api.http import CACHE_CONTROL
from api.schemas import SourceOut
from core.database import Source, SourceRepository, Style, StyleRepository


router = APIRouter(prefix="/sources", tags=["sources"])


def _to_out(source: Source, style: Style | None) -> SourceOut:
    # Resolve the lineature ratio + slant: per-source override if set, else the
    # style default. Falls back to Kurrent-ish constants if the style is missing
    # (65 mirrors styles.default_slant_deg's server default — the literature
    # value for Kurrent um 1900, not a chart measurement).
    default_ratio = list(style.default_style_ratio) if style is not None else [2, 1, 2]
    default_slant = float(style.default_slant_deg) if style is not None else 65.0
    return SourceOut(
        id=source.id,
        style_id=source.style_id,
        hand_id=source.hand_id,
        kind=source.kind,
        title=source.title,
        license=source.license,
        chart_path=source.chart_path,
        chart_size=source.chart_size,
        style_ratio=list(source.style_ratio) if source.style_ratio is not None else default_ratio,
        slant_deg=float(source.slant_deg) if source.slant_deg is not None else default_slant,
        attribution=source.attribution,
        origin_url=source.origin_url,
        note=source.note,
    )


@router.get("", response_model=list[SourceOut])
async def list_sources(response: Response, db: AsyncSession = Depends(require_db)) -> list[SourceOut]:
    rows = await SourceRepository(db).list()
    style_repo = StyleRepository(db)
    styles = {s.id: s for s in await style_repo.list()}
    # Sources only change with a migration — cache like the render payloads.
    response.headers["Cache-Control"] = CACHE_CONTROL
    return [_to_out(s, styles.get(s.style_id)) for s in rows]


@router.get("/{source_id}", response_model=SourceOut)
async def get_source(
    response: Response, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
) -> SourceOut:
    style = await StyleRepository(db).get(source.style_id)
    response.headers["Cache-Control"] = CACHE_CONTROL
    return _to_out(source, style)
