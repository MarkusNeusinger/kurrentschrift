"""Template (canonical) endpoints — trace, resample, list, get, delete, diagnostic, fit.

Templates are canonical per *style* (Grundvorlage), not per source. The admin
works on a chart `source`; this router resolves the source's style and stores
the canonical there, recording the chart as `provenance_source_id`.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db, require_source
from api.rendering import invalidate_pooled_nib, resolve_render_context, resolve_style
from api.schemas import ResampleRequest, TemplateOut, TemplateSummary, TraceRequest
from core.database import BboxRepository, Source, Template, TemplateRepository
from core.fit import fit_glyph_to_crop
from core.pipeline import (
    DEFAULT_N_ANCHORS,
    canonical_from_path,
    canonical_from_raw_path_only,
    diagnostic_for_glyph,
    written_preview_for_canonical,
)
from core.quality import quality_for_glyph
from core.quality_suetterlin import suetterlin_quality_for_glyph
from core.suetterlin import canonical_suetterlin_from_path, canonical_suetterlin_from_raw_path_only


def _derive_canonical(width_resolver: str, **kwargs) -> dict:
    """Derive a canonical with the geometry path the style demands.

    Constant-width styles (Sütterlin Gleichzug) go through the skeleton-locked
    `core.suetterlin` derivation; everything else uses the pressure pipeline.
    Both accept the same kwargs (raw_path, bbox, chart_path, glyph, position,
    n_anchors), so the call site stays identical.
    """
    if width_resolver == "constant":
        return canonical_suetterlin_from_path(**kwargs)
    return canonical_from_path(**kwargs)


def _derive_canonical_from_raw(width_resolver: str, **kwargs) -> dict:
    """Re-derive from a stored `raw_path` with the style's geometry path."""
    if width_resolver == "constant":
        return canonical_suetterlin_from_raw_path_only(**kwargs)
    return canonical_from_raw_path_only(**kwargs)


router = APIRouter(prefix="/sources/{source_id}/templates", tags=["templates"])


def _reject_locked_unless_forced(bbox, force: bool) -> None:
    """Server-side backstop for the lock: writes to a locked glyph need `force`.

    The lock (Bbox.locked) used to be a UI-only contract; this enforces it at
    the API so an accidental write (stale tab, script) cannot mutate a
    finished glyph. 423 Locked tells the client exactly what to do.
    """
    if bbox.locked and not force:
        raise HTTPException(
            status.HTTP_423_LOCKED, detail=f"glyph {bbox.glyph_key!r} is locked; pass force=true to overwrite"
        )


def _sync_bbox_anchor_count(bbox, canonical: dict) -> None:
    """Keep bbox.n_anchors truthful to the canonical that was just derived.

    The derivation count is `n_anchors or DEFAULT_N_ANCHORS`, not bbox.n_anchors
    — so a bulk or per-glyph re-derive at the recommended density leaves the
    bbox field stale (the wizard's anchor input would still show the old count,
    and a wizard resample from there would revert the template). Mirror the
    actual count back. The bbox row is session-attached, so the mutation is
    flushed and committed with the rest of the request — no explicit flush.
    """
    actual = int(canonical.get("trace_meta", {}).get("n_anchors") or len(canonical.get("anchors", [])))
    if actual and actual != bbox.n_anchors:
        bbox.n_anchors = actual


def _bbox_to_dict(bbox) -> dict:
    """The full derivation dict: the shared crop-affecting fields
    (`Bbox.to_pipeline_dict`, so ink/patches/auto-fill can't drift from the crop
    preview) plus the calibration the anchor/width derivation needs on top."""
    guides = bbox.guides or {}
    return {
        **bbox.to_pipeline_dict(),
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
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"no canonical for {glyph_key!r}")
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
        raise HTTPException(status.HTTP_409_CONFLICT, detail=f"set bbox for {glyph_key!r} before tracing")
    _reject_locked_unless_forced(bbox, payload.force)
    _, _, _, width_resolver = await resolve_style(source, db)
    # CPU-bound (binarize + skeleton + EDT) — keep it off the event loop.
    canonical = await run_in_threadpool(
        _derive_canonical,
        width_resolver,
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
    _sync_bbox_anchor_count(bbox, canonical)
    invalidate_pooled_nib(source.style_id, source.id)
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
        raise HTTPException(status.HTTP_409_CONFLICT, detail=f"set bbox for {glyph_key!r} before tracing")
    _, style_ratio, slant_deg, width_resolver = await resolve_style(source, db)
    bbox_dict = _bbox_to_dict(bbox)
    raw_path = [p.model_dump() for p in payload.raw_path]

    def compute() -> dict:
        # Gleichzug has no edge-refine stage: the skeleton-locked geometry is
        # final, so "raw" and "refined" are the same canonical (computed once).
        if width_resolver == "constant":
            canon = canonical_suetterlin_from_path(
                raw_path=raw_path,
                bbox=bbox_dict,
                chart_path=source.chart_path,
                glyph=payload.glyph,
                position=payload.position,
                n_anchors=payload.n_anchors,
            )
            preview = written_preview_for_canonical(canon, style_ratio, slant_deg, width_resolver)
            return {"raw": preview, "refined": preview}
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
            out[name] = written_preview_for_canonical(canon, style_ratio, slant_deg, width_resolver)
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
        raise HTTPException(status.HTTP_409_CONFLICT, detail=f"bbox for {glyph_key!r} missing")
    _reject_locked_unless_forced(bbox, payload.force)
    existing = await TemplateRepository(db).get(source.style_id, glyph_key)
    if existing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"no canonical to resample for {glyph_key!r}")
    if not existing.raw_path:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="stored canonical has no raw_path; re-trace to enable resampling"
        )
    # None means "re-derive with current code AND its current recommended
    # anchor density" — DEFAULT_N_ANCHORS is bench-calibrated; a deliberate
    # per-glyph count still wins by sending n_anchors explicitly (the wizard
    # slider does).
    n_anchors = payload.n_anchors or DEFAULT_N_ANCHORS
    _, _, _, width_resolver = await resolve_style(source, db)
    canonical = await run_in_threadpool(
        _derive_canonical_from_raw,
        width_resolver,
        glyph_row={"raw_path": list(existing.raw_path), "glyph": existing.glyph, "position": existing.position},
        bbox=_bbox_to_dict(bbox),
        chart_path=source.chart_path,
        n_anchors=n_anchors,
    )
    t = await TemplateRepository(db).upsert(
        source.style_id, glyph_key, canonical, variant=existing.variant, provenance_source_id=source.id
    )
    _sync_bbox_anchor_count(bbox, canonical)
    invalidate_pooled_nib(source.style_id, source.id)
    return _template_to_out(t)


