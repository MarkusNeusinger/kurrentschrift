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
from core.extract import binarize_adaptive, load_grayscale


def resolve_chart_path(chart_path: str | Path) -> Path:
    """Turn a stored (relative) chart_path into an absolute path under the repo root."""
    p = Path(chart_path)
    return p if p.is_absolute() else REPO_ROOT / p


def load_chart_grayscale(chart_path: str | Path) -> np.ndarray:
    """Load chart bytes as float32 [0, 1] grayscale."""
    return load_grayscale(resolve_chart_path(chart_path))


def _rasterize_strokes(strokes: list, w: int, h: int, x0: int, y0: int) -> np.ndarray:
    """Rasterise a list of {points, radius} brush strokes to a boolean mask.

    Defensive: tolerate stray short points so a malformed row can't crash the
    crop (the API schema already enforces (x, y) pairs on new writes).
    """
    img = Image.new("1", (w, h), 0)
    draw = ImageDraw.Draw(img)
    for stroke in strokes:
        raw_points = stroke.get("points") or []
        pts = [(float(p[0]) - x0, float(p[1]) - y0) for p in raw_points if len(p) >= 2]
        if not pts:
            continue
        radius = max(0.5, float(stroke.get("radius", 4.0)))
        width = max(1, int(round(radius * 2)))
        if len(pts) >= 2:
            draw.line(pts, fill=1, width=width, joint="curve")
        # round caps / single-point dabs
        for px, py in pts:
            draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=1)
    return np.array(img, dtype=bool)


def crop_with_mask(chart: np.ndarray, bbox: dict, fill: float | int = 1.0) -> np.ndarray:
    """Slice the main rect, blank the eraser strokes, then paint the ink strokes.

    `bbox` is a dict-shaped row carrying `y0/y1/x0/x1` plus two optional brush-
    stroke lists in chart-pixel coords, each `[{points: [[x, y], ...], radius}]`:

    - `mask_strokes` — the freeform eraser (German: Radierer): covered pixels are
      set to `fill`, the input's background (255 for uint8, 1.0 for float32).
    - `ink_strokes` — the manual ink brush (German: Tinten-Pinsel), the positive
      twin: covered pixels are set to ink (0), to close specks/gaps inside a
      stroke. Applied *after* the eraser, so ink wins on any overlap.

    Both happen *before* skeletonisation: erasing keeps neighbouring-letter ink
    out of the skeleton, inking keeps a faded fleck from breaking it.
    """
    y0, y1, x0, x1 = bbox["y0"], bbox["y1"], bbox["x0"], bbox["x1"]
    crop = chart[y0:y1, x0:x1].copy()
    h, w = crop.shape[:2]
    if h <= 0 or w <= 0:
        return crop

    eraser = bbox.get("mask_strokes") or []
    if eraser:
        crop[_rasterize_strokes(eraser, w, h, x0, y0)] = fill
    ink = bbox.get("ink_strokes") or []
    if ink:
        crop[_rasterize_strokes(ink, w, h, x0, y0)] = 0
    return crop


def crop_to_png_bytes(chart: np.ndarray, bbox: dict) -> bytes:
    """Crop + eraser + ink → PNG bytes (8-bit grayscale, white background)."""
    from io import BytesIO

    crop = crop_with_mask(chart, bbox, fill=1.0)
    crop_uint8 = (np.clip(crop, 0.0, 1.0) * 255).astype(np.uint8)
    buf = BytesIO()
    Image.fromarray(crop_uint8, mode="L").save(buf, format="PNG")
    return buf.getvalue()


def crop_mask_to_png_bytes(chart: np.ndarray, bbox: dict) -> bytes:
    """Crop + eraser + ink, binarise with the bbox's fill, and colour-code what
    the auto-fill swallowed → RGB PNG of the mask the skeleton actually sees.

    Backs the wizard's "Maske zeigen" preview. The raw crop shows neither the
    binarisation nor the Lücken-füllen (both are downstream of it), so raising the
    fill threshold changes nothing on the raw scan. Here:

    - black  = ink (incl. the manual ink-brush strokes, baked in before binarising)
    - green  = specks the auto-fill swallowed at the current threshold
    - white  = background — so a white spot still *inside* the letter is exactly
               what the auto-fill missed and the user must ink by hand.
    """
    from io import BytesIO

    crop = crop_with_mask(chart, bbox, fill=1.0)
    max_area = int(bbox.get("fill_holes_max_area") or 0)
    raw = binarize_adaptive(crop, fill_holes_max_area=0)
    filled = binarize_adaptive(crop, fill_holes_max_area=max_area) if max_area > 0 else raw
    auto_filled = filled & ~raw  # what the threshold swallowed beyond the raw ink

    h, w = crop.shape[:2]
    rgb = np.full((h, w, 3), 255, dtype=np.uint8)
    rgb[raw] = (0, 0, 0)
    rgb[auto_filled] = (31, 168, 90)
    buf = BytesIO()
    Image.fromarray(rgb, mode="RGB").save(buf, format="PNG")
    return buf.getvalue()
