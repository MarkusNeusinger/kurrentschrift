"""Style (Grundvorlage) endpoints — read-only list + get."""

from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import require_db
from api.schemas import StyleOut
from core.chart import resolve_chart_path
from core.database import Source, SourceRepository, Style, StyleRepository


router = APIRouter(prefix="/styles", tags=["styles"])


@lru_cache(maxsize=256)
def _chart_bytes_exist(chart_path: str) -> bool:
    """Filesystem stat of a chart's bytes, memoised per path. Chart sources ship
    with the deploy, so a path's existence is stable for the process lifetime —
    caching keeps the per-source `.exists()` off the hot `/styles` path."""
    return resolve_chart_path(chart_path).exists()


def _authorable(sources: list[Source]) -> bool:
    """A style is authorable once a teaching-chart source with bytes on disk exists."""
    return any(s.kind == "chart" and _chart_bytes_exist(s.chart_path) for s in sources)


def _to_out(style: Style, sources: list[Source]) -> StyleOut:
    return StyleOut(
        id=style.id,
        name=style.name,
        width_resolver=style.width_resolver,
        default_slant_deg=style.default_slant_deg,
        default_style_ratio=list(style.default_style_ratio),
        description=style.description,
        authorable=_authorable(sources),
    )


@router.get("", response_model=list[StyleOut])
async def list_styles(db: AsyncSession = Depends(require_db)) -> list[StyleOut]:
    styles = await StyleRepository(db).list()
    # One query for every source, grouped per style in Python — not a per-style
    # `source_repo.list(style_id=...)` round trip (mirrors sources.py's batching).
    by_style: dict[str, list[Source]] = {}
    for source in await SourceRepository(db).list():
        by_style.setdefault(source.style_id, []).append(source)
    return [_to_out(style, by_style.get(style.id, [])) for style in styles]


@router.get("/{style_id}", response_model=StyleOut)
async def get_style(style_id: str, db: AsyncSession = Depends(require_db)) -> StyleOut:
    style = await StyleRepository(db).get(style_id)
    if style is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"style {style_id!r} not found")
    sources = await SourceRepository(db).list(style_id=style_id)
    return _to_out(style, sources)