@router.get("/{glyph_key}/diagnostic")
async def get_diagnostic(
    glyph_key: str, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    bbox = await BboxRepository(db).get(source.id, glyph_key)
    if bbox is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"bbox not set for {glyph_key!r}")
    template = await TemplateRepository(db).get(source.style_id, glyph_key)
    if template is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"no canonical for {glyph_key!r}")
    ctx = await resolve_render_context(source, db)
    return await run_in_threadpool(
        diagnostic_for_glyph,
        glyph_row={
            "anchors": list(template.anchors),
            "half_widths": list(template.half_widths),
            "trace_meta": dict(template.trace_meta),
            # Connection metadata so the public word renderer can place glyphs and
            # generate the Übergänge between them (architektur.md §4).
            "entry": dict(template.entry) if template.entry else {},
            "exit_pt": dict(template.exit_pt) if template.exit_pt else {},
            "advance": template.advance,
        },
        bbox=_bbox_to_dict(bbox),
        chart_path=source.chart_path,
        style_ratio=ctx.style_ratio,
        slant_deg=ctx.slant_deg,
        width_resolver=ctx.width_resolver,
        constant_nib_units=ctx.nib,
    )


@router.get("/{glyph_key}/fit", dependencies=[Depends(require_admin)])
async def get_fit(
    glyph_key: str,
    lambda_reg: float = 1.0,
    width_weight: float = 0.15,
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    """Fit the stored canonical to its own crop skeleton (read-only).

    The optimisation takes seconds and is pure CPU — run it in the threadpool
    so it cannot freeze every other request on the event loop. Admin-gated
    like the writes (it costs the same CPU); only the public renderer's
    read endpoints stay open.
    """
    bbox = await BboxRepository(db).get(source.id, glyph_key)
    if bbox is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"bbox not set for {glyph_key!r}")
    template = await TemplateRepository(db).get(source.style_id, glyph_key)
    if template is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"no canonical for {glyph_key!r}")
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


@router.get("/{glyph_key}/quality", dependencies=[Depends(require_admin)])
async def get_quality(glyph_key: str, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)):
    """Image-space quality of the stored template, plus a re-derive dry run.

    `stored` scores what the DB currently holds against its crop; `candidate`
    is the quality a fresh re-derivation from `raw_path` with the CURRENT
    pipeline code would achieve (nothing is written — the admin compares both
    before deciding to /resample). Pure CPU, threadpooled and admin-gated like /fit.

    BOTH sides are scored with the style's OWN metric: the Kurrent pixel/width
    metric for the pressure pipeline, the Gleichzug naturalness metric for a
    constant-width style. `candidate` already comes from the canonical's
    `trace_meta.quality` (the metric the derivation stamped), so `stored` must
    use the matching metric — else a Sütterlin delta subtracts a naturalness
    score from a Kurrent coverage score and never converges to 0 after a write.
    """
    bbox = await BboxRepository(db).get(source.id, glyph_key)
    if bbox is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"bbox not set for {glyph_key!r}")
    template = await TemplateRepository(db).get(source.style_id, glyph_key)
    if template is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"no canonical for {glyph_key!r}")
    bbox_dict = _bbox_to_dict(bbox)
    trace_meta = dict(template.trace_meta or {})
    # Older templates predate the pixel-space trace meta the metric scores —
    # a clear 409 beats the ValueError-turned-500 the metric would raise.
    if not trace_meta.get("pixel_anchors") or not trace_meta.get("half_widths_px"):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"stored template for {glyph_key!r} lacks pixel-space trace meta; resample or re-trace first",
        )
    raw_path = list(template.raw_path or [])
    glyph, position = template.glyph, template.position
    _, _, _, width_resolver = await resolve_style(source, db)
    # The candidate must preview exactly what apply (= /resample without an
    # explicit count) would store: current code + recommended anchor density.
    n_anchors = DEFAULT_N_ANCHORS

    def compute() -> dict:
        if width_resolver == "constant":
            stored = suetterlin_quality_for_glyph({"trace_meta": trace_meta}, bbox_dict, source.chart_path)
        else:
            stored = quality_for_glyph({"trace_meta": trace_meta}, bbox_dict, source.chart_path)
        candidate = None
        candidate_refine = None
        if raw_path:
            canon = _derive_canonical_from_raw(
                width_resolver,
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
    invalidate_pooled_nib(source.style_id, source.id)
