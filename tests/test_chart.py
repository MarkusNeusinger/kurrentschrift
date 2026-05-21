"""Crop + exclude geometry."""

import numpy as np

from core.chart import crop_with_excludes


def test_crop_slices_correctly():
    chart = np.arange(100 * 100, dtype=np.float32).reshape(100, 100) / 10000.0
    bbox = {"y0": 10, "y1": 30, "x0": 20, "x1": 60, "excludes": []}
    crop = crop_with_excludes(chart, bbox)
    assert crop.shape == (20, 40)
    assert np.allclose(crop[0, 0], chart[10, 20])


def test_excludes_are_filled_with_background():
    chart = np.zeros((50, 50), dtype=np.float32)
    bbox = {"y0": 0, "y1": 50, "x0": 0, "x1": 50, "excludes": [{"y0": 10, "y1": 20, "x0": 30, "x1": 40}]}
    crop = crop_with_excludes(chart, bbox, fill=1.0)
    # The exclude region is whited out…
    assert crop[10:20, 30:40].min() == 1.0
    # …and everything else stays at the original background (0).
    assert crop[0:10].max() == 0.0
    assert crop[20:].max() == 0.0


def test_partially_offscreen_exclude_is_clipped():
    chart = np.zeros((50, 50), dtype=np.float32)
    bbox = {"y0": 10, "y1": 40, "x0": 10, "x1": 40, "excludes": [{"y0": 5, "y1": 15, "x0": 5, "x1": 15}]}
    crop = crop_with_excludes(chart, bbox, fill=1.0)
    # Only the overlap (rows 10–14, cols 10–14 → local rows 0–4, cols 0–4) gets filled.
    assert crop[0:5, 0:5].min() == 1.0
    assert crop[5:, 5:].max() == 0.0
