"""Bbox CRUD per source."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db, require_source
from api.schemas import BboxIn, BboxOut, GuideConfig
from core.database import Bbox, BboxRepository, Source
from core.pipeline import DEFAULT_N_ANCHORS


router = APIRouter(prefix="/sources/{source_id}/bboxes", tags=["bboxes"])


def _to_out(bbox: Bbox) -> BboxOut:
    return BboxOut(
        glyph_key=bbox.glyph_key,
        y0=bbox.y0,
        y1=bbox.y1,
        x0=bbox.x0,
        x1=bbox.x1,
        mask_strokes=list(bbox.mask_strokes),
        ink_strokes=list(bbox.ink_strokes),
        patches=list(bbox.patches),
        baseline_y=bbox.baseline_y,
        midband_y=bbox.midband_y,
        n_anchors=bbox.n_anchors,
        guides=GuideConfig(**(bbox.guides or {})),
        locked=bool(bbox.locked),
        split=bool(bbox.split),
        fill_holes_max_area=int(bbox.fill_holes_max_area),
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
    # `guides`, `locked`, `split`, `n_anchors` and `fill_holes_max_area` are all
    # optional: when the client omits one, keep whatever is already stored (a
    # plain bbox/calibration save must not wipe the guide lines, silently rewrite
    # the anchor count, or require resending unrelated fields). Load the existing
    # row once, only if at least one of them is actually omitted.
    optionals = (payload.guides, payload.locked, payload.split, payload.n_anchors, payload.fill_holes_max_area)
    existing = await repo.get(source.id, glyph_key) if any(v is None for v in optionals) else None

    def coalesce(value, attr, default, cast):
        """Prefer the payload value; else fall back to the stored row, else the default."""
        if value is not None:
            return value
        return cast(getattr(existing, attr)) if existing is not None else default

    guides = payload.guides.model_dump() if payload.guides is not None else coalesce(None, "guides", {}, dict)
    locked = coalesce(payload.locked, "locked", False, bool)
    split = coalesce(payload.split, "split", False, bool)
    n_anchors = coalesce(payload.n_anchors, "n_anchors", DEFAULT_N_ANCHORS, int)
    fill_holes_max_area = coalesce(payload.fill_holes_max_area, "fill_holes_max_area", 0, int)
    bbox = await repo.upsert(
        source.id,
        glyph_key,
        y0=payload.y0,
        y1=payload.y1,
        x0=payload.x0,
        x1=payload.x1,
        mask_strokes=[m.model_dump() for m in payload.mask_strokes],
        ink_strokes=[m.model_dump() for m in payload.ink_strokes],
        patches=[p.model_dump() for p in payload.patches],
        baseline_y=payload.baseline_y,
        midband_y=payload.midband_y,
        n_anchors=n_anchors,
        guides=guides,
        locked=locked,
        split=split,
        fill_holes_max_area=fill_holes_max_area,
    )
    return _to_out(bbox)


@router.delete("/{glyph_key}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_bbox(glyph_key: str, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)):
    await BboxRepository(db).delete(source.id, glyph_key)
