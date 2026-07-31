"""Occurrence endpoints (handmodell plan H1/H2): per-glyph and per-pair rows.

The statistics layer's write path: the laufform harvest stores every clean
per-occurrence M4 fit (`instances`), the pairlab harvest every dissected
letter join (`pair_instances`) — occurrences, not just medians, per the
2026-07-31 decision. Reads are public like the template lists (the data is
derived from PD specimens); writes are admin-gated batches that get-or-create
the writer's `hands` row in the same request. Nothing here affects rendering —
the composer keeps reading templates/laufform variants and approved
`glyph_pairs` only.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db, require_source
from api.schemas import BatchStoreOut, HandIn, InstanceBatchIn, InstanceOut, PairInstanceBatchIn, PairInstanceOut
from core.database import (
    HandRepository,
    Instance,
    InstanceRepository,
    PairInstance,
    PairInstanceRepository,
    Source,
    TemplateRepository,
)
from core.shaping import is_registry_glyph_key


router = APIRouter(prefix="/sources/{source_id}", tags=["instances"])


def _reject_unknown_keys(keys: set[str]) -> None:
    """Occurrence keys must be registry glyphs — a typo'd key would store fine
    but never join up with a template or a shaped slot."""
    unknown = sorted(k for k in keys if not is_registry_glyph_key(k))
    if unknown:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"not registry glyphs: {', '.join(map(repr, unknown))}"
        )


async def _upsert_hand(db: AsyncSession, hand: HandIn, style_id: str) -> str:
    row = await HandRepository(db).upsert(hand.id, style_id=style_id, label=hand.label, era=hand.era, note=hand.note)
    return row.id


def _instance_out(row: Instance) -> InstanceOut:
    return InstanceOut(
        glyph_key=row.glyph_key,
        glyph=row.glyph,
        position=row.position,
        variant=row.variant,
        hand_id=row.hand_id,
        y0=row.y0,
        y1=row.y1,
        x0=row.x0,
        x1=row.x1,
        anchors=[list(a) for a in row.anchors],
        half_widths=list(row.half_widths or []),
        measurements=dict(row.measurements or {}),
    )


@router.get("/instances", response_model=list[InstanceOut])
async def list_instances(
    glyph_key: str | None = None, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    """The stored glyph occurrences of this source (optionally one glyph's).
    Uncached like /templates: the harvest writes and expects fresh rows."""
    rows = await InstanceRepository(db).list(source_id=source.id, glyph_key=glyph_key)
    return [_instance_out(r) for r in rows]


@router.put("/instances", response_model=BatchStoreOut, dependencies=[Depends(require_admin)])
async def put_instances(
    payload: InstanceBatchIn, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    _reject_unknown_keys({item.glyph_key for item in payload.items})
    hand_id = await _upsert_hand(db, payload.hand, source.style_id)
    repo = InstanceRepository(db)
    deleted = await repo.delete_for_source(source.id) if payload.replace else 0
    # Resolve each occurrence's canonical (base-variant) template in one query;
    # a not-yet-authored glyph stores with template_id NULL.
    templates = await TemplateRepository(db).get_many(
        source.style_id, sorted({i.glyph_key for i in payload.items}), variant=0, render_only=True
    )
    template_id_by_key = {t.glyph_key: t.id for t in templates}
    # Within one batch the ON CONFLICT upsert must not see the same identity
    # twice ("cannot affect row a second time") — last write wins.
    by_identity: dict[tuple, dict] = {}
    for item in payload.items:
        row = {
            "source_id": source.id,
            "hand_id": hand_id,
            "template_id": template_id_by_key.get(item.glyph_key),
            "glyph_key": item.glyph_key,
            "glyph": item.glyph,
            "position": item.position,
            "variant": item.variant,
            "y0": item.y0,
            "y1": item.y1,
            "x0": item.x0,
            "x1": item.x1,
            "anchors": [list(a) for a in item.anchors],
            "half_widths": item.half_widths,
            "raw_path": [],
            "measurements": item.measurements,
        }
        by_identity[(item.glyph, item.position, item.variant, item.y0, item.x0)] = row
    stored = await repo.upsert_many(list(by_identity.values()))
    return BatchStoreOut(hand_id=hand_id, stored=stored, deleted=deleted)


@router.delete("/instances", dependencies=[Depends(require_admin)])
async def delete_instances(source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)):
    deleted = await InstanceRepository(db).delete_for_source(source.id)
    return {"deleted": deleted}


def _pair_instance_out(row: PairInstance) -> PairInstanceOut:
    return PairInstanceOut(
        left_key=row.left_key,
        right_key=row.right_key,
        kind=row.kind,
        specimen_id=row.specimen_id,
        slot=row.slot,
        hand_id=row.hand_id,
        geometry=row.geometry,
        measurements=dict(row.measurements or {}),
    )


@router.get("/pair-instances", response_model=list[PairInstanceOut])
async def list_pair_instances(
    left_key: str | None = None,
    right_key: str | None = None,
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    """The stored join occurrences of this source (optionally one pair's)."""
    rows = await PairInstanceRepository(db).list(source_id=source.id, left_key=left_key, right_key=right_key)
    return [_pair_instance_out(r) for r in rows]


@router.put("/pair-instances", response_model=BatchStoreOut, dependencies=[Depends(require_admin)])
async def put_pair_instances(
    payload: PairInstanceBatchIn, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    _reject_unknown_keys({i.left_key for i in payload.items} | {i.right_key for i in payload.items})
    hand_id = await _upsert_hand(db, payload.hand, source.style_id)
    repo = PairInstanceRepository(db)
    deleted = await repo.delete_for_source(source.id) if payload.replace else 0
    by_identity: dict[tuple, dict] = {}
    for item in payload.items:
        row = {
            "source_id": source.id,
            "hand_id": hand_id,
            "left_key": item.left_key,
            "right_key": item.right_key,
            "kind": item.kind,
            "specimen_id": item.specimen_id,
            "slot": item.slot,
            "geometry": item.geometry.model_dump(),
            "measurements": item.measurements,
        }
        by_identity[(item.kind, item.specimen_id, item.slot)] = row
    stored = await repo.upsert_many(list(by_identity.values()))
    return BatchStoreOut(hand_id=hand_id, stored=stored, deleted=deleted)


@router.delete("/pair-instances", dependencies=[Depends(require_admin)])
async def delete_pair_instances(source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)):
    deleted = await PairInstanceRepository(db).delete_for_source(source.id)
    return {"deleted": deleted}
