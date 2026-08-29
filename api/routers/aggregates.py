"""Per-hand aggregate endpoints — the statistics layer over the occurrences.

Two routers, one per occurrence level:

* `router` (Stufenplan H1, `/hands/{hand_id}/aggregates`): read + rebuild +
  apply. `instances` holds every clean glyph occurrence, the rebuild condenses
  them per `(glyph_key, variant)` into the per-anchor median (the running
  form), its spread and the pooled layer-1 statistics.
* `pair_router` (Stufenplan H2, `/hands/{hand_id}/pair-aggregates`): read +
  rebuild. `pair_instances` holds every dissected letter join, the rebuild
  condenses them per `(left_key, right_key)` into the median placement offset,
  the median connector centerline and the pooled dissection QC.

Unlike the occurrence reads, BOTH routers are admin-gated end to end: an
aggregate is learned geometry — the median form of a hand — and therefore part
of the open-core moat (quellen-und-rechte.md §5), not public product surface.
The reads and the rebuilds affect no rendering; the composer keeps reading
templates and approved `glyph_pairs` only. `POST …/apply-laufform` closes H1's
loop and IS a render-affecting write — the variant-100 Laufform row becomes a
DERIVATION from the stored aggregate instead of the harvest's end product —
which is exactly why it is its own deliberate step and never a side effect of
the rebuild. The pair side has no such counterpart on purpose (see below).
"""

from typing import Annotated

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
    PairAggregateKeySummary,
    PairAggregateOut,
    PairAggregateRebuildOut,
)
from core.aggregate import LAUFFORM_MIN_OCCURRENCES, aggregate_instances, aggregate_pair_instances, laufform_deviation
from core.database import (
    LAUFFORM_VARIANT,
    Aggregate,
    AggregateRepository,
    Hand,
    HandRepository,
    InstanceRepository,
    PairAggregate,
    PairAggregateRepository,
    PairInstanceRepository,
    Template,
    TemplateRepository,
)


router = APIRouter(prefix="/hands/{hand_id}/aggregates", tags=["aggregates"], dependencies=[Depends(require_admin)])


def _written_anchors(base: Template | None, median: list[list[float]]) -> list[list[float]]:
    """The anchors `apply-laufform` WOULD write for this median.

    The Prüfstein (list + rebuild) asks whether the stored running form is what
    this aggregate would write — so the median goes through the same canonical
    builder the apply step uses, its end blend (when one is enabled) included;
    against the raw median every blended row would carry a permanent end-piece
    residue and 0 would never read again. Without a chart row, or with a
    deviating anchor count, the apply step skips the key and the raw median is
    the only comparable.
    """
    if base is None or len(base.anchors) != len(median):
        return median
    return build_laufform_canonical(base, median, {})["anchors"]


pair_router = APIRouter(
    prefix="/hands/{hand_id}/pair-aggregates", tags=["aggregates"], dependencies=[Depends(require_admin)]
)


async def require_hand(hand_id: str, db: AsyncSession = Depends(require_db)) -> Hand:
    """Load the writer row this rebuild aggregates over (404 if unknown)."""
    hand = await HandRepository(db).get(hand_id)
    if hand is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"unknown hand {hand_id!r}")
    return hand


def _to_out(
    row: Aggregate, laufform_anchors: list[list[float]] | None = None, base: Template | None = None
) -> AggregateOut:
    median = [list(a) for a in row.cluster_center or []]
    return AggregateOut(
        glyph_key=row.glyph_key,
        glyph=row.glyph,
        variant=row.variant,
        cluster_center=median,
        hull=dict(row.hull or {}),
        mean_stats=dict(row.mean_stats or {}),
        n_instances=row.n_instances,
        laufform_anchors=laufform_anchors,
        laufform_dev_xh=(
            laufform_deviation(_written_anchors(base, median), laufform_anchors)
            if laufform_anchors is not None
            else None
        ),
    )


