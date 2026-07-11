"""Template-coord helpers."""

import numpy as np
from shapely.geometry import Point as ShapelyPoint
from shapely.geometry import Polygon as ShapelyPolygon

from core.template import (
    allocate_samples,
    apply_slant,
    capsule_union_rings,
    erase_silhouette_piece,
    multi_stroke_centerlines,
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


def test_apply_slant_90_is_identity():
    # Schräglage convention: 90° = upright, so 90 must be the no-op.
    x = np.array([0.0, 0.0, 0.0])
    y = np.array([0.0, 1.0, 2.0])
    x2, y2 = apply_slant(x, y, 90.0)
    assert np.allclose(x2, x)
    assert np.allclose(y2, y)


def test_apply_slant_makes_baseline_angle():
    # A vertical sheared to Schräglage 65 must make 65° with the baseline.
    x = np.array([0.0, 0.0])
    y = np.array([0.0, 1.0])
    x2, y2 = apply_slant(x, y, 65.0)
    angle = np.degrees(np.arctan2(y2[1] - y2[0], x2[1] - x2[0]))
    assert np.isclose(angle, 65.0)


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


def test_multi_stroke_centerlines_one_line_per_stroke():
    anchors = np.array([[0.0, 1.0], [0.0, 0.0], [0.3, 1.0], [0.3, 0.0]])
    widths = np.array([0.1, 0.1, 0.1, 0.1])
    lines = multi_stroke_centerlines(anchors, widths, [0, 2], slant_deg=90.0)
    assert len(lines) == 2
    # No stroke_starts → one continuous centerline.
    assert len(multi_stroke_centerlines(anchors, widths, None, slant_deg=90.0)) == 1


def _evenodd_region(rings):
    """Reconstruct the evenodd fill region of a ring payload (the client's
    fill rule) — the same pairing erase_silhouette_piece performs."""
    region = None
    for ring in rings:
        poly = ShapelyPolygon(ring)
        region = poly if region is None else region.symmetric_difference(poly)
    return region


def test_erase_silhouette_piece_noop_on_empty_or_short_input():
    x = np.array([0.0, 1.0, 2.0])
    rings = capsule_union_rings(x, np.zeros(3), np.full(3, 0.1))
    assert erase_silhouette_piece([], [(0.0, 0.0), (1.0, 0.0)], 0.1) == []
    # A piece of fewer than two samples has no arc to erase around.
    assert erase_silhouette_piece(rings, [(0.0, 0.0)], 0.1) == rings


def test_erase_silhouette_piece_removes_the_piece_and_keeps_the_rest():
    x = np.array([0.0, 1.0, 2.0])
    rings = capsule_union_rings(x, np.zeros(3), np.full(3, 0.1))
    erased = erase_silhouette_piece(rings, [(0.0, 0.0), (0.6, 0.0)], 0.12)
    before, after = _evenodd_region(rings), _evenodd_region(erased)
    assert after.area < before.area
    assert not after.contains(ShapelyPoint(0.2, 0.0))  # the stub piece is gone
    assert after.contains(ShapelyPoint(1.5, 0.0))  # the kept flank still renders


def test_erase_silhouette_piece_preserves_holes():
    # A closed loop's capsule union carries its counter as a real hole
    # (exterior + interior ring); erasing a short piece on the far side must
    # not fill the hole in — the evenodd reconstruction keeps the pairing.
    t = np.linspace(0.0, 2 * np.pi, 60)
    rings = capsule_union_rings(np.cos(t), np.sin(t), np.full_like(t, 0.15))
    assert len(rings) >= 2  # exterior + hole
    erased = erase_silhouette_piece(rings, [(1.0, -0.05), (1.0, 0.05)], 0.1)
    region = _evenodd_region(erased)
    assert not region.contains(ShapelyPoint(0.0, 0.0))  # hole is still a hole
    assert region.contains(ShapelyPoint(-1.0, 0.0))  # loop ink far away survives


def test_centerline_runs_down_the_spine_of_its_outline():
    # The outline is left+right offsets of the same centerline samples, so each
    # outline polygon has exactly twice as many points as its centerline — proof
    # they are sampled identically and stay aligned.
    anchors = np.array([[0.0, 1.0], [0.0, 0.0], [0.3, 1.0], [0.3, 0.0]])
    widths = np.array([0.1, 0.12, 0.1, 0.12])
    lines = multi_stroke_centerlines(anchors, widths, [0, 2], slant_deg=65.0, n=40)
    polys = multi_stroke_outline(anchors, widths, [0, 2], slant_deg=65.0, n=40)
    assert len(lines) == len(polys) == 2
    for line, poly in zip(lines, polys, strict=True):
        assert len(poly) == 2 * len(line)
