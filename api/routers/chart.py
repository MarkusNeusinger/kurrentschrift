"""Chart image endpoints — serves the raw Loth chart and per-glyph crops."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response

from api.core.pipeline import get_bbox, render_crop_png
from api.core.settings import settings


router = APIRouter(tags=["chart"])


@router.get("/chart")
async def get_chart():
    """Return the source Loth 1866 chart JPG.

    Frontend renders this as the main canvas background; bboxes overlay
    on top of it in screen coords that map 1:1 to chart-pixel coords
    (no resize on the server).
    """
    if not settings.chart_path.exists():
        raise HTTPException(status_code=404, detail=f"chart not found at {settings.chart_path}")
    return FileResponse(settings.chart_path, media_type="image/jpeg")


@router.get("/chart/crop/{glyph_key}")
async def get_chart_crop(glyph_key: str):
    """Return the bbox-cropped chart with exclude-rects whited out, as PNG."""
    try:
        bbox = get_bbox(glyph_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if bbox is None:
        raise HTTPException(status_code=409, detail=f"{glyph_key}: bbox not yet set")
    png_bytes = render_crop_png(bbox)
    return Response(content=png_bytes, media_type="image/png")
