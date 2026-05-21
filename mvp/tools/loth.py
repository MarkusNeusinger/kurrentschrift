"""Shared utilities for working with the Loth 1866 chart.

Three consumers — annotate_chart.py (interactive coordinate picking),
render_canonicals.py (side-by-side review), trace_skeleton.py (skeleton →
canonical-anchor extraction) — all need the same handful of operations:
loading the bbox table, cropping a glyph rectangle with exclude regions,
and rasterising the SVG copy of the chart for the visual review tools.

The actual M0 image pipeline (binarize, skeletonize, distance transform) lives
in mvp.extract — this module is only the glue between bbox-table coordinates
and image data.
"""

from __future__ import annotations

import json
from pathlib import Path

import cairosvg
import numpy as np
from PIL import Image

from mvp.extract import load_grayscale


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOTH_JPG = REPO_ROOT / "data" / "sources" / "loth-1866" / "chart.jpg"
LOTH_SVG = REPO_ROOT / "data" / "sources" / "loth-1866" / "chart.svg"
BBOXES_JSON = REPO_ROOT / "mvp" / "canonical" / "loth_bboxes.json"
CANONICAL_DIR = REPO_ROOT / "mvp" / "canonical"
OUTPUT_DIR = REPO_ROOT / "mvp" / "out"
SVG_RENDER_PATH = OUTPUT_DIR / "chart-svg-render-white.png"
SVG_RENDER_SIZE = (1633, 1869)


def load_bboxes() -> dict[str, dict | None]:
    """Read the editable bbox table verbatim.

    Returns a dict mapping glyph_key → bbox-dict-or-None. Each non-null bbox
    is the raw JSON object, so callers can access y0/y1/x0/x1, the optional
    exclude list, and the v0.2 calibration fields (baseline_y, midband_y,
    start_xy, branch_choices, n_anchors) without a parsing layer in the way.
    """
    data = json.loads(BBOXES_JSON.read_text(encoding="utf-8"))
    return {name: bbox for name, bbox in data["bboxes"].items()}


def crop_with_excludes(chart: np.ndarray, bbox: dict, fill: float | int = 255) -> np.ndarray:
    """Slice the main rect and white out any exclude sub-rectangles.

    `fill` is whatever counts as "background" in the input dtype — 255 for
    uint8 grayscale, 1.0 for float32-in-[0,1].
    """
    y0, y1, x0, x1 = bbox["y0"], bbox["y1"], bbox["x0"], bbox["x1"]
    crop = chart[y0:y1, x0:x1].copy()
    for ex in bbox.get("exclude", []):
        ey0 = max(0, ex["y0"] - y0)
        ey1 = min(y1 - y0, ex["y1"] - y0)
        ex0 = max(0, ex["x0"] - x0)
        ex1 = min(x1 - x0, ex["x1"] - x0)
        if ey1 > ey0 and ex1 > ex0:
            crop[ey0:ey1, ex0:ex1] = fill
    return crop


def rasterise_svg() -> np.ndarray:
    """Render chart.svg onto a white background as uint8 grayscale; cache to disk."""
    if not SVG_RENDER_PATH.exists():
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        # cairosvg writes RGBA with transparent background; composite onto
        # white so the grayscale conversion produces the expected ink-on-paper.
        cairosvg.svg2png(url=str(LOTH_SVG), write_to=str(SVG_RENDER_PATH), output_width=SVG_RENDER_SIZE[0], output_height=SVG_RENDER_SIZE[1])
        rgba = Image.open(SVG_RENDER_PATH)
        white = Image.new("RGB", rgba.size, (255, 255, 255))
        white.paste(rgba, mask=rgba.split()[3])
        white.convert("L").save(SVG_RENDER_PATH)
    return np.asarray(Image.open(SVG_RENDER_PATH).convert("L"))


def load_chart_grayscale() -> np.ndarray:
    """Load the JPG source (float32 in [0,1]) — the pipeline's true input.

    SVG is only used for the visual-review tools (`annotate_chart`,
    bottom row of `render_canonicals`). The actual M0/M3 pipeline reads
    the JPG because that's what the project commits as the authoritative
    public-domain source and what every downstream tool standardises on.
    """
    return load_grayscale(LOTH_JPG)