@router.get("", response_model=list[AggregateOut])
async def list_aggregates(hand: Hand = Depends(require_hand), db: AsyncSession = Depends(require_db)):
    """This hand's stored aggregates, by glyph_key. Uncached like the
    occurrence reads: the rebuild writes and expects fresh rows.

    Each row carries the CURRENTLY RENDERED running form beside its median:
    `laufform_anchors` (the stored template variant 100, null when the glyph
    has none yet) and `laufform_dev_xh`, their mean anchor distance in x-height
    units. Without those, "is what the engine writes still what the statistics
    say?" was answerable only by running a rebuild or an apply — i.e. only by
    doing something — which is what left `apply-laufform` a blind curl call
    (issue #270). A plain read answers it now, and 0 means the two agree.
    """
    rows = await AggregateRepository(db).list(hand_id=hand.id)
    # Two queries for the whole listing (the stored running forms and the
    # chart rows the Prüfstein's builder needs), over the BASE-variant keys
    # only — non-base aggregates never get a distance; a hand without a style
    # has no templates to compare against, so the freshness columns stay null.
    laufform_by_key: dict[str, list[list[float]]] = {}
    chart_by_key: dict[str, Template] = {}
    keys = sorted({r.glyph_key for r in rows if r.variant == 0})
    if hand.style_id and keys:
        repo = TemplateRepository(db)
        laufform_by_key = {
            t.glyph_key: [list(a) for a in t.anchors]
            for t in await repo.get_many(hand.style_id, keys, variant=LAUFFORM_VARIANT, render_only=True)
        }
        # The chart rows feed the Prüfstein's canonical builder (_written_anchors).
        chart_by_key = {t.glyph_key: t for t in await repo.get_many(hand.style_id, keys, variant=0, render_only=True)}
    # Only a BASE-variant aggregate is a Laufform source (the apply step skips
    # every other one), so only there does a comparison mean anything.
    return [
        _to_out(r, laufform_by_key.get(r.glyph_key) if r.variant == 0 else None, chart_by_key.get(r.glyph_key))
        for r in rows
    ]


