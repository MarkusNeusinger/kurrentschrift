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


def test_ink_stroke_is_painted_as_ink():
    chart = np.ones((50, 50), dtype=np.float32)  # all background (white)
    bbox = {
        "y0": 0,
        "y1": 50,
        "x0": 0,
        "x1": 50,
        "mask_strokes": [],
        "ink_strokes": [{"points": [[30, 10], [30, 20]], "radius": 5}],
    }
    crop = crop_with_mask(chart, bbox, fill=1.0)
    assert crop[15, 30] == 0.0  # the inked centerline is painted black (ink)
    assert crop[40, 5] == 1.0  # far from the stroke stays background


def test_ink_wins_over_eraser_on_overlap():
    chart = np.zeros((50, 50), dtype=np.float32)  # all ink (black)
    pt = [[25, 25]]
    bbox = {
        "y0": 0,
        "y1": 50,
        "x0": 0,
        "x1": 50,
        "mask_strokes": [{"points": pt, "radius": 5}],
        "ink_strokes": [{"points": pt, "radius": 5}],
    }
    crop = crop_with_mask(chart, bbox, fill=1.0)
    assert crop[25, 25] == 0.0  # ink applied after the eraser → ink wins on overlap


def test_patch_copies_donor_ink_to_dst():
    chart = np.ones((50, 50), dtype=np.float32)  # white
    chart[5:10, 5:10] = 0.0  # a 5×5 dark donor block on the chart
    # dst (20, 20) in chart coords → crop-local (10, 10) for x0=y0=10.
    bbox = {"y0": 10, "y1": 40, "x0": 10, "x1": 40, "patches": [{"src": [5, 5, 10, 10], "dst": [20, 20]}]}
    crop = crop_with_mask(chart, bbox, fill=1.0)
    assert np.all(crop[10:15, 10:15] == 0.0)  # the donor ink landed at the offset
    assert crop[0, 0] == 1.0  # everything else stays background


def test_patch_darken_keeps_base_ink():
    chart = np.ones((50, 50), dtype=np.float32)
    chart[30, 30] = 0.0  # base ink inside the bbox (crop-local (20, 20))
    # An all-white donor placed over that base ink must not erase it (np.minimum).
    bbox = {"y0": 10, "y1": 40, "x0": 10, "x1": 40, "patches": [{"src": [0, 0, 5, 5], "dst": [28, 28]}]}
    crop = crop_with_mask(chart, bbox, fill=1.0)
    assert crop[20, 20] == 0.0  # the donor's white background left the base ink intact


def test_patch_applies_after_eraser():
    chart = np.ones((50, 50), dtype=np.float32)
    chart[5:10, 5:10] = 0.0  # dark donor
    # The eraser blanks around (22, 22); the patch then darkens the same spot.
    bbox = {
        "y0": 0,
        "y1": 50,
        "x0": 0,
        "x1": 50,
        "mask_strokes": [{"points": [[22, 22]], "radius": 6}],
        "patches": [{"src": [5, 5, 10, 10], "dst": [20, 20]}],
    }
    crop = crop_with_mask(chart, bbox, fill=1.0)
    assert crop[22, 22] == 0.0  # patch runs after the eraser, so its ink wins


def test_patch_out_of_bounds_clips_without_crashing():
    chart = np.ones((50, 50), dtype=np.float32)
    chart[0:10, 0:10] = 0.0  # dark donor
    bbox = {
        "y0": 10,
        "y1": 40,
        "x0": 10,
        "x1": 40,
        "patches": [
            {"src": [0, 0, 10, 10], "dst": [35, 35]},  # spills past the crop edge → partial paste
            {"src": [100, 100, 120, 120], "dst": [20, 20]},  # src outside the chart → skipped
            {"src": [0, 0, 5, 5], "dst": [-100, -100]},  # dst outside the crop → skipped
        ],
    }
    crop = crop_with_mask(chart, bbox, fill=1.0)  # must not raise
    assert crop.shape == (30, 30)
    assert crop[25, 25] == 0.0  # the in-bounds part of the spilling patch still landed


def test_patch_malformed_rows_are_skipped():
    chart = np.ones((50, 50), dtype=np.float32)
    bbox = {"y0": 0, "y1": 50, "x0": 0, "x1": 50, "patches": [{"src": [1, 2, 3]}, {"dst": [5, 5]}, {}]}
    crop = crop_with_mask(chart, bbox, fill=1.0)  # must not raise
    assert np.all(crop == 1.0)
