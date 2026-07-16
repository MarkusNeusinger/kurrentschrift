"""Bbox CRUD per source."""

from typing import TypeVar

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db, require_source
from api.http import CACHE_CONTROL
from api.schemas import BboxIn, BboxOut, BboxStatusOut, GuideConfig
from core.database import Bbox, BboxRepository, Source
from core.pipeline import DEFAULT_N_ANCHORS


router = APIRouter(prefix="/sources/{source_id}/bboxes", tags=["bboxes"])

T = TypeVar("T")


def _coalesce(payload_val: T | None, stored_val: T | None, default: T) -> T:
    """Optional-field precedence for a bbox PUT: the client's value when it sent
    one, else whatever is already stored, else the default. Keeps a plain
    bbox/calibration save from wiping fields the client omitted."""
    if payload_val is not None:
        return payload_val
    return stored_val if stored_val is not None else default


def _to_out(bbox: Bbox) -> BboxOut:
    # The crop-affecting fields come from the ONE shared serializer (Pydantic
    # coerces the stroke/patch dicts into their models); the read-only bbox
    # metadata (calibration, guides, lock/split) rides alongside.
    return BboxOut(
        **bbox.to_pipeline_dict(),
        glyph_key=bbox.glyph_key,
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


@router.get("/status", response_model=list[BboxStatusOut])
async def list_bbox_status(
    response: Response, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    """Slim public read: just the availability flags per glyph_key.

    The quiz gates its vocabulary on locked/split (+ TemplateSummary.has_data);
    the full list above ships every mask/ink/patch JSONB blob for that. Declared
    BEFORE /{glyph_key} so the literal path wins the route match. Only the quiz
    boot consumes it (the admin reads the full list), so it caches like the
    other public reads — the flags change on the same admin-write cadence as
    the /write payloads.
    """
    response.headers["Cache-Control"] = CACHE_CONTROL
    rows = await BboxRepository(db).list_status(source.id)
    return [BboxStatusOut(**row) for row in rows]


@router.get("/{glyph_key}", response_model=BboxOut)
async def get_bbox(glyph_key: str, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)):
    bbox = await BboxRepository(db).get(source.id, glyph_key)
    if bbox is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"bbox not set for {glyph_key!r}")
    return _to_out(bbox)


@router.put("/{glyph_key}", response_model=BboxOut, dependencies=[Depends(require_admin)])
async def put_bbox(
    glyph_key: str, payload: BboxIn, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    # Geometry sanity: a degenerate or inverted rectangle would store fine but
    # blow up later on the public read path (empty crop → 500 in the pipeline).
    if min(payload.x0, payload.y0, payload.x1, payload.y1) < 0:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="bbox coordinates must be non-negative chart pixels"
        )
    if payload.x1 <= payload.x0 or payload.y1 <= payload.y0:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="bbox must have positive extent (x1 > x0 and y1 > y0)"
        )
    if payload.baseline_y <= payload.midband_y:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="baseline_y must be greater than midband_y (baseline is below midband)",
        )
    repo = BboxRepository(db)
    # `guides`, `locked`, `split`, `n_anchors` and `fill_holes_max_area` are
    # optional: when the client omits one, keep whatever is already stored (a
    # plain bbox/calibration save must not wipe the guide lines, silently rewrite
    # the anchor count, or require resending unrelated fields). Load `existing`
    # once up front and coalesce each field.
    existing = await repo.get(source.id, glyph_key)
    guides = payload.guides.model_dump() if payload.guides is not None else (existing.guides if existing else {})
    locked = _coalesce(payload.locked, bool(existing.locked) if existing else None, False)
    split = _coalesce(payload.split, bool(existing.split) if existing else None, False)
    n_anchors = _coalesce(payload.n_anchors, int(existing.n_anchors) if existing else None, DEFAULT_N_ANCHORS)
    fill_holes_max_area = _coalesce(
        payload.fill_holes_max_area, int(existing.fill_holes_max_area) if existing else None, 0
    )
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
