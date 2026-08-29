"""Template (canonical) endpoints — trace, resample, list, get, delete, diagnostic, fit.

Templates are canonical per *style* (Grundvorlage), not per source. The admin
works on a chart `source`; this router resolves the source's style and stores
the canonical there, recording the chart as `provenance_source_id`.
"""

from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db, require_source
from api.rendering import invalidate_pooled_style, resolve_render_context, resolve_style
from api.schemas import LaufformUpsert, ResampleRequest, TemplateOut, TemplateQualityOut, TemplateSummary, TraceRequest
from core.aggregate import LAUFFORM_MIN_OCCURRENCES
from core.database import LAUFFORM_VARIANT, BboxRepository, Source, Template, TemplateRepository
from core.fit import fit_glyph_to_crop
from core.laufform import LAUFFORM_END_WINDOW, blend_stroke_ends, spike_gate
from core.pipeline import (
    DEFAULT_N_ANCHORS,
    canonical_from_path,
    canonical_from_raw_path_only,
    diagnostic_for_glyph,
    written_preview_for_canonical,
)
from core.quality import quality_for_glyph
from core.quality_suetterlin import suetterlin_quality_for_glyph
from core.shaping import expected_glyph_key, is_registry_glyph_key
from core.suetterlin import canonical_suetterlin_from_path, canonical_suetterlin_from_raw_path_only


