"""Glyph (canonical) endpoints — trace, resample, list, get, delete, diagnostic."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db, require_source
from api.schemas import GlyphOut, GlyphSummary, ResampleRequest, TraceRequest
from core.database import BboxRepository, Glyph, GlyphRepository, Source
from core.fit import fit_glyph_to_crop
from core.pipeline import canonical_from_path, canonical_from_raw_path_only, diagnostic_for_glyph


router = APIRouter(prefix="/sources/{source_id}/glyphs", tags=["glyphs"])


def _bbox_to_dict(bbox) -> dict:
    return {
        "y0": bbox.y0,
        "y1": bbox.y1,
        "x0": bbox.x0,
        "x1": bbox.x1,
        "excludes": list(bbox.excludes),
        "baseline_y": bbox.baseline_y,
        "midband_y": bbox.midband_y,
        "n_anchors": bbox.n_anchors,
    }


def _glyph_to_out(g: Glyph) -> GlyphOut:
    return GlyphOut(
        glyph_key=g.glyph_key,
        glyph=g.glyph,
        position=g.position,
        variant=g.variant,
        advance=g.advance,
        entry=g.entry,
        exit_pt=g.exit_pt,
        anchors=g.anchors,
        half_widths=g.half_widths,
        raw_path=g.raw_path,
        trace_meta=g.trace_meta,
        measurements=g.measurements,
    )


@router.get("", response_model=list[GlyphSummary])
async def list_glyphs(source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)):
    rows = await GlyphRepository(db).list(source.id)
    return [
        GlyphSummary(
            glyph_key=g.glyph_key,
            glyph=g.glyph,
            position=g.position,
            variant=g.variant,
            advance=g.advance,
            has_data=True,
        )
        for g in rows
    ]


@router.get("/{glyph_key}", response_model=GlyphOut)
async def get_glyph(glyph_key: str, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)):
    glyph = await GlyphRepository(db).get(source.id, glyph_key)
    if glyph is None:
        raise HTTPException(404, detail=f"no canonical for {glyph_key!r}")
    return _glyph_to_out(glyph)


@router.post("/{glyph_key}/trace", response_model=GlyphOut, dependencies=[Depends(require_admin)])
async def post_trace(
    glyph_key: str,
    payload: TraceRequest,
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    bbox = await BboxRepository(db).get(source.id, glyph_key)
    if bbox is None:
        raise HTTPException(409, detail=f"set bbox for {glyph_key!r} before tracing")
    canonical = canonical_from_path(
        raw_path=[p.model_dump() for p in payload.raw_path],
        bbox=_bbox_to_dict(bbox),
        chart_path=source.chart_path,
        glyph=payload.glyph,
        position=payload.position,
        n_anchors=payload.n_anchors,
    )
    g = await GlyphRepository(db).upsert(source.id, glyph_key, canonical, variant=payload.variant)
    return _glyph_to_out(g)


@router.post("/{glyph_key}/resample", response_model=GlyphOut, dependencies=[Depends(require_admin)])
async def post_resample(
    glyph_key: str,
    payload: ResampleRequest,
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    bbox = await BboxRepository(db).get(source.id, glyph_key)
    if bbox is None:
        raise HTTPException(409, detail=f"bbox for {glyph_key!r} missing")
    existing = await GlyphRepository(db).get(source.id, glyph_key)
    if existing is None:
        raise HTTPException(404, detail=f"no canonical to resample for {glyph_key!r}")
    if not existing.raw_path:
        raise HTTPException(409, detail="stored canonical has no raw_path; re-trace to enable resampling")
    canonical = canonical_from_raw_path_only(
        glyph_row={"raw_path": list(existing.raw_path), "glyph": existing.glyph, "position": existing.position},
        bbox=_bbox_to_dict(bbox),
        chart_path=source.chart_path,
        n_anchors=payload.n_anchors,
    )
    g = await GlyphRepository(db).upsert(source.id, glyph_key, canonical, variant=existing.variant)
    return _glyph_to_out(g)


@router.get("/{glyph_key}/diagnostic")
async def get_diagnostic(
    glyph_key: str, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    bbox = await BboxRepository(db).get(source.id, glyph_key)
    if bbox is None:
        raise HTTPException(404, detail=f"bbox not set for {glyph_key!r}")
    glyph = await GlyphRepository(db).get(source.id, glyph_key)
    if glyph is None:
        raise HTTPException(404, detail=f"no canonical for {glyph_key!r}")
    return diagnostic_for_glyph(
        glyph_row={
            "anchors": list(glyph.anchors),
            "half_widths": list(glyph.half_widths),
            "trace_meta": dict(glyph.trace_meta),
        },
        bbox=_bbox_to_dict(bbox),
        chart_path=source.chart_path,
        style_ratio=list(source.style_ratio),
        slant_deg=float(source.slant_deg),
    )


@router.get("/{glyph_key}/fit")
async def get_fit(
    glyph_key: str,
    lambda_reg: float = 1.0,
    width_weight: float = 0.15,
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    """M4: fit the stored canonical to its own crop skeleton (read-only).

    Returns a filled library entry plus crop-local overlay polylines
    (skeleton, canonical grey, fit red) and the `fit` diagnostic. `lambda_reg`
    (Tikhonov weight) and `width_weight` are tunable so the editor can show the
    regularisation trade-off live.
    """
    bbox = await BboxRepository(db).get(source.id, glyph_key)
    if bbox is None:
        raise HTTPException(404, detail=f"bbox not set for {glyph_key!r}")
    glyph = await GlyphRepository(db).get(source.id, glyph_key)
    if glyph is None:
        raise HTTPException(404, detail=f"no canonical for {glyph_key!r}")
    return fit_glyph_to_crop(
        glyph_row={
            "glyph": glyph.glyph,
            "position": glyph.position,
            "anchors": list(glyph.anchors),
            "half_widths": list(glyph.half_widths),
            "entry": dict(glyph.entry) if glyph.entry else {},
            "exit_pt": dict(glyph.exit_pt) if glyph.exit_pt else {},
        },
        bbox=_bbox_to_dict(bbox),
        chart_path=source.chart_path,
        lambda_reg=lambda_reg,
        width_weight=width_weight,
    )


@router.delete("/{glyph_key}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_glyph(
    glyph_key: str, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    await GlyphRepository(db).delete(source.id, glyph_key)
