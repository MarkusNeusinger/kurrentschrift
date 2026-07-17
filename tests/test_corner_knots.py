"""Corner knots: detection, knot-forced resampling, corner-aware sampling."""

from __future__ import annotations

import numpy as np
import pytest

from core.pipeline import _detect_corners, canonical_from_path, canonical_from_raw_path_only
from core.template import build_sample_plan, sample_with_plan, sample_with_sample_plan, stroke_sample_plan


def _two_stroke_anchors() -> tuple[np.ndarray, np.ndarray, list[int]]:
    """Two separate slanted strokes with varying widths (no corners)."""
    rng = np.linspace(0.0, 1.0, 12)
    first = np.column_stack([rng, 2.0 - 2.0 * rng])
    second = np.column_stack([0.6 + rng, 2.0 - 1.5 * rng])
    anchors = np.concatenate([first, second])
    widths = np.concatenate([0.05 + 0.04 * np.sin(rng * 3.0), np.full(12, 0.07)])
    return anchors, widths, [0, 12]


def test_plan_without_corners_matches_legacy_bit_for_bit():
    """corner_anchors=None must reproduce stroke_sample_plan/sample_with_plan exactly."""
    anchors, widths, stroke_starts = _two_stroke_anchors()
    legacy_slices, legacy_alloc, legacy_starts = stroke_sample_plan(anchors, stroke_starts, 100)
    plan = build_sample_plan(anchors, stroke_starts, None, 100)
    assert plan.slices == legacy_slices
    assert plan.alloc == legacy_alloc
    assert plan.sample_starts == legacy_starts
    assert plan.drop_rows == []
    assert plan.corner_sample_idx == []

    lx, ly, lw = sample_with_plan(anchors, widths, legacy_slices, legacy_alloc)
    nx, ny, nw = sample_with_sample_plan(anchors, widths, plan)
    assert np.array_equal(lx, nx)
    assert np.array_equal(ly, ny)
    assert np.array_equal(lw, nw)


def test_plan_with_corner_shares_anchor_and_drops_duplicate():
    """A corner splits the stroke into sub-arcs sharing the corner anchor."""
    # Chevron: down to the apex at index 5, back up — one stroke, one corner.
    down = np.column_stack([np.linspace(0.0, 0.5, 6), np.linspace(1.0, 0.0, 6)])
    up = np.column_stack([np.linspace(0.6, 1.1, 5), np.linspace(0.2, 1.0, 5)])
    anchors = np.concatenate([down, up])
    widths = np.full(len(anchors), 0.06)

    plan = build_sample_plan(anchors, [0], [5], 60)
    assert plan.slices == [(0, 6), (5, 11)]  # corner anchor 5 shared
    assert plan.sample_starts == [0]  # still ONE pen stroke
    assert len(plan.drop_rows) == 1
    assert len(plan.corner_sample_idx) == 1

    sx, sy, sw = sample_with_sample_plan(anchors, widths, plan)
    assert len(sx) == sum(plan.alloc) - 1  # duplicate corner row removed
    ci = plan.corner_sample_idx[0]
    # The surviving corner sample sits exactly on the corner anchor.
    assert abs(sx[ci] - anchors[5, 0]) < 1e-9
    assert abs(sy[ci] - anchors[5, 1]) < 1e-9


def test_corner_sampling_renders_a_true_kink():
    """With a corner knot the sampled centerline reaches the apex; without, the spline rounds it."""
    half = np.column_stack([np.linspace(0.0, 1.0, 8), np.linspace(2.0, 0.0, 8)])
    back = np.column_stack([np.linspace(1.0, 2.0, 8), np.linspace(0.0, 2.0, 8)])[1:]
    anchors = np.concatenate([half, back])  # sharp V, apex at index 7
    widths = np.full(len(anchors), 0.08)
    apex = anchors[7]

    def min_apex_distance(corner_anchors):
        plan = build_sample_plan(anchors, [0], corner_anchors, 120)
        sx, sy, _ = sample_with_sample_plan(anchors, widths, plan)
        return float(np.min(np.hypot(sx - apex[0], sy - apex[1])))

    d_with = min_apex_distance([7])
    d_without = min_apex_distance(None)
    assert d_with < 1e-9  # corner sample sits ON the apex
    # Plain spline through evenly spaced anchors overshoots/rounds the apex.
    assert d_with < d_without


# ------------------------------------------------------------------ detection