def _derive_canonical(width_resolver: str, **kwargs) -> dict:
    """Derive a canonical with the geometry path the style demands.

    Constant-width styles (Sütterlin Gleichzug) go through the skeleton-locked
    `core.suetterlin` derivation; everything else uses the pressure pipeline.
    Both accept the same kwargs (raw_path, bbox, chart_path, glyph,
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


def _reject_key_identity_mismatch(glyph_key: str, glyph: str) -> None:
    """Backstop: the URL's glyph_key and the payload's glyph must agree.

    The template upsert conflicts on (style, glyph, variant) while reads go by
    glyph_key — a mismatched pair would conflict-update another row and
    rewrite its glyph_key, so subsequent GETs silently 404. Derive the
    expected key from the shared registry (core.shaping, the Python twin of
    glyphs.ts); a glyph outside the registry subset keeps its client-chosen
    key but may never claim a registry-owned one.
    """
    expected = expected_glyph_key(glyph)
    if expected is not None:
        if expected != glyph_key:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"glyph_key {glyph_key!r} does not match glyph {glyph!r} (expected {expected!r})",
            )
    elif is_registry_glyph_key(glyph_key):
        # An out-of-registry glyph may never claim a registry-owned key: the
        # upsert would stamp that key onto its own glyph row and duplicate it
        # against the registry glyph's row.
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"glyph_key {glyph_key!r} belongs to a registry glyph, not to {glyph!r}",
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
    return {
        **bbox.to_pipeline_dict(),
        "baseline_y": bbox.baseline_y,
        "midband_y": bbox.midband_y,
        "n_anchors": bbox.n_anchors,
    }


def _template_to_out(t: Template) -> TemplateOut:
    return TemplateOut(
        glyph_key=t.glyph_key,
        glyph=t.glyph,
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
    # Deliberately uncached: the admin sidebar reads this same list and expects
    # a fresh `has_data` immediately after a trace/delete — a browser max-age
    # would serve it the pre-write list for minutes. The public quiz boot
    # tolerates the origin round trip (it already rides the cold-start retry).
    rows = await TemplateRepository(db).list_summaries(source.style_id)
    return [TemplateSummary(**row, has_data=True) for row in rows]


# MUST stay above `GET /{glyph_key}`: FastAPI matches routes in declaration
# order, so a later literal path would be swallowed as a glyph_key.
# Admin-gated for the same open-core reason as the full row (quellen-und-rechte.md
# §5) — a quality score is measured over the learned dataset. Uncached like the
# summary list: the admin expects the fresh number right after a re-derive.
@router.get("/quality", response_model=list[TemplateQualityOut], dependencies=[Depends(require_admin)])
async def list_template_quality(source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)):
    """Every template's stored quality score in one read (admin only).

    The score as the derivation stamped it — see TemplateQualityOut; the
    per-glyph `/{glyph_key}/quality` below is the one that re-derives.
    """
    rows = await TemplateRepository(db).list_quality(source.style_id)
    return [TemplateQualityOut(**row) for row in rows]


# Admin-gated as the open-core moat (quellen-und-rechte.md §5): the full row
# is the learned dataset's raw form (anchors, half_widths, raw stylus path)
# and no public surface needs it — the public pages render from the /write
# payloads, and the summary list above carries no geometry. The docstring
# below stays short because it surfaces in the public OpenAPI docs.
# `variant` makes the STORED derived rows readable too (issue #311): the
# wordbench fixture layer froze a local reconstruction of the Laufform rows
# before this existed, and a knife-edge classification turned that
# rebuild-instead-of-read into a discrete render flip. Same philosophy as the
# render-context nib read — transported, not re-derived.
@router.get("/{glyph_key}", response_model=TemplateOut, dependencies=[Depends(require_admin)])
async def get_template(
    glyph_key: str,
    variant: int = Query(0, ge=0, le=999, description=f"template variant; {LAUFFORM_VARIANT} = the Laufform row"),
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    """The full authored template (admin only)."""
    template = await TemplateRepository(db).get(source.style_id, glyph_key, variant=variant)
    if template is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"no variant-{variant} canonical for {glyph_key!r}")
    return _template_to_out(template)


def build_laufform_canonical(
    base: Template,
    anchors: Sequence[Sequence[float]],
    laufform_meta: dict,
    *,
    end_window: float = LAUFFORM_END_WINDOW,
    transverse_only: bool = True,
) -> dict:
    """The LAUFFORM_VARIANT canonical for one glyph: median geometry on the
    chart row's ductus.

    The ONE derivation of a running-form row, shared by the manual
    `PUT …/laufform` (harvest drafts) and the aggregate-derived apply endpoint
    (`POST /hands/{id}/aggregates/apply-laufform`, Stufenplan H1) so the two
    can never produce differently-shaped rows. Everything but the anchors comes
    from the chart template: widths, stroke topology (`trace_meta`), and
    entry/exit/advance shifted by their end anchors' delta. `laufform_meta`
    lands under `trace_meta.laufform` and records where the median came from.

    The stroke ENDS' direction is the ductus prior's too (end blend,
    `core.laufform.blend_stroke_ends`, §14 LF5/LF6): within `end_window` of arc
    length from every free stroke end the median's transverse deviation from
    the chart shape fades to zero (its longitudinal one — the running form's
    own extent — stays), rigidly attached at the Laufform's placement — the
    fitted ends drift toward neighbouring ink, and the composer reads its join
    tangents off exactly those ends. Window and mode are stamped as
    `trace_meta.laufform.end_window` / `end_mode`; a window of `0` reproduces
    the pre-blend row (anchors verbatim).

    Args:
        base: The variant-0 chart template — the ductus prior.
        anchors: The median anchors, same count as `base.anchors`.
        laufform_meta: Provenance dict for `trace_meta.laufform`.
        end_window: Arc-length window (x-height units) of the end blend.
        transverse_only: LF6 (fade the transverse residual only, default) or
            the LF5 full cross-fade — see `blend_stroke_ends`.

    Returns:
        A canonical dict in `TemplateRepository.upsert` shape.
    """
    chart = [tuple(p) for p in base.anchors]
    stroke_starts = (base.trace_meta or {}).get("stroke_starts") or [0]
    blended = blend_stroke_ends(chart, anchors, stroke_starts, window=end_window, transverse_only=transverse_only)
    canonical: dict[str, Any] = {
        "glyph": base.glyph,
        "anchors": blended,
        "half_widths": base.half_widths,
        # No stylus capture behind a derived variant — an empty path, not
        # NULL, so every raw_path consumer keeps its list contract.
        "raw_path": [],
        "trace_meta": {
            **(base.trace_meta or {}),
            "laufform": {
                **laufform_meta,
                "end_window": end_window,
                "end_mode": "transverse" if transverse_only else "full",
            },
        },
    }
    # Entry/exit/advance ride their (blended) end anchors: shift the chart
    # fields by the respective anchor delta. The tangents stay — after the end
    # blend the end pieces ARE the chart's, and the composer re-measures
    # tangents off the rendered centerline anyway.
    d_in = (blended[0][0] - chart[0][0], blended[0][1] - chart[0][1])
    d_out = (blended[-1][0] - chart[-1][0], blended[-1][1] - chart[-1][1])
    for field, delta in (("entry", d_in), ("exit_pt", d_out)):
        stored = getattr(base, field) or {}
        if stored.get("xy"):
            stored = {**stored, "xy": [stored["xy"][0] + delta[0], stored["xy"][1] + delta[1]]}
        canonical[field] = stored
    canonical["advance"] = (base.advance or 0.0) + d_out[0]
    return canonical


@router.put("/{glyph_key}/laufform", response_model=TemplateOut, dependencies=[Depends(require_admin)])
async def put_laufform(
    glyph_key: str,
    payload: LaufformUpsert,
    min_occurrences: int = Query(
        LAUFFORM_MIN_OCCURRENCES,
        ge=1,
        description="evidence floor for THIS write (default: the server floor; lower it only as an explicit author statement)",
    ),
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    """Store the median RUNNING form as templates LAUFFORM_VARIANT (jul31 doctrine:
    chart cell = ductus prior, written words = form model). The anchors must
    match the chart row one-to-one — same count, same stroke topology — so
    stroke starts, corners and crossings carry over unchanged; entry/exit/
    advance shift with their end anchors. `/write/word` picks the row up for
    glyphs in a flowing run; solo renders stay chart-true.

    Two gates stand in front of the write (qualitaetsmetrik.md §14 LF7/LF8),
    the same two `apply-laufform` applies: the evidence floor
    `LAUFFORM_MIN_OCCURRENCES` — a thinner draft is refused unless the request
    lowers the floor itself (`?min_occurrences=1`, the explicit author
    statement) — and the row gate: a draft whose anchor spike ratio („Anker im
    leeren Papier", the harvest's own detector measured on the row) exceeds
    `LAUFFORM_SPIKE_RATIO_MAX` is refused with the ratio in the detail, without
    an override (it is fit noise, not author knowledge). The Sütterlin K
    entered the writing path through this very endpoint with n = 1 and a
    spiked, wavy tail; a word-ruler gain is no admission."""
    base = await TemplateRepository(db).get(source.style_id, glyph_key, variant=0)
    if base is None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=f"no chart template for {glyph_key!r} — author it first")
    if len(payload.anchors) != len(base.anchors):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"anchor count {len(payload.anchors)} != chart row's {len(base.anchors)}"
            " — the ductus prior must match",
        )
    if payload.n_occurrences < min_occurrences:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{payload.n_occurrences} occurrence(s) behind the draft for {glyph_key!r} — below the floor of "
            f"{min_occurrences} (LAUFFORM_MIN_OCCURRENCES); pass ?min_occurrences=1 only as an explicit author statement",
        )
    spike = spike_gate(base, payload.anchors)
    if spike["exceeded"]:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"the draft for {glyph_key!r} carries an anchor spike: ratio {spike['ratio']:.2f} over the row gate "
            f'{spike["max"]:.2f} (§14 LF8, „Anker im leeren Papier") — more evidence or the chart fallback, no override',
        )
    canonical = build_laufform_canonical(
        base, payload.anchors, {"derived_from": "specimen-words", "n_occurrences": payload.n_occurrences}
    )
    t = await TemplateRepository(db).upsert(
        source.style_id, glyph_key, canonical, variant=LAUFFORM_VARIANT, provenance_source_id=source.id
    )
    out = _template_to_out(t)
    await db.commit()
    invalidate_pooled_style(source.style_id)
    return out


@router.delete("/{glyph_key}/laufform", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def delete_laufform(
    glyph_key: str, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    """Remove the running-form variant; composition falls back to the chart
    row (plus the LAUFFORM_SX width factor)."""
    deleted = await TemplateRepository(db).delete(source.style_id, glyph_key, variant=LAUFFORM_VARIANT)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"no laufform variant for {glyph_key!r}")
    await db.commit()
    invalidate_pooled_style(source.style_id)


@router.post("/{glyph_key}/trace", response_model=TemplateOut, dependencies=[Depends(require_admin)])
async def post_trace(
    glyph_key: str,
    payload: TraceRequest,
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    _reject_key_identity_mismatch(glyph_key, payload.glyph)
    # Stored-row backstop for keys the registry doesn't know: whatever row this
    # key already names must carry the same glyph — otherwise the upsert
    # (conflict target: style/glyph/variant) would write onto a DIFFERENT row
    # and leave two rows claiming the same glyph_key.
    stored = await TemplateRepository(db).get(source.style_id, glyph_key, variant=payload.variant)
    if stored is not None and stored.glyph != payload.glyph:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"glyph_key {glyph_key!r} already names glyph {stored.glyph!r};"
            f" refusing to re-key it to {payload.glyph!r}",
        )
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
        n_anchors=payload.n_anchors,
    )
    t = await TemplateRepository(db).upsert(
        source.style_id, glyph_key, canonical, variant=payload.variant, provenance_source_id=source.id
    )
    _sync_bbox_anchor_count(bbox, canonical)
    out = _template_to_out(t)
    # Commit BEFORE invalidating the pooled-nib cache: get_db only commits in
    # its teardown, so invalidating first would let a concurrent public request
    # repopulate the cache (TTL 600s) from the pre-write DB state. The
    # teardown's commit then finalises an already-committed session (a no-op).
    await db.commit()
    invalidate_pooled_style(source.style_id)
    return out


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
        glyph_row={"raw_path": list(existing.raw_path), "glyph": existing.glyph},
        bbox=_bbox_to_dict(bbox),
        chart_path=source.chart_path,
        n_anchors=n_anchors,
    )
    t = await TemplateRepository(db).upsert(
        source.style_id, glyph_key, canonical, variant=existing.variant, provenance_source_id=source.id
    )
    _sync_bbox_anchor_count(bbox, canonical)
    out = _template_to_out(t)
    # Commit before invalidating the pooled-nib cache — see post_trace.
    await db.commit()
    invalidate_pooled_style(source.style_id)
    return out


@router.get("/{glyph_key}/diagnostic", dependencies=[Depends(require_admin)])
async def get_diagnostic(
    glyph_key: str, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    """3-column diagnostic payload (crop · skeleton+anchors · canonical).

    Re-runs the image pipeline (chart decode + binarise + skeletonise) per
    request — admin-gated like /fit and /quality ("it costs the same CPU").
    Only the admin surfaces (Diagnose dialog, wizard, /admin/buchstaben) consume
    it; the public renderer reads the cached /write payloads instead.
    """
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
    lambda_reg: float = Query(1.0, ge=0.0, le=100.0),
    width_weight: float = Query(0.15, ge=0.0, le=10.0),
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
    glyph = template.glyph
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
                glyph_row={"raw_path": raw_path, "glyph": glyph},
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
    deleted = await TemplateRepository(db).delete(source.style_id, glyph_key)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"no canonical for {glyph_key!r}")
    # Commit before invalidating the pooled-nib cache — see post_trace.
    await db.commit()
    invalidate_pooled_style(source.style_id)
