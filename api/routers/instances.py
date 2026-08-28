"""Occurrence endpoints (handmodell plan H1/H2): per-glyph and per-pair rows.

The statistics layer's write path: the laufform harvest stores every clean
per-occurrence M4 fit (`instances`), the pairlab harvest every dissected
letter join (`pair_instances`) — occurrences, not just medians, per the
2026-07-31 decision. Reads AND writes are admin-gated (since 2026-08-28):
an occurrence is a measured fit over the authored templates — the learned
dataset the README reserves (quellen-und-rechte.md §5) — and no public page
ever consumed one; the readers are the workbench, the harvests and the
fixture/snapshot tools, all of which carry the admin token. The write batches
get-or-create the writer's `hands` row in the same request. Nothing here
affects rendering — the composer keeps reading templates/laufform variants
and approved `glyph_pairs` only.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db, require_source
from api.schemas import (
    BatchStoreOut,
    HandIn,
    InstanceBatchIn,
    InstanceOut,
    PairInstanceBatchIn,
    PairInstanceOut,
    WordInstanceBatchIn,
    WordInstanceOut,
)
from core.database import (
    HandRepository,
    Instance,
    InstanceRepository,
    PairInstance,
    PairInstanceRepository,
    Source,
    TemplateRepository,
    WordInstance,
    WordInstanceRepository,
)
from core.shaping import expected_glyph_key, is_registry_glyph_key


router = APIRouter(prefix="/sources/{source_id}", tags=["instances"])


def _reject_unknown_keys(keys: set[str]) -> None:
    """Occurrence keys must be registry glyphs — a typo'd key would store fine
    but never join up with a template or a shaped slot."""
    unknown = sorted(k for k in keys if not is_registry_glyph_key(k))
    if unknown:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"not registry glyphs: {', '.join(map(repr, unknown))}"
        )


def _reject_key_identity_mismatch(glyph_key: str, glyph: str) -> None:
    """Backstop: an item's glyph_key and glyph must agree per the registry.

    The occurrence identity conflicts on `glyph` (uq_instance_loc) while the
    template link resolves by `glyph_key` — a mismatched pair would store an
    inconsistent row linked to the wrong canonical. Same contract as the
    templates write path."""
    expected = expected_glyph_key(glyph)
    if expected is not None and expected != glyph_key:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"glyph_key {glyph_key!r} does not match glyph {glyph!r} (expected {expected!r})",
        )


async def _upsert_hand(db: AsyncSession, hand: HandIn, style_id: str) -> str:
    repo = HandRepository(db)
    existing = await repo.get(hand.id)
    if existing is not None and existing.style_id not in (None, style_id):
        # A hand is registered under the style it was observed writing — a
        # reused id across styles would silently reassign the hand and detach
        # its existing occurrences' semantics.
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"hand {hand.id!r} belongs to style {existing.style_id!r}, not {style_id!r}",
        )
    row = await repo.upsert(hand.id, style_id=style_id, label=hand.label, era=hand.era, note=hand.note)
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


@router.get("/instances", response_model=list[InstanceOut], dependencies=[Depends(require_admin)])
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
    for item in payload.items:
        _reject_key_identity_mismatch(item.glyph_key, item.glyph)
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


@router.get("/pair-instances", response_model=list[PairInstanceOut], dependencies=[Depends(require_admin)])
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


def _word_instance_out(row: WordInstance) -> WordInstanceOut:
    return WordInstanceOut(
        kind=row.kind,
        specimen_id=row.specimen_id,
        word=row.word,
        slots=list(row.slots),
        strokes=row.strokes,
        provenance=row.provenance,
        hand_id=row.hand_id,
        measurements=dict(row.measurements or {}),
    )


@router.get("/word-instances", response_model=list[WordInstanceOut], dependencies=[Depends(require_admin)])
async def list_word_instances(
    specimen_id: str | None = None,
    word: str | None = None,
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    """The stored word traces of this source — all of them, one specimen's
    (`?specimen_id=wenn-2`), or every occurrence of one word text
    (`?word=wenn`). The matching crop comes from
    `GET …/word-samples/{specimen_id}/crop`."""
    rows = await WordInstanceRepository(db).list(source_id=source.id, specimen_id=specimen_id, word=word)
    return [_word_instance_out(r) for r in rows]


@router.put("/word-instances", response_model=BatchStoreOut, dependencies=[Depends(require_admin)])
async def put_word_instances(
    payload: WordInstanceBatchIn, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    _reject_unknown_keys({key for item in payload.items for key in item.slots})
    hand_id = await _upsert_hand(db, payload.hand, source.style_id)
    repo = WordInstanceRepository(db)
    # Authored rows are manual admin work — a traced batch (harvest) never
    # touches them: replace spares them, and traced upserts skip their identity.
    authored = await repo.authored_identities(source.id)
    deleted = await repo.delete_for_source(source.id, include_authored=False) if payload.replace else 0
    by_identity: dict[tuple, dict] = {}
    skipped = 0
    for item in payload.items:
        identity = (item.kind, item.specimen_id)
        if item.provenance == "traced" and identity in authored:
            skipped += 1
            continue
        # In-batch precedence mirrors the stored contract: an authored item is
        # never displaced by a later traced one for the same identity.
        prior = by_identity.get(identity)
        if prior is not None and prior["provenance"] == "authored" and item.provenance == "traced":
            skipped += 1
            continue
        by_identity[identity] = {
            "source_id": source.id,
            "hand_id": hand_id,
            "kind": item.kind,
            "specimen_id": item.specimen_id,
            "word": item.word,
            "slots": item.slots,
            "strokes": item.strokes,
            "provenance": item.provenance,
            "measurements": item.measurements,
        }
    stored = await repo.upsert_many(list(by_identity.values()))
    return BatchStoreOut(hand_id=hand_id, stored=stored, deleted=deleted, skipped=skipped)


@router.delete("/word-instances", dependencies=[Depends(require_admin)])
async def delete_word_instances(
    include_authored: bool = False, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    """Wipe the source's word traces. Authored rows survive unless
    `?include_authored=true` — deleting manual work is an explicit decision."""
    deleted = await WordInstanceRepository(db).delete_for_source(source.id, include_authored=include_authored)
    return {"deleted": deleted}
