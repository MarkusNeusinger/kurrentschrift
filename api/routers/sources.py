"""Source CRUD (read-only in v1) + the admin-gated resolved render context."""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db, require_source
from api.http import CACHE_CONTROL
from api.rendering import resolve_render_context
from api.schemas import PenOut, RenderContextOut, SourceOut
from core.database import Source, SourceRepository, Style, StyleRepository
from core.widths import PenStyle


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


def _pen_out(pen: PenStyle | None) -> PenOut | None:
    """Flatten a resolved `PenStyle` for the wire (nib fields inlined)."""
    if pen is None:
        return None
    nib = pen.nib
    return PenOut(
        kind=pen.kind,
        hairline_half=pen.hairline_half,
        nib_width_units=None if nib is None else nib.width_units,
        nib_angle_deg=None if nib is None else nib.angle_deg,
        nib_edge_fraction=None if nib is None else nib.edge_fraction,
    )


# Admin-gated for the same reason the single-template read is
# (quellen-und-rechte.md §5): the pooled nib/pen is measured geometry over the
# source's authored templates. No HTTP caching (unlike the public /write
# reads): the values come from the same api.rendering memoisation the /write
# path uses — explicitly invalidated on template writes, 10-minute TTL only as
# the safety net for out-of-band writes — so a fetch after an authoring change
# sees the new pool as soon as the API itself does.
@router.get("/{source_id}/render-context", response_model=RenderContextOut, dependencies=[Depends(require_admin)])
async def get_render_context(
    source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
) -> RenderContextOut:
    """The resolved render context of a source at full precision (admin only).

    Same resolution every `/write` request performs — lineature, width
    resolver, pooled nib/pen — but unrounded, so an offline renderer can
    reproduce a served payload bit-for-bit. See `RenderContextOut`.
    """
    ctx = await resolve_render_context(source, db)
    return RenderContextOut(
        style_id=ctx.style_id,
        style_ratio=ctx.style_ratio,
        slant_deg=ctx.slant_deg,
        width_resolver=ctx.width_resolver,
        constant_nib_units=ctx.nib,
        pen=_pen_out(ctx.pen),
    )
