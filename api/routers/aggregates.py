"""Per-hand aggregate endpoints (Stufenplan H1): read + rebuild.

The statistics layer's second stage: `instances` holds every clean occurrence,
this router condenses them per `(glyph_key, variant)` into the per-anchor
median (the running form), its spread and the pooled layer-1 statistics.

Unlike the occurrence reads, the WHOLE router is admin-gated: an aggregate is
learned geometry — the median form of a hand — and therefore part of the
open-core moat (quellen-und-rechte.md §5), not public product surface. Nothing
here affects rendering; the composer keeps reading templates and approved
`glyph_pairs` only. Deriving the variant-100 Laufform FROM the aggregate is a
later step; the rebuild only reports how far the two are apart (the H1
Prüfstein).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db
from api.schemas import AggregateKeySummary, AggregateOut, AggregateRebuildOut
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
