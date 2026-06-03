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
        excludes=list(bbox.excludes),
        baseline_y=bbox.baseline_y,
        midband_y=bbox.midband_y,
        n_anchors=bbox.n_anchors,
        guides=GuideConfig(**(bbox.guides or {})),
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
    bbox = await repo.upsert(
        source.id,
        glyph_key,
        y0=payload.y0,
        y1=payload.y1,
        x0=payload.x0,
        x1=payload.x1,
        excludes=[e.model_dump() for e in payload.excludes],
        baseline_y=payload.baseline_y,
        midband_y=payload.midband_y,
        n_anchors=payload.n_anchors,
        guides=payload.guides.model_dump(),
    )
    return _to_out(bbox)


@router.delete("/{glyph_key}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_bbox(glyph_key: str, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)):
    await BboxRepository(db).delete(source.id, glyph_key)
