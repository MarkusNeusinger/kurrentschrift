"""Chart-image endpoints — full chart + per-bbox crop (binary responses)."""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import require_db, require_source
from core.chart import crop_to_png_bytes, load_chart_grayscale, resolve_chart_path
from core.database import BboxRepository, Source


router = APIRouter(prefix="/sources/{source_id}", tags=["chart"])


@router.get("/chart")
async def get_chart(source: Source = Depends(require_source)) -> Response:
    """Stream the source chart image (`chart_path` bytes from disk)."""
    path = resolve_chart_path(source.chart_path)
    if not path.exists():
        raise HTTPException(404, detail=f"chart file missing on disk: {path}")
    media_type = "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
    return Response(content=path.read_bytes(), media_type=media_type)


@router.get("/bboxes/{glyph_key}/crop")
async def get_crop(
    glyph_key: str, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
) -> Response:
    bbox = await BboxRepository(db).get(source.id, glyph_key)
    if bbox is None:
        raise HTTPException(404, detail=f"bbox not set for {glyph_key!r}")
    chart = load_chart_grayscale(source.chart_path)
    bbox_dict = {"y0": bbox.y0, "y1": bbox.y1, "x0": bbox.x0, "x1": bbox.x1, "mask_strokes": list(bbox.mask_strokes)}
    png = crop_to_png_bytes(chart, bbox_dict)
    return Response(content=png, media_type="image/png")
