"""Bbox CRUD per source."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db, require_source
from api.schemas import BboxIn, BboxOut, GuideConfig
from core.database import Bbox, BboxRepository, Source


router = APIRouter(prefix="/sources/{source_id}/bboxes", tags=["bboxes"])


def _to_out(bbox: Bbox) -> BboxOut:
    return BboxOut(
        glyph_key=bbox.glyph_key,
        y0=bbox.y0,
        y1=bbox.y1,
        x0=bbox.x0,
        x1=bbox.x1,
        mask_strokes=list(bbox.mask_strokes),
        baseline_y=bbox.baseline_y,
        midband_y=bbox.midband_y,
        n_anchors=bbox.n_anchors,
        guides=GuideConfig(**(bbox.guides or {})),
        locked=bool(bbox.locked),
        split=bool(bbox.split),
    )


@router.get("", response_model=list[BboxOut])
async def list_bboxes(source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)):
    rows = await BboxRepository(db).list(source.id)
    return [_to_out(b) for b in rows]


@router.get("/{glyph_key}", response_model=BboxOut)
async def get_bbox(glyph_key: str, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)):
    bbox = await BboxRepository(db).get(source.id, glyph_key)
    if bbox is None:
        raise HTTPException(404, detail=f"bbox not set for {glyph_key!r}")
    return _to_out(bbox)


@router.put("/{glyph_key}", response_model=BboxOut, dependencies=[Depends(require_admin)])
async def put_bbox(
    glyph_key: str, payload: BboxIn, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    if payload.baseline_y <= payload.midband_y:
        raise HTTPException(422, detail="baseline_y must be greater than midband_y (baseline is below midband)")
    repo = BboxRepository(db)
    # `guides`, `locked` and `split` are optional: when the client omits one,
    # keep whatever is already stored (a plain bbox/calibration save must not
    # wipe the guide lines, and toggling the lock or split must not require
    # resending guides).
    existing = None
    if payload.guides is not None:
        guides = payload.guides.model_dump()
    else:
        existing = await repo.get(source.id, glyph_key)
        guides = existing.guides if existing is not None else {}
    if payload.locked is not None:
        locked = payload.locked
    else:
        if existing is None:
            existing = await repo.get(source.id, glyph_key)
        locked = bool(existing.locked) if existing is not None else False
    if payload.split is not None:
        split = payload.split
    else:
        if existing is None:
            existing = await repo.get(source.id, glyph_key)
        split = bool(existing.split) if existing is not None else False
    bbox = await repo.upsert(
        source.id,
        glyph_key,
        y0=payload.y0,
        y1=payload.y1,
        x0=payload.x0,
        x1=payload.x1,
        mask_strokes=[m.model_dump() for m in payload.mask_strokes],
        baseline_y=payload.baseline_y,
        midband_y=payload.midband_y,
        n_anchors=payload.n_anchors,
        guides=guides,
        locked=locked,
        split=split,
    )
    return _to_out(bbox)


@router.delete("/{glyph_key}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_bbox(glyph_key: str, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)):
    await BboxRepository(db).delete(source.id, glyph_key)
