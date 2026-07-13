"""Chart-image endpoints — full chart + per-bbox crop (binary responses)."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import require_db, require_source
from core.chart import crop_mask_to_png_bytes, crop_to_png_bytes, load_chart_grayscale, resolve_chart_path
from core.database import BboxRepository, Source


router = APIRouter(prefix="/sources/{source_id}", tags=["chart"])


_DISPLAY_MEDIA_TYPES = {".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


@router.get("/chart")
async def get_chart(source: Source = Depends(require_source)) -> FileResponse:
    """Stream the source chart image for display.

    Prefers a crisp vector sibling (`<chart>.svg`) if one sits next to the raster
    `chart_path`; it shares the raster's exact pixel coordinate space (same
    `viewBox`), so it scales sharply at any zoom without touching stored bbox /
    mask / guide coordinates. The measurement pipeline (crops, skeletonisation)
    keeps reading the raster `chart_path` itself — this endpoint is display-only.
    """
    raster = resolve_chart_path(source.chart_path)
    svg = raster.with_suffix(".svg")
    path = svg if svg.exists() else raster
    if not path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"chart file missing on disk: {path}")
    media_type = _DISPLAY_MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream")
    return FileResponse(path, media_type=media_type)


@router.get("/bboxes/{glyph_key}/crop")
async def get_crop(
    glyph_key: str,
    view: Literal["raw", "mask"] = "raw",
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
) -> Response:
    """Per-bbox crop PNG. `view=raw` (default) is the grayscale scan with the
    eraser + ink brush applied; `view=mask` is the binarised mask the skeleton
    sees, colour-coding what the auto-fill swallowed (the wizard's preview)."""
    bbox = await BboxRepository(db).get(source.id, glyph_key)
    if bbox is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"bbox not set for {glyph_key!r}")
    chart = load_chart_grayscale(source.chart_path)
    bbox_dict = bbox.to_pipeline_dict()
    png = crop_mask_to_png_bytes(chart, bbox_dict) if view == "mask" else crop_to_png_bytes(chart, bbox_dict)
    return Response(content=png, media_type="image/png")
