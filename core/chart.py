"""Chart-image loading + bbox cropping. Pure functions; no DB, no globals.

The chart bytes live on disk under `/data/sources/<source_id>/...`. The DB's
`sources.chart_path` is the relative path; resolve against `REPO_ROOT` from
`core.config`. Callers pass either a `Source` row dict or the resolved path
directly.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from core.config import REPO_ROOT
from core.extract import load_grayscale


def resolve_chart_path(chart_path: str | Path) -> Path:
    """Turn a stored (relative) chart_path into an absolute path under the repo root."""
    p = Path(chart_path)
    return p if p.is_absolute() else REPO_ROOT / p


def load_chart_grayscale(chart_path: str | Path) -> np.ndarray:
    """Load chart bytes as float32 [0, 1] grayscale."""
    return load_grayscale(resolve_chart_path(chart_path))


def crop_with_excludes(chart: np.ndarray, bbox: dict, fill: float | int = 1.0) -> np.ndarray:
    """Slice the main rect and white out any exclude sub-rectangles.

    `bbox` is a dict-shaped row carrying `y0/y1/x0/x1` and optional
    `excludes: list[{y0,y1,x0,x1}]`. `fill` is whatever counts as background
    in the input dtype — 255 for uint8, 1.0 for float32-in-[0,1].
    """
    y0, y1, x0, x1 = bbox["y0"], bbox["y1"], bbox["x0"], bbox["x1"]
    crop = chart[y0:y1, x0:x1].copy()
    for ex in bbox.get("excludes") or []:
        ey0 = max(0, ex["y0"] - y0)
        ey1 = min(y1 - y0, ex["y1"] - y0)
        ex0 = max(0, ex["x0"] - x0)
        ex1 = min(x1 - x0, ex["x1"] - x0)
        if ey1 > ey0 and ex1 > ex0:
            crop[ey0:ey1, ex0:ex1] = fill
    return crop


def crop_to_png_bytes(chart: np.ndarray, bbox: dict) -> bytes:
    """Crop + excludes → PNG bytes (8-bit grayscale, white background)."""
    from io import BytesIO

    crop = crop_with_excludes(chart, bbox, fill=1.0)
    crop_uint8 = (np.clip(crop, 0.0, 1.0) * 255).astype(np.uint8)
    buf = BytesIO()
    Image.fromarray(crop_uint8, mode="L").save(buf, format="PNG")
    return buf.getvalue()
