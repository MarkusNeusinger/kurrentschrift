"""Template-coord helpers."""

import numpy as np

from core.template import (
    allocate_samples,
    apply_slant,
    multi_stroke_outline,
    sample_polyline,
    stroke_outline,
    template_guides,
)


def test_template_guides_match_ratio():
    g = template_guides([2, 1, 2])
    assert g["baseline"] == 0.0
    assert g["midband"] == 1.0
    assert g["ascender"] == 3.0  # 1 + 2/1
    assert g["descender"] == -2.0


def test_template_guides_for_111_ratio():
    g = template_guides([1, 1, 1])
    assert g["ascender"] == 2.0
    assert g["descender"] == -1.0


def test_sample_polyline_returns_n_points():
    anchors = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 0.0]])
    widths = np.array([0.1, 0.15, 0.1])
    x, y, w = sample_polyline(anchors, widths, n=50)
    assert len(x) == len(y) == len(w) == 50


def test_stroke_outline_is_closed_polygon():
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([0.0, 0.0, 0.0])
    w = np.array([0.1, 0.1, 0.1])
    poly_x, poly_y = stroke_outline(x, y, w)
    assert len(poly_x) == len(poly_y) == 6  # 3 top + 3 bottom


def test_apply_slant_zero_is_identity():
    x = np.array([0.0, 0.0, 0.0])
    y = np.array([0.0, 1.0, 2.0])
    x2, y2 = apply_slant(x, y, 0.0)
    assert np.allclose(x2, x)
    assert np.allclose(y2, y)


def test_apply_slant_shears_along_x():
    x = np.array([0.0])
    y = np.array([1.0])
    # 90° slant = upright leans into the +x direction by tan(0°) = 0
    # 45° slant means the top of a unit-height vertical moves by tan(45°)=1 in +x
    x2, _ = apply_slant(x, y, 45.0)
    assert np.isclose(x2[0], 1.0)


def test_allocate_samples_proportional_with_floor():
    alloc = allocate_samples([10.0, 30.0], 20)
    assert sum(alloc) == 20
    assert min(alloc) >= 2
    # The longer segment gets more samples.
    assert alloc[1] > alloc[0]


def test_allocate_samples_grows_when_n_too_small():
    # Three strokes need at least 2 each; n=4 is bumped up to 6.
    alloc = allocate_samples([1.0, 1.0, 1.0], 4)
    assert sum(alloc) == 6
    assert all(a >= 2 for a in alloc)


def test_multi_stroke_outline_one_polygon_per_stroke():
    # Two separate vertical strokes (anchors 0–1 and 2–3), split at index 2.
    anchors = np.array([[0.0, 1.0], [0.0, 0.0], [0.3, 1.0], [0.3, 0.0]])
    widths = np.array([0.1, 0.1, 0.1, 0.1])
    polys = multi_stroke_outline(anchors, widths, [0, 2], slant_deg=90.0)
    assert len(polys) == 2
    # No stroke_starts → a single continuous stroke → one polygon.
    assert len(multi_stroke_outline(anchors, widths, None, slant_deg=90.0)) == 1
