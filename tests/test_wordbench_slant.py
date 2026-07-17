"""The wordbench slant report column (redesign R5): shear-search estimator.

Report-only diagnostics — these tests pin the estimator's convention
(90 = upright, < 90 = right-leaning) on synthetic strokes and the crop-frame
rasterization of a composed payload. The headline loss never touches slant.
"""

import math

import numpy as np

from tools.wordbench.slant import composed_raster, slant_deg


def _stroke_mask(lean_deg: float, n_strokes: int = 6, height: int = 120) -> np.ndarray:
    """Parallel straight strokes leaning ``lean_deg`` right of vertical (y down)."""
    mask = np.zeros((height, 40 * n_strokes), dtype=bool)
    for s in range(n_strokes):
        x0 = 40 * s + 20
        for y in range(height):
            x = int(round(x0 - y * math.tan(math.radians(lean_deg))))
            if 0 <= x < mask.shape[1]:
                mask[y, x] = True
    return mask


def test_upright_strokes_measure_90() -> None:
    assert slant_deg(_stroke_mask(0.0)) == 90.0


def test_right_lean_measures_below_90() -> None:
    measured = slant_deg(_stroke_mask(5.0))
    assert measured is not None
    assert abs(measured - 85.0) <= 0.5


def test_left_lean_measures_above_90() -> None:
    measured = slant_deg(_stroke_mask(-4.0))
    assert measured is not None
    assert abs(measured - 94.0) <= 0.5


def test_too_little_ink_returns_none() -> None:
    mask = np.zeros((50, 50), dtype=bool)
    mask[10, 10] = True
    assert slant_deg(mask) is None


def test_composed_raster_maps_template_units_to_crop_frame() -> None:
    # One vertical centerline from baseline to midband at x=1.0 template units.
    composed = {"items": [{"centerline": [(1.0, 0.0), (1.0, 1.0)]}]}
    registration = {"xh_px": 20.0, "tx": 5.0, "ty": 0.0}
    word_meta = {"rect": [0, 0, 60, 60], "baseline_y": 40}
    raster = composed_raster(composed, registration, word_meta, (60, 60))
    ys, xs = np.nonzero(raster)
    # x = 1.0 * 20 + 5 = 25; y runs from baseline_row 40 up to 40 - 20 = 20.
    assert set(np.unique(xs)) == {25}
    assert ys.min() == 20 and ys.max() == 40
