"""Chart-image loading + bbox cropping. Pure functions; no DB, no globals.

The chart bytes live on disk under `/data/sources/<source_id>/...`. The DB's
`sources.chart_path` is the relative path; resolve against `REPO_ROOT` from
`core.config`. Callers pass either a `Source` row dict or the resolved path
directly.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from core.config import REPO_ROOT
from core.extract import load_grayscale


def resolve_chart_path(chart_path: str | Path) -> Path:
    """Turn a stored (relative) chart_path into an absolute path under the repo root."""
    p = Path(chart_path)
    return p if p.is_absolute() else REPO_ROOT / p


def load_chart_grayscale(chart_path: str | Path) -> np.ndarray:
    """Load chart bytes as float32 [0, 1] grayscale."""
    return load_grayscale(resolve_chart_path(chart_path))


def crop_with_mask(chart: np.ndarray, bbox: dict, fill: float | int = 1.0) -> np.ndarray:
    """Slice the main rect and blank the freeform eraser strokes (German: Radierer).

    `bbox` is a dict-shaped row carrying `y0/y1/x0/x1` and optional
    `mask_strokes: list[{points: [[x, y], ...], radius}]` in chart-pixel coords.
    Each stroke is rasterised to a thick polyline (rounded caps) and the covered
    pixels are set to `fill` — whatever counts as background in the input dtype
    (255 for uint8, 1.0 for float32-in-[0, 1]). Erasing happens *before*
    skeletonisation so neighbouring-letter ink can't pollute the skeleton.
    """
    y0, y1, x0, x1 = bbox["y0"], bbox["y1"], bbox["x0"], bbox["x1"]
    crop = chart[y0:y1, x0:x1].copy()
    h, w = crop.shape[:2]
    strokes = bbox.get("mask_strokes") or []
    if not strokes or h <= 0 or w <= 0:
        return crop

    mask_img = Image.new("1", (w, h), 0)
    draw = ImageDraw.Draw(mask_img)
    for stroke in strokes:
        pts = [(float(p[0]) - x0, float(p[1]) - y0) for p in (stroke.get("points") or [])]
        if not pts:
            continue
        radius = max(0.5, float(stroke.get("radius", 4.0)))
        width = max(1, int(round(radius * 2)))
        if len(pts) >= 2:
            draw.line(pts, fill=1, width=width, joint="curve")
        # round caps / single-point dabs
        for px, py in pts:
            draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=1)

    crop[np.array(mask_img, dtype=bool)] = fill
    return crop


def crop_to_png_bytes(chart: np.ndarray, bbox: dict) -> bytes:
    """Crop + eraser mask → PNG bytes (8-bit grayscale, white background)."""
    from io import BytesIO

    crop = crop_with_mask(chart, bbox, fill=1.0)
    crop_uint8 = (np.clip(crop, 0.0, 1.0) * 255).astype(np.uint8)
    buf = BytesIO()
    Image.fromarray(crop_uint8, mode="L").save(buf, format="PNG")
    return buf.getvalue()