@router.post("/rebuild", response_model=AggregateRebuildOut)
async def rebuild_aggregates(
    min_n: int = Query(1, ge=1), hand: Hand = Depends(require_hand), db: AsyncSession = Depends(require_db)
):
    """Recompute this hand's aggregates from its stored occurrences.

    Reads every `instances` row of the hand ACROSS sources (statistics belong
    to the writer, not the plate, §12), groups them per `(glyph_key, variant)`
    and stores the per-anchor median + MAD hull for every group with at least
    `min_n` usable occurrences. The hand's previous aggregates are replaced
    wholesale, so a key that no longer qualifies disappears instead of going
    stale.

    `min_n` defaults to 1, like the pair rebuild and for a related reason
    (issue #273): SEEING a median is measurement — nothing renders from it — so
    withholding the only evidence there is helps nobody, and nearly every
    capital stays below four occurrences on the 1922 plates. The caution the
    old default of 4 encoded belongs one step further on, at `apply-laufform`,
    where a human reads `n_instances` per glyph and presses a button. The gate
    itself stays in `core/aggregate.py` and keeps counting `below_min_n` for
    whatever threshold is passed.

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

    # Prüfstein: compare against the stored running forms of the hand's style
    # — through the canonical builder, see _written_anchors.
    laufform_by_key: dict[str, list] = {}
    chart_by_key: dict[str, Template] = {}
    if hand.style_id:
        keys = sorted({glyph_key for glyph_key, _ in aggregates})
        repo = TemplateRepository(db)
        templates = await repo.get_many(hand.style_id, keys, variant=LAUFFORM_VARIANT, render_only=True)
        laufform_by_key = {t.glyph_key: t.anchors for t in templates}
        chart_by_key = {t.glyph_key: t for t in await repo.get_many(hand.style_id, keys, variant=0, render_only=True)}

    keys_out = [
        AggregateKeySummary(
            glyph_key=glyph_key,
            variant=variant,
            n_instances=agg["n_instances"],
            laufform_dev_xh=(
                laufform_deviation(
                    _written_anchors(chart_by_key.get(glyph_key), agg["cluster_center"]), laufform_by_key[glyph_key]
                )
                if glyph_key in laufform_by_key
                else None
            ),
        )
        for (glyph_key, variant), agg in aggregates.items()
    ]
    return AggregateRebuildOut(hand_id=hand.id, stored=stored, deleted=deleted, skipped=skipped, keys=keys_out)


@router.post("/apply-laufform", response_model=AggregateApplyOut)
async def apply_laufform(
    # Annotated rather than a plain default: a repeated query parameter needs a
    # list annotation, and a call in a list-typed default is exactly what B008
    # forbids.
    glyph_keys: Annotated[list[str] | None, Query()] = None,
    min_occurrences: int = Query(LAUFFORM_MIN_OCCURRENCES, ge=1),
    hand: Hand = Depends(require_hand),
    db: AsyncSession = Depends(require_db),
):
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

    `glyph_keys` narrows the write to the named keys (repeatable query
    parameter, e.g. `?glyph_keys=a&glyph_keys=n`); absent, every stored
    aggregate is a candidate as before. The selection exists because the
    aggregate gate is `min_n = 1` (issue #273): with singletons in the
    statistics layer, "apply everything or nothing" would force a hand's
    one-occurrence idiosyncrasies into the writing path together with its
    well-attested medians. Every key the selection left out is reported back in
    `excluded`, so the response says what was NOT written just as plainly as
    what was.

    `min_occurrences` is the floor UNDER that selection, and it is the endpoint's
    own judgement rather than the request's: an aggregate thinner than
    `core.aggregate.LAUFFORM_MIN_OCCURRENCES` is reported as
    `below_min_occurrences` and left alone, however it was named — but LAST in
    the triage: a key whose variant, missing chart row or anchor count already
    blocks the derivation keeps that reason, because those are what to act on
    first. The caution
    used to live only in the dialog's proposed selection — which is exactly why
    it did not hold: a re-apply names the keys that ALREADY have a Laufform row,
    so a key that once earned one from a word harvest kept being re-derived from
    however thin an aggregate it had since acquired. That is how the Sütterlin
    capital S came to be written from two occurrences, spike and all. Same
    doctrine as the `work_items` protocol (optimierungs-werkbank.md §5): a rule
    the API ENFORCES rather than trusts a client to apply. Lowering the floor
    stays possible for the human who means it (`?min_occurrences=1`), and then
    the request itself says so.
    """
    if not hand.style_id:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail=f"hand {hand.id!r} has no style — nothing to write the Laufform into"
        )
    rows = await AggregateRepository(db).list(hand_id=hand.id)
    applied: list[AggregateApplyKeySummary] = []
    skipped: list[AggregateApplySkip] = []
    # None = no selection = every aggregate is a candidate (the pre-#273
    # behaviour); an EMPTY selection is a deliberate "write nothing" and is not
    # silently widened back to all.
    selection = None if glyph_keys is None else set(glyph_keys)
    excluded: set[str] = set()

    usable: list[Aggregate] = []
    for row in rows:
        if selection is not None and row.glyph_key not in selection:
            # Deselected is not the same as unusable: it never reaches the
            # variant/topology triage below, and it is reported on its own.
            excluded.add(row.glyph_key)
        elif row.variant == LAUFFORM_VARIANT:
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
        if row.n_instances < min_occurrences:
            # LAST in the whole triage, after the variant AND the topology
            # questions: every other reason names something that would block the
            # derivation whatever the occurrence count is, and the report exists
            # to say what to DO — "author the chart row" and "the anchor counts
            # disagree" are actionable, "harvest more occurrences" only becomes
            # the true next step once the derivable ones are answered.
            skipped.append(
                AggregateApplySkip(
                    glyph_key=row.glyph_key,
                    variant=row.variant,
                    reason="below_min_occurrences",
                    n_instances=row.n_instances,
                )
            )
            continue
        # Snapshot the PRE-write anchors: the upsert re-selects with
        # `populate_existing`, which overwrites this very row object with what
        # was just written — reading it afterwards would always measure 0.
        stored_laufform = laufform_by_key.get(row.glyph_key)
        prev_anchors = [list(a) for a in stored_laufform.anchors] if stored_laufform is not None else None
        canonical = build_laufform_canonical(
            base, median, {"derived_from": "hand-aggregate", "hand_id": hand.id, "n_occurrences": row.n_instances}
        )
        # The pre-write distance compares what is ABOUT TO BE WRITTEN with what
        # stands — the canonical anchors, the builder's end blend (when one is
        # enabled) included, not the raw median: a re-apply of an unchanged
        # aggregate then reads 0 as promised.
        written_anchors = [list(a) for a in canonical["anchors"]]
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
                laufform_dev_xh=(
                    laufform_deviation(written_anchors, prev_anchors) if prev_anchors is not None else None
                ),
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
    return AggregateApplyOut(
        hand_id=hand.id, style_id=hand.style_id, applied=applied, skipped=skipped, excluded=sorted(excluded)
    )


