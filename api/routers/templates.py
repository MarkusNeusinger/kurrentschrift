"""Template (canonical) endpoints — trace, resample, list, get, delete, diagnostic, fit.

Templates are canonical per *style* (Grundvorlage), not per source. The admin
works on a chart `source`; this router resolves the source's style and stores
the canonical there, recording the chart as `provenance_source_id`.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db, require_source
from api.schemas import ResampleRequest, TemplateOut, TemplateSummary, TraceRequest
from core.database import BboxRepository, Source, StyleRepository, Template, TemplateRepository
from core.fit import fit_glyph_to_crop
from core.pipeline import (
    DEFAULT_N_ANCHORS,
    canonical_from_path,
    canonical_from_raw_path_only,
    diagnostic_for_glyph,
    written_preview_for_canonical,
)
from core.quality import quality_for_glyph


router = APIRouter(prefix="/sources/{source_id}/templates", tags=["templates"])


def _reject_locked_unless_forced(bbox, force: bool) -> None:
    """Server-side backstop for the lock: writes to a locked glyph need `force`.

    The lock (Bbox.locked) used to be a UI-only contract; this enforces it at
    the API so an accidental write (stale tab, script) cannot mutate a
    finished glyph. 423 Locked tells the client exactly what to do.
    """
    if bbox.locked and not force:
        raise HTTPException(423, detail=f"glyph {bbox.glyph_key!r} is locked; pass force=true to overwrite")


async def _resolve_style(source: Source, db: AsyncSession) -> tuple[str, list[float], float]:
    """Return (style_id, resolved style_ratio, resolved slant_deg) for a source.

    A source may override the style defaults per chart; null => use the style.
    """
    style = await StyleRepository(db).get(source.style_id)
    if style is None:
        raise HTTPException(500, detail=f"source {source.id!r} references unknown style {source.style_id!r}")
    style_ratio = list(source.style_ratio) if source.style_ratio is not None else list(style.default_style_ratio)
    slant_deg = float(source.slant_deg) if source.slant_deg is not None else float(style.default_slant_deg)
    return style.id, style_ratio, slant_deg


def _bbox_to_dict(bbox) -> dict:
    guides = bbox.guides or {}
    return {
        "y0": bbox.y0,
        "y1": bbox.y1,
        "x0": bbox.x0,
        "x1": bbox.x1,
        "mask_strokes": list(bbox.mask_strokes),
        "baseline_y": bbox.baseline_y,
        "midband_y": bbox.midband_y,
        "n_anchors": bbox.n_anchors,
        # Coupling height travels with the bbox so trace/resample can stamp it
        # onto the canonical's entry/exit (default baseline when unset).
        "entry_coupling": guides.get("entry_coupling", "baseline"),
        "exit_coupling": guides.get("exit_coupling", "baseline"),
    }


def _template_to_out(t: Template) -> TemplateOut:
    return TemplateOut(
        glyph_key=t.glyph_key,
        glyph=t.glyph,
        position=t.position,
        variant=t.variant,
        advance=t.advance,
        entry=t.entry,
        exit_pt=t.exit_pt,
        anchors=t.anchors,
        half_widths=t.half_widths,
        raw_path=t.raw_path,
        trace_meta=t.trace_meta,
        measurements=t.measurements,
    )


@router.get("", response_model=list[TemplateSummary])
async def list_templates(source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)):
    rows = await TemplateRepository(db).list(source.style_id)
    return [
        TemplateSummary(
            glyph_key=t.glyph_key,
            glyph=t.glyph,
            position=t.position,
            variant=t.variant,
            advance=t.advance,
            has_data=True,
        )
        for t in rows
    ]


@router.get("/{glyph_key}", response_model=TemplateOut)
async def get_template(
    glyph_key: str, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    template = await TemplateRepository(db).get(source.style_id, glyph_key)
    if template is None:
        raise HTTPException(404, detail=f"no canonical for {glyph_key!r}")
    return _template_to_out(template)


@router.post("/{glyph_key}/trace", response_model=TemplateOut, dependencies=[Depends(require_admin)])
async def post_trace(
    glyph_key: str,
    payload: TraceRequest,
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    bbox = await BboxRepository(db).get(source.id, glyph_key)
    if bbox is None:
        raise HTTPException(409, detail=f"set bbox for {glyph_key!r} before tracing")
    _reject_locked_unless_forced(bbox, payload.force)
    # CPU-bound (binarize + skeleton + EDT) — keep it off the event loop.
    canonical = await run_in_threadpool(
        canonical_from_path,
        raw_path=[p.model_dump() for p in payload.raw_path],
        bbox=_bbox_to_dict(bbox),
        chart_path=source.chart_path,
        glyph=payload.glyph,
        position=payload.position,
        n_anchors=payload.n_anchors,
    )
    t = await TemplateRepository(db).upsert(
        source.style_id, glyph_key, canonical, variant=payload.variant, provenance_source_id=source.id
    )
    return _template_to_out(t)


@router.post("/{glyph_key}/trace-preview", dependencies=[Depends(require_admin)])
async def post_trace_preview(
    glyph_key: str,
    payload: TraceRequest,
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    """Dry-run trace: derive the raw and the optimized variant, write NOTHING.

    The wizard's Optimieren step renders both as written glyphs side by side
    (with their image-space quality scores) so the user confirms the
    optimization before the real /trace persists it. Admin-gated like /trace —
    it costs the same CPU — but no lock check: nothing is stored.
    """
    bbox = await BboxRepository(db).get(source.id, glyph_key)
    if bbox is None:
        raise HTTPException(409, detail=f"set bbox for {glyph_key!r} before tracing")
    _, style_ratio, slant_deg = await _resolve_style(source, db)
    bbox_dict = _bbox_to_dict(bbox)
    raw_path = [p.model_dump() for p in payload.raw_path]

    def compute() -> dict:
        out: dict = {}
        for name, refine in (("raw", False), ("refined", True)):
            canon = canonical_from_path(
                raw_path=raw_path,
                bbox=bbox_dict,
                chart_path=source.chart_path,
                glyph=payload.glyph,
                position=payload.position,
                n_anchors=payload.n_anchors,
                refine=refine,
            )
            out[name] = written_preview_for_canonical(canon, style_ratio, slant_deg)
        return out

    return await run_in_threadpool(compute)


@router.post("/{glyph_key}/resample", response_model=TemplateOut, dependencies=[Depends(require_admin)])
async def post_resample(
    glyph_key: str,
    payload: ResampleRequest,
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    bbox = await BboxRepository(db).get(source.id, glyph_key)
    if bbox is None:
        raise HTTPException(409, detail=f"bbox for {glyph_key!r} missing")
    _reject_locked_unless_forced(bbox, payload.force)
    existing = await TemplateRepository(db).get(source.style_id, glyph_key)
    if existing is None:
        raise HTTPException(404, detail=f"no canonical to resample for {glyph_key!r}")
    if not existing.raw_path:
        raise HTTPException(409, detail="stored canonical has no raw_path; re-trace to enable resampling")
    # None means "re-derive with current code AND its current recommended
    # anchor density" — DEFAULT_N_ANCHORS is bench-calibrated; a deliberate
    # per-glyph count still wins by sending n_anchors explicitly (the wizard
    # slider does).
    n_anchors = payload.n_anchors or DEFAULT_N_ANCHORS
    canonical = await run_in_threadpool(
        canonical_from_raw_path_only,
        glyph_row={"raw_path": list(existing.raw_path), "glyph": existing.glyph, "position": existing.position},
        bbox=_bbox_to_dict(bbox),
        chart_path=source.chart_path,
        n_anchors=n_anchors,
    )
    t = await TemplateRepository(db).upsert(
        source.style_id, glyph_key, canonical, variant=existing.variant, provenance_source_id=source.id
    )
    return _template_to_out(t)


@router.get("/{glyph_key}/diagnostic")
async def get_diagnostic(
    glyph_key: str, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    bbox = await BboxRepository(db).get(source.id, glyph_key)
    if bbox is None:
        raise HTTPException(404, detail=f"bbox not set for {glyph_key!r}")
    template = await TemplateRepository(db).get(source.style_id, glyph_key)
    if template is None:
        raise HTTPException(404, detail=f"no canonical for {glyph_key!r}")
    _, style_ratio, slant_deg = await _resolve_style(source, db)
    return await run_in_threadpool(
        diagnostic_for_glyph,
        glyph_row={
            "anchors": list(template.anchors),
            "half_widths": list(template.half_widths),
            "trace_meta": dict(template.trace_meta),
        },
        bbox=_bbox_to_dict(bbox),
        chart_path=source.chart_path,
        style_ratio=style_ratio,
        slant_deg=slant_deg,
    )


@router.get("/{glyph_key}/fit")
async def get_fit(
    glyph_key: str,
    lambda_reg: float = 1.0,
    width_weight: float = 0.15,
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    """Fit the stored canonical to its own crop skeleton (read-only).

    The optimisation takes seconds and is pure CPU — run it in the threadpool
    so it cannot freeze every other request on the event loop.
    """
    bbox = await BboxRepository(db).get(source.id, glyph_key)
    if bbox is None:
        raise HTTPException(404, detail=f"bbox not set for {glyph_key!r}")
    template = await TemplateRepository(db).get(source.style_id, glyph_key)
    if template is None:
        raise HTTPException(404, detail=f"no canonical for {glyph_key!r}")
    return await run_in_threadpool(
        fit_glyph_to_crop,
        glyph_row={
            "glyph": template.glyph,
            "position": template.position,
            "anchors": list(template.anchors),
            "half_widths": list(template.half_widths),
            "entry": dict(template.entry) if template.entry else {},
            "exit_pt": dict(template.exit_pt) if template.exit_pt else {},
            # Pen-stroke boundaries so the fit samples each stroke on its own;
            # corner knots so the fit's spline keeps the same kinks the render does.
            "stroke_starts": (template.trace_meta or {}).get("stroke_starts"),
            "corner_anchors": (template.trace_meta or {}).get("corner_anchors"),
        },
        bbox=_bbox_to_dict(bbox),
        chart_path=source.chart_path,
        lambda_reg=lambda_reg,
        width_weight=width_weight,
    )


@router.get("/{glyph_key}/quality")
async def get_quality(glyph_key: str, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)):
    """Image-space quality of the stored template, plus a re-derive dry run.

    `stored` scores what the DB currently holds against its crop; `candidate`
    is the quality a fresh re-derivation from `raw_path` with the CURRENT
    pipeline code would achieve (nothing is written — the admin compares both
    before deciding to /resample). Pure CPU, threadpooled like /fit.
    """
    bbox = await BboxRepository(db).get(source.id, glyph_key)
    if bbox is None:
        raise HTTPException(404, detail=f"bbox not set for {glyph_key!r}")
    template = await TemplateRepository(db).get(source.style_id, glyph_key)
    if template is None:
        raise HTTPException(404, detail=f"no canonical for {glyph_key!r}")
    bbox_dict = _bbox_to_dict(bbox)
    trace_meta = dict(template.trace_meta or {})
    # Older templates predate the pixel-space trace meta the metric scores —
    # a clear 409 beats the ValueError-turned-500 the metric would raise.
    if not trace_meta.get("pixel_anchors") or not trace_meta.get("half_widths_px"):
        raise HTTPException(
            409, detail=f"stored template for {glyph_key!r} lacks pixel-space trace meta; resample or re-trace first"
        )
    raw_path = list(template.raw_path or [])
    glyph, position = template.glyph, template.position
    # The candidate must preview exactly what apply (= /resample without an
    # explicit count) would store: current code + recommended anchor density.
    n_anchors = DEFAULT_N_ANCHORS

    def compute() -> dict:
        stored = quality_for_glyph({"trace_meta": trace_meta}, bbox_dict, source.chart_path)
        candidate = None
        candidate_refine = None
        if raw_path:
            canon = canonical_from_raw_path_only(
                glyph_row={"raw_path": raw_path, "glyph": glyph, "position": position},
                bbox=bbox_dict,
                chart_path=source.chart_path,
                n_anchors=n_anchors,
            )
            candidate = canon["trace_meta"].get("quality")
            candidate_refine = canon["trace_meta"].get("refine")
        return {"stored": stored, "candidate": candidate, "candidate_refine": candidate_refine}

    return await run_in_threadpool(compute)


@router.delete("/{glyph_key}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_template(
    glyph_key: str, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    await TemplateRepository(db).delete(source.style_id, glyph_key)
