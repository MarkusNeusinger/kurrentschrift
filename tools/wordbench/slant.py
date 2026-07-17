"""Slant estimation for the word bench report (redesign R5, report-only).

Classic HTR shear search: try shear angles in a fixed band, straighten the ink
by each candidate and keep the angle whose column profile is most concentrated
(maximum sum of squared column sums). Repo-wide slant convention: 90 degrees =
upright, below 90 = right-leaning (docs/schriftkunde). The estimate is a REPORT
column, never part of the headline loss — the frozen ruler in
core/word_metric.py stays untouched.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw

SHEAR_RANGE_DEG = 30.0
SHEAR_STEP_DEG = 0.25
MIN_PIXELS = 32  # below this a profile maximum is noise, not a slant


def slant_deg(mask: np.ndarray) -> float | None:
    """Dominant stroke slant of the True pixels in an image-frame array (y down).

    Returns degrees against the baseline (90.0 = upright, < 90 = right-leaning),
    or None when there is too little ink to measure.
    """
    ys, xs = np.nonzero(mask)
    if ys.size < MIN_PIXELS:
        return None
    ys = ys.astype(np.float64)
    xs = xs.astype(np.float64)
    best_lean = 0.0
    best_score = -1.0
    for lean in np.arange(-SHEAR_RANGE_DEG, SHEAR_RANGE_DEG + SHEAR_STEP_DEG / 2, SHEAR_STEP_DEG):
        # y grows downward, so a right-leaning stroke (top further right) is
        # straightened by pushing lower rows right by tan(lean) per row.
        sheared = np.round(xs + ys * math.tan(math.radians(lean))).astype(np.int64)
        profile = np.bincount(sheared - sheared.min())
        score = float(np.dot(profile, profile))
        if score > best_score:
            best_score = score
            best_lean = float(lean)
    return 90.0 - best_lean


def composed_raster(composed: dict, registration: dict, word_meta: dict, shape: tuple[int, int]) -> np.ndarray:
    """Rasterize the composed centerlines into the specimen crop frame.

    Same mapping as the run's overlay: template units -> crop pixels via the
    metric's fitted registration, so specimen and engine slant are measured on
    the same grid. Ink outside the crop is clipped (a trailing swing past the
    crop edge does not change the dominant slant).
    """
    xh, tx, ty = registration["xh_px"], registration["tx"], registration["ty"]
    baseline_row = word_meta["baseline_y"] - word_meta["rect"][1]
    img = Image.new("L", (shape[1], shape[0]), 0)
    draw = ImageDraw.Draw(img)
    for item in composed["items"]:
        pts = [(x * xh + tx, baseline_row - y * xh + ty) for x, y in item["centerline"]]
        if len(pts) >= 2:
            draw.line(pts, fill=255, width=1)
    return np.array(img) > 0