def _dense_chevron(apex=(400.0, 450.0), top_y=150.0, dx=150.0, num=60) -> np.ndarray:
    """Dense V-path: down the left flank to the apex, up the right flank."""
    down = np.column_stack([np.linspace(apex[0] - dx, apex[0], num), np.linspace(top_y, apex[1], num)])
    up = np.column_stack([np.linspace(apex[0], apex[0] + dx, num), np.linspace(apex[1], top_y, num)])[1:]
    return np.concatenate([down, up])


def test_detect_corners_finds_chevron_apex():
    corners = _detect_corners(_dense_chevron(), unit_px=100.0)
    assert len(corners) == 1
    # Arc position of the apex = length of the left flank.
    left_len = float(np.hypot(150.0, 300.0))
    assert abs(corners[0] - left_len) < 6.0


def test_detect_corners_ignores_smooth_arc():
    theta = np.linspace(np.pi, 0.0, 120)
    arc = np.column_stack([400.0 + 80.0 * np.cos(theta), 300.0 + 80.0 * np.sin(theta)])
    assert _detect_corners(arc, unit_px=100.0) == []


def test_detect_corners_ignores_hand_wobble():
    x = np.linspace(100.0, 500.0, 200)
    y = 300.0 + 1.5 * np.sin(x / 9.5)  # ±1.5px jitter on a straight stroke
    assert _detect_corners(np.column_stack([x, y]), unit_px=100.0) == []


def test_detect_corners_short_stroke_is_safe():
    assert _detect_corners(np.array([[0.0, 0.0], [4.0, 4.0]]), unit_px=100.0) == []


# ------------------------------------------------------------------ end to end


@pytest.fixture
def chevron_chart_path(tmp_path) -> str:
    """800x800 chart with a 16px-thick V (apex down) — a true reversal corner."""
    from PIL import Image

    yy, xx = np.mgrid[0:800, 0:800].astype(float)

    def dist_to_segment(p0, p1):
        d = np.array(p1) - np.array(p0)
        t = np.clip(((xx - p0[0]) * d[0] + (yy - p0[1]) * d[1]) / (d @ d), 0.0, 1.0)
        return np.hypot(xx - (p0[0] + t * d[0]), yy - (p0[1] + t * d[1]))

    apex, top_y, dx = (400.0, 450.0), 150.0, 150.0
    ink = (dist_to_segment((apex[0] - dx, top_y), apex) <= 8.0) | (dist_to_segment(apex, (apex[0] + dx, top_y)) <= 8.0)
    img = np.ones((800, 800), dtype=np.float32)
    img[ink] = 0.05
    out = tmp_path / "chevron.png"
    Image.fromarray((img * 255).astype(np.uint8), mode="L").save(out)
    return str(out)


CHEVRON_BBOX = {
    "y0": 100,
    "y1": 550,
    "x0": 200,
    "x1": 600,
    "mask_strokes": [],
    "baseline_y": 450,
    "midband_y": 350,
    "n_anchors": 40,
}


def _chevron_raw_path() -> list[dict]:
    pts = _dense_chevron()
    return [{"x": float(x), "y": float(y), "pressure": 0.5, "t": float(i)} for i, (x, y) in enumerate(pts)]


def test_canonical_records_corner_anchor_on_the_apex(chevron_chart_path):
    canon = canonical_from_path(
        raw_path=_chevron_raw_path(), bbox=CHEVRON_BBOX, chart_path=chevron_chart_path, glyph="k"
    )
    corners = canon["trace_meta"]["corner_anchors"]
    assert len(corners) == 1
    # The corner anchor sits on the apex (chart coords ~ (400, 450)).
    ax, ay = canon["trace_meta"]["pixel_anchors"][corners[0]]
    assert abs(ax - 400.0) < 6.0
    assert abs(ay - 450.0) < 6.0


def test_corner_survives_resample_from_raw_path(chevron_chart_path):
    canon = canonical_from_path(
        raw_path=_chevron_raw_path(), bbox=CHEVRON_BBOX, chart_path=chevron_chart_path, glyph="k"
    )
    rederived = canonical_from_raw_path_only(canon, CHEVRON_BBOX, chevron_chart_path, n_anchors=24)
    assert len(rederived["trace_meta"]["corner_anchors"]) == 1
    assert len(rederived["anchors"]) == 24


def test_corner_outside_stroke_interior_is_ignored():
    """Corners at a stroke boundary (or out of range) cannot split anything."""
    anchors, widths, stroke_starts = _two_stroke_anchors()
    plan = build_sample_plan(anchors, stroke_starts, [0, 11, 12, 23, 99], 100)
    legacy_slices, legacy_alloc, _ = stroke_sample_plan(anchors, stroke_starts, 100)
    assert plan.slices == legacy_slices
    assert plan.alloc == legacy_alloc
    assert plan.drop_rows == []
