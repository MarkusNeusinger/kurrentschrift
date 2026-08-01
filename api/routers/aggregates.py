"""Per-hand aggregate endpoints (Stufenplan H1): read + rebuild + apply.

The statistics layer's second stage: `instances` holds every clean occurrence,
this router condenses them per `(glyph_key, variant)` into the per-anchor
median (the running form), its spread and the pooled layer-1 statistics.

Unlike the occurrence reads, the WHOLE router is admin-gated: an aggregate is
learned geometry — the median form of a hand — and therefore part of the
open-core moat (quellen-und-rechte.md §5), not public product surface. The read
and the rebuild affect no rendering; the composer keeps reading templates and
approved `glyph_pairs` only. `POST …/apply-laufform` closes H1's loop and IS a
render-affecting write — the variant-100 Laufform row becomes a DERIVATION from
the stored aggregate instead of the harvest's end product — which is exactly
why it is its own deliberate step and never a side effect of the rebuild.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db
from api.rendering import invalidate_pooled_style
from api.routers.templates import build_laufform_canonical
from api.schemas import (
    AggregateApplyKeySummary,
    AggregateApplyOut,
    AggregateApplySkip,
    AggregateKeySummary,
    AggregateOut,
    AggregateRebuildOut,
)
from core.aggregate import aggregate_instances, laufform_deviation
from core.database import (
    LAUFFORM_VARIANT,
    Aggregate,
    AggregateRepository,
    Hand,
    HandRepository,
    InstanceRepository,
    TemplateRepository,
)


router = APIRouter(prefix="/hands/{hand_id}/aggregates", tags=["aggregates"], dependencies=[Depends(require_admin)])


async def require_hand(hand_id: str, db: AsyncSession = Depends(require_db)) -> Hand:
    """Load the writer row this rebuild aggregates over (404 if unknown)."""
    hand = await HandRepository(db).get(hand_id)
    if hand is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"unknown hand {hand_id!r}")
    return hand


def _to_out(row: Aggregate) -> AggregateOut:
    return AggregateOut(
        glyph_key=row.glyph_key,
        glyph=row.glyph,
        variant=row.variant,
        cluster_center=[list(a) for a in row.cluster_center or []],
        hull=dict(row.hull or {}),
        mean_stats=dict(row.mean_stats or {}),
        n_instances=row.n_instances,
    )


@router.get("", response_model=list[AggregateOut])
async def list_aggregates(hand: Hand = Depends(require_hand), db: AsyncSession = Depends(require_db)):
    """This hand's stored aggregates, by glyph_key. Uncached like the
    occurrence reads: the rebuild writes and expects fresh rows."""
    rows = await AggregateRepository(db).list(hand_id=hand.id)
    return [_to_out(r) for r in rows]


@router.post("/rebuild", response_model=AggregateRebuildOut)
async def rebuild_aggregates(
    min_n: int = Query(4, ge=1), hand: Hand = Depends(require_hand), db: AsyncSession = Depends(require_db)
):
    """Recompute this hand's aggregates from its stored occurrences.

    Reads every `instances` row of the hand ACROSS sources (statistics belong
    to the writer, not the plate, §12), groups them per `(glyph_key, variant)`
    and stores the per-anchor median + MAD hull for every group with at least
    `min_n` usable occurrences. The hand's previous aggregates are replaced
    wholesale, so a key that no longer qualifies disappears instead of going
    stale.

    The response carries the H1 Prüfstein per key: `laufform_dev_xh`, the mean
    anchor distance between the recomputed median and the stored Laufform
    (template variant 100) — the occurrence anchors are stored centered, so a
    faithful persistence layer reproduces the harvested running form.
    """
    instances = await InstanceRepository(db).list(hand_id=hand.id)
    rows = [
        {
            "glyph_key": i.glyph_key,
            "glyph": i.glyph,
            "variant": i.variant,
            "anchors": i.anchors,
            "position": i.position,
            "measurements": i.measurements or {},
        }
        for i in instances
    ]
    aggregates, skipped = aggregate_instances(rows, min_n=min_n)

    repo = AggregateRepository(db)
    deleted = await repo.delete_for_hand(hand.id)
    stored = await repo.upsert_many(
        [
            {"hand_id": hand.id, "glyph_key": glyph_key, "variant": variant, **agg}
            for (glyph_key, variant), agg in aggregates.items()
        ]
    )

    # Prüfstein: compare against the stored running forms of the hand's style.
    laufform_by_key: dict[str, list] = {}
    if hand.style_id:
        keys = sorted({glyph_key for glyph_key, _ in aggregates})
        templates = await TemplateRepository(db).get_many(
            hand.style_id, keys, variant=LAUFFORM_VARIANT, render_only=True
        )
        laufform_by_key = {t.glyph_key: t.anchors for t in templates}

    keys_out = [
        AggregateKeySummary(
            glyph_key=glyph_key,
            variant=variant,
            n_instances=agg["n_instances"],
            laufform_dev_xh=(
                laufform_deviation(agg["cluster_center"], laufform_by_key[glyph_key])
                if glyph_key in laufform_by_key
                else None
            ),
        )
        for (glyph_key, variant), agg in aggregates.items()
    ]
    return AggregateRebuildOut(hand_id=hand.id, stored=stored, deleted=deleted, skipped=skipped, keys=keys_out)


@router.post("/apply-laufform", response_model=AggregateApplyOut)
async def apply_laufform(hand: Hand = Depends(require_hand), db: AsyncSession = Depends(require_db)):
    """Derive the style's Laufform rows (templates variant 100) FROM this
    hand's stored aggregates — the last H1 step.

    Reads the STORED aggregates; it never recomputes them (that is the
    rebuild's job). The two stay separate on purpose: an aggregate is a
    statistic, a Laufform row is what `/write/word` renders, so promoting one
    into the other must be a deliberate act, not a side effect of a rebuild.

    Per aggregate the per-anchor median (`cluster_center`) becomes the running
    form's anchors — occurrence anchors are stored centered onto the chart
    template ("shapes, not placements"), so the median already sits in the
    chart row's frame and needs no re-registration. Everything else — widths,
    stroke topology, entry/exit/advance — comes from the chart template through
    the same `build_laufform_canonical` the manual harvest PUT uses, so the
    ductus prior carries over unchanged.

    Only base-variant (0) aggregates qualify: there is exactly ONE Laufform row
    per glyph_key, and feeding it from a variant-100 occurrence would let the
    row derive from itself. Every other aggregate is reported as skipped, as is
    a key without a chart template or with a deviating anchor count. Idempotent
    — a second run rewrites the same rows (upsert on the unique
    `(style_id, glyph_key, variant)`) and reports `laufform_dev_xh` 0.
    """
    if not hand.style_id:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail=f"hand {hand.id!r} has no style — nothing to write the Laufform into"
        )
    rows = await AggregateRepository(db).list(hand_id=hand.id)
    applied: list[AggregateApplyKeySummary] = []
    skipped: list[AggregateApplySkip] = []

    usable: list[Aggregate] = []
    for row in rows:
        if row.variant == LAUFFORM_VARIANT:
            # A derived row may never be its own input.
            skipped.append(AggregateApplySkip(glyph_key=row.glyph_key, variant=row.variant, reason="laufform_variant"))
        elif row.variant != 0:
            skipped.append(AggregateApplySkip(glyph_key=row.glyph_key, variant=row.variant, reason="non_base_variant"))
        else:
            usable.append(row)

    repo = TemplateRepository(db)
    keys = sorted({row.glyph_key for row in usable})
    # Both sides in one query each: the chart rows supply everything but the
    # anchors, the stored Laufform rows the pre-write Prüfstein distance.
    base_by_key = {t.glyph_key: t for t in await repo.get_many(hand.style_id, keys, variant=0, render_only=True)}
    laufform_by_key = {
        t.glyph_key: t for t in await repo.get_many(hand.style_id, keys, variant=LAUFFORM_VARIANT, render_only=True)
    }

    for row in usable:
        base = base_by_key.get(row.glyph_key)
        if base is None:
            skipped.append(AggregateApplySkip(glyph_key=row.glyph_key, variant=row.variant, reason="no_base_template"))
            continue
        median = [list(a) for a in row.cluster_center or []]
        if len(median) != len(base.anchors):
            # Same contract as the manual PUT: the chart row stays the ductus
            # prior, so the anchor lists must correspond one-to-one.
            skipped.append(AggregateApplySkip(glyph_key=row.glyph_key, variant=row.variant, reason="anchor_count"))
            continue
        # Snapshot the PRE-write anchors: the upsert re-selects with
        # `populate_existing`, which overwrites this very row object with what
        # was just written — reading it afterwards would always measure 0.
        stored_laufform = laufform_by_key.get(row.glyph_key)
        prev_anchors = [list(a) for a in stored_laufform.anchors] if stored_laufform is not None else None
        canonical = build_laufform_canonical(
            base, median, {"derived_from": "hand-aggregate", "hand_id": hand.id, "n_occurrences": row.n_instances}
        )
        await repo.upsert(
            hand.style_id,
            row.glyph_key,
            canonical,
            variant=LAUFFORM_VARIANT,
            # The chart the ductus prior came from — the aggregate itself spans
            # every source the hand was observed on, so it names no single one.
            provenance_source_id=base.provenance_source_id,
        )
        applied.append(
            AggregateApplyKeySummary(
                glyph_key=row.glyph_key,
                variant=row.variant,
                n_instances=row.n_instances,
                laufform_dev_xh=(laufform_deviation(median, prev_anchors) if prev_anchors is not None else None),
                created=prev_anchors is None,
            )
        )

    # Commit before invalidating the pooled-nib cache — see templates.post_trace.
    await db.commit()
    if applied:
        invalidate_pooled_style(hand.style_id)
    # The skips are collected in two passes (variants, then per-key) — sort them
    # back into the aggregate listing's order so the report reads as one list.
    skipped.sort(key=lambda s: (s.glyph_key, s.variant))
    return AggregateApplyOut(hand_id=hand.id, style_id=hand.style_id, applied=applied, skipped=skipped)
