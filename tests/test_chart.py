"""Crop + freeform eraser-mask geometry."""

import numpy as np

from core.chart import crop_with_mask


def test_crop_slices_correctly():
    chart = np.arange(100 * 100, dtype=np.float32).reshape(100, 100) / 10000.0
    bbox = {"y0": 10, "y1": 30, "x0": 20, "x1": 60, "mask_strokes": []}
    crop = crop_with_mask(chart, bbox)
    assert crop.shape == (20, 40)
    assert np.allclose(crop[0, 0], chart[10, 20])


def test_eraser_stroke_is_filled_with_background():
    chart = np.zeros((50, 50), dtype=np.float32)
    # A vertical brush stroke at x=30 from y=10 to y=20, radius 5 (10px wide).
    bbox = {"y0": 0, "y1": 50, "x0": 0, "x1": 50, "mask_strokes": [{"points": [[30, 10], [30, 20]], "radius": 5}]}
    crop = crop_with_mask(chart, bbox, fill=1.0)
    # The brushed centerline is whited out…
    assert crop[15, 30] == 1.0
    # …and a pixel far from the stroke stays at the original background (0).
    assert crop[40, 5] == 0.0


def test_eraser_strokes_are_offset_into_crop_local_coords():
    chart = np.zeros((50, 50), dtype=np.float32)
    # Chart-global point (15, 15) sits at crop-local (5, 5) for x0=y0=10.
    bbox = {"y0": 10, "y1": 40, "x0": 10, "x1": 40, "mask_strokes": [{"points": [[15, 15]], "radius": 3}]}
    crop = crop_with_mask(chart, bbox, fill=1.0)
    assert crop[5, 5] == 1.0  # the single-point dab lands at the offset location
    assert crop[25, 25] == 0.0  # far away, untouched