# ------------------------------------------------- pair aggregates (Stufenplan H2)


def _pair_to_out(row: PairAggregate) -> PairAggregateOut:
    return PairAggregateOut(
        left_key=row.left_key,
        right_key=row.right_key,
        offset_center=list(row.offset_center or []),
        connector_center=[list(p) for p in row.connector_center or []],
        hull=dict(row.hull or {}),
        mean_stats=dict(row.mean_stats or {}),
        n_instances=row.n_instances,
    )


@pair_router.get("", response_model=list[PairAggregateOut])
async def list_pair_aggregates(
    left_key: str | None = None,
    right_key: str | None = None,
    hand: Hand = Depends(require_hand),
    db: AsyncSession = Depends(require_db),
):
    """This hand's stored pair aggregates, by (left_key, right_key). Uncached
    like the glyph read: the rebuild writes and expects fresh rows.

    `left_key` and `right_key` narrow the listing — together to exactly one
    transition, singly to every join of one letter: the compare-tab and report
    consumers ask for a single join's statistics, not the hand's whole matrix.
    """
    rows = await PairAggregateRepository(db).list(hand_id=hand.id, left_key=left_key, right_key=right_key)
    return [_pair_to_out(r) for r in rows]


@pair_router.post("/rebuild", response_model=PairAggregateRebuildOut)
async def rebuild_pair_aggregates(
    min_n: int = Query(1, ge=1), hand: Hand = Depends(require_hand), db: AsyncSession = Depends(require_db)
):
    """Recompute this hand's pair aggregates from its stored join occurrences.

    Reads every `pair_instances` row of the hand ACROSS sources (statistics
    belong to the writer, not the plate, §12), groups them per
    `(left_key, right_key)` — pooling the word plates and the pair drills, the
    same hand writing the same transition — and stores the median placement
    offset plus the per-point median of the arc-length-resampled connector
    centerlines, each with its MAD hull. The hand's previous pair aggregates are
    replaced wholesale, so a pair that no longer qualifies disappears instead of
    going stale.

    `min_n` defaults to 1 because pairs are sparse: most transitions are
    attested by a handful of occurrences and some by exactly one, which is still
    the only measured truth about them. `n_instances` rides along on every row
    so consumers can weigh it.

    The response reports `gen_chamfer_mean` per pair — the harvest's
    „gemessen vs. komponiert" distance between the GENERATED connector and the
    specimen skeleton, the audit number this layer exists for.
    """
    occurrences = await PairInstanceRepository(db).list(hand_id=hand.id)
    rows = [
        {
            "left_key": p.left_key,
            "right_key": p.right_key,
            "kind": p.kind,
            "specimen_id": p.specimen_id,
            "geometry": p.geometry or {},
            "measurements": p.measurements or {},
        }
        for p in occurrences
    ]
    aggregates, skipped = aggregate_pair_instances(rows, min_n=min_n)

    repo = PairAggregateRepository(db)
    deleted = await repo.delete_for_hand(hand.id)
    stored = await repo.upsert_many(
        [
            {"hand_id": hand.id, "left_key": left_key, "right_key": right_key, **agg}
            for (left_key, right_key), agg in aggregates.items()
        ]
    )

    # No `apply` counterpart here, deliberately: the pair statistics are
    # READ-ONLY by design (Stufenplan H2). `glyph_pairs` stays the sparse
    # verbatim override the admin approves per pair, the §4 generator stays the
    # default for everything else — a median join written back into the writing
    # path would be exactly the bigram database architektur.md §2 rejected. The
    # first consumers are report surfaces (wordbench audit columns, the
    # comparison tab's „gemessen vs. komponiert").
    pairs_out = [
        PairAggregateKeySummary(
            left_key=left_key,
            right_key=right_key,
            n_instances=agg["n_instances"],
            gen_chamfer_mean=agg["mean_stats"].get("gen_chamfer", {}).get("mean"),
        )
        for (left_key, right_key), agg in sorted(aggregates.items())
    ]
    return PairAggregateRebuildOut(hand_id=hand.id, stored=stored, deleted=deleted, skipped=skipped, pairs=pairs_out)
