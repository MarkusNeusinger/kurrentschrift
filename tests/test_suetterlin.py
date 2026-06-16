"""Sütterlin (Gleichzug) derivation: skeleton-locked geometry, constant nib.

The headline claim of `core.suetterlin` is that a constant-width glyph is the
crop's skeleton buffered by one radius, so the rendered silhouette hugs the ink
by construction. These tests assert exactly that on synthetic constant-width
charts: the width is genuinely constant, the silhouette scores a high IoU
against the crop, pen lifts split strokes, and sharp turns become corner knots.
"""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from core.suetterlin import (
    _constant_nib_radius,
    _modal_half_width,
    _smooth_snapped_strokes,
    _verticalize_downstrokes,
    canonical_suetterlin_from_path,
    canonical_suetterlin_from_raw_path_only,
)


def _save(img: np.ndarray, tmp_path, name: str = "chart.png") -> str:
    out = tmp_path / name
    Image.fromarray((img * 255).astype(np.uint8), mode="L").save(out)
    return str(out)


@pytest.fixture
def l_shape_chart_path(tmp_path) -> str:
    """A constant-width (16px) right-angle 'L': a downstroke into a footstroke.

    Vertical bar x∈[392,408), y∈[200,600); horizontal bar y∈[584,600),
    x∈[392,700). The 90° corner at the bottom-left is the kink the derivation
    must keep crisp.
    """
    img = np.ones((800, 800), dtype=np.float32)
    img[200:600, 392:408] = 0.05
    img[584:600, 392:700] = 0.05
    return _save(img, tmp_path)


@pytest.fixture
def l_shape_bbox() -> dict:
    return {
        "y0": 150,
        "y1": 650,
        "x0": 300,
        "x1": 750,
        "mask_strokes": [],
        "baseline_y": 600,
        "midband_y": 500,
        "n_anchors": 40,
    }


def _vertical_path(num: int = 40, x_global: int = 400) -> list[dict]:
    """A rough downstroke on the synthetic vertical bar."""
    return [{"x": float(x_global), "y": float(205 + 390 * i / (num - 1))} for i in range(num)]


def _l_shape_path(num: int = 30) -> list[dict]:
    """Down the stem, then right along the foot — one continuous pen-stroke."""
    down = [{"x": 400.0, "y": float(210 + 382 * i / (num - 1))} for i in range(num)]
    foot = [{"x": float(400 + 290 * i / (num - 1)), "y": 592.0} for i in range(num)]
    return down + foot


def test_width_is_constant(synthetic_chart_path, synthetic_bbox):
    canon = canonical_suetterlin_from_path(
        raw_path=_vertical_path(), bbox=synthetic_bbox, chart_path=synthetic_chart_path, glyph="l", position="initial"
    )
    hw = canon["half_widths"]
    assert len(hw) == len(canon["anchors"])
    # Gleichzug: every half-width is the same stamped nib radius.
    assert max(hw) - min(hw) < 1e-9
    assert hw[0] > 0.0
    assert canon["trace_meta"]["method"] == "suetterlin-gleichzug"
    assert canon["trace_meta"]["nib_radius_px"] > 0.0


def test_silhouette_hugs_the_crop(synthetic_chart_path, synthetic_bbox):
    canon = canonical_suetterlin_from_path(
        raw_path=_vertical_path(), bbox=synthetic_bbox, chart_path=synthetic_chart_path, glyph="l", position="initial"
    )
    quality = canon["trace_meta"]["quality"]
    assert quality is not None
    # The silhouette is the skeleton buffered by one radius — it overlaps the
    # 16px ink bar almost perfectly (round caps cost a sliver at the ends).
    assert quality["iou"] > 0.85


def test_anchors_lock_to_the_skeleton(synthetic_chart_path, synthetic_bbox):
    # A deliberately sloppy Weg, drifting up to ~5px off the bar centre, must
    # still snap back onto the medial axis (x≈400 in chart coords).
    rng = np.random.default_rng(0)
    raw = [{"x": 400.0 + rng.uniform(-5, 5), "y": float(205 + 390 * i / 39)} for i in range(40)]
    canon = canonical_suetterlin_from_path(
        raw_path=raw, bbox=synthetic_bbox, chart_path=synthetic_chart_path, glyph="l", position="initial"
    )
    xs = np.array([px for px, _ in canon["trace_meta"]["pixel_anchors"]])
    # The bar's medial axis sits at x≈399–400; snapped anchors hug it tightly
    # despite the ±5px hand wobble in the drawn path.
    assert np.abs(xs - 399.5).max() < 2.0


def test_pen_lift_splits_strokes(synthetic_chart_path, synthetic_bbox):
    first = [{"x": 400.0, "y": float(210 + 180 * i / 9)} for i in range(10)]
    first[-1]["pen_up"] = True
    second = [{"x": 400.0, "y": float(410 + 180 * i / 9)} for i in range(10)]
    canon = canonical_suetterlin_from_path(
        raw_path=first + second, bbox=synthetic_bbox, chart_path=synthetic_chart_path, glyph="u", position="initial"
    )
    assert len(canon["trace_meta"]["stroke_starts"]) == 2


def test_sharp_corner_becomes_a_knot(l_shape_chart_path, l_shape_bbox):
    canon = canonical_suetterlin_from_path(
        raw_path=_l_shape_path(), bbox=l_shape_bbox, chart_path=l_shape_chart_path, glyph="L", position="initial"
    )
    # The 90° turn at the foot is a within-stroke reversal → at least one corner.
    assert len(canon["trace_meta"]["corner_anchors"]) >= 1
    # And the cornered silhouette still hugs the L-shaped ink.
    assert canon["trace_meta"]["quality"]["iou"] > 0.8


def test_nib_radius_uses_histogram_mode():
    # 250 single-stroke half-widths at the true nib (8), plus merged double/
    # triple tails at 14 and 20 — exactly the t/s case where strokes run
    # together. The median is dragged up into the tail; the mode is not.
    vals = np.concatenate([np.full(250, 8.0), np.full(130, 14.0), np.full(130, 20.0)])
    assert np.median(vals) >= 13.0  # a plain median would over-stamp the nib
    assert abs(_modal_half_width(vals) - 8.0) < 1.0

    # Through the public helper on a (skeleton, width_map) pair: the modal width
    # recovers the nib radius despite the merged-region tail.
    skel = np.ones((1, vals.size), dtype=bool)
    width_map = np.zeros((1, vals.size), dtype=float)
    width_map[0, :] = vals
    assert abs(_constant_nib_radius(skel, width_map, skel) - 8.0) < 1.0


@pytest.fixture
def merged_double_chart_path(tmp_path) -> str:
    """A thin single bar (the nib reference) beside a wide merged double bar.

    The 16px bar (x∈[340,356)) fixes the nib radius at ~8 via the histogram
    mode; the 32px bar (x∈[400,432)) is what two pen-strokes look like once
    their ink has merged into one block — its medial axis is a single central
    line at x≈416 reading a half-width of ~16. Tracing that block as a hairpin
    (down one side, up the other) must follow its two edges, not collapse onto
    the centerline.
    """
    img = np.ones((800, 800), dtype=np.float32)
    img[150:560, 340:356] = 0.05  # 16px single-stroke nib reference
    img[200:500, 400:432] = 0.05  # 32px merged double stroke
    return _save(img, tmp_path)


@pytest.fixture
def merged_double_bbox() -> dict:
    return {
        "y0": 120,
        "y1": 600,
        "x0": 320,
        "x1": 460,
        "mask_strokes": [],
        "baseline_y": 500,
        "midband_y": 400,
        "n_anchors": 60,
    }


def _merged_hairpin_path() -> list[dict]:
    """Down the left of the wide block and back up the right — one pen-stroke.

    Drawn with only a mild lateral bias (x≈412 down, x≈420 up, the block centre
    being 416) to show the edge-follow PLACES each pass at its edge from the
    ink, taking only the side from the drawing.
    """
    down = [{"x": 412.0, "y": float(212 + 274 * i / 29)} for i in range(30)]
    turn = [{"x": float(414 + 4 * i / 2), "y": 492.0} for i in range(3)]
    up = [{"x": 420.0, "y": float(486 - 274 * i / 29)} for i in range(30)]
    return down + turn + up


def test_merged_double_stroke_follows_edges(merged_double_chart_path, merged_double_bbox):
    canon = canonical_suetterlin_from_path(
        raw_path=_merged_hairpin_path(),
        bbox=merged_double_bbox,
        chart_path=merged_double_chart_path,
        glyph="t",
        position="initial",
    )
    # The thin bar fixes the nib at ~8 despite the wide bar's ~16 readings.
    assert abs(canon["trace_meta"]["nib_radius_px"] - 8.0) < 2.0

    xs = np.array([px for px, _ in canon["trace_meta"]["pixel_anchors"]])
    left = xs[xs < 412]
    right = xs[xs > 420]
    # Both passes exist and sit out at their own edge-inset (centre 416 ∓ nib 8
    # ≈ 408 / 424) — NOT collapsed onto the shared centerline at x≈416.
    assert left.size and right.size
    assert abs(left.mean() - 408.0) < 3.0
    assert abs(right.mean() - 424.0) < 3.0
    # Two 8-radius passes at ±8 from centre span the full 32px block; a centre
    # collapse would leave the spread near zero.
    assert xs.max() - xs.min() > 12.0


@pytest.fixture
def plus_cross_chart_path(tmp_path) -> str:
    """A constant-width '+' — a vertical stroke crossed by a horizontal one.

    Vertical bar x∈[400,416), y∈[200,560); horizontal bar y∈[372,388),
    x∈[300,560). Both are 16px (nib ~8). The overlap blob at the crossing reads
    a half-width above the nib, but it is a Kreuzung, not a merge: each stroke
    must pass straight through at one nib thickness, no widening, no shove.
    """
    img = np.ones((800, 800), dtype=np.float32)
    img[200:560, 400:416] = 0.05
    img[372:388, 300:560] = 0.05
    return _save(img, tmp_path)


@pytest.fixture
def plus_cross_bbox() -> dict:
    return {
        "y0": 180,
        "y1": 580,
        "x0": 340,
        "x1": 540,
        "mask_strokes": [],
        "baseline_y": 560,
        "midband_y": 460,
        "n_anchors": 60,
    }


def test_crossing_is_not_edge_split(plus_cross_chart_path, plus_cross_bbox):
    # Vertical stroke (drawn with a mild left bias) then horizontal stroke.
    vert = [{"x": 406.0, "y": float(210 + 340 * i / 39)} for i in range(40)]
    vert[-1]["pen_up"] = True
    horiz = [{"x": float(310 + 240 * i / 39), "y": 380.0} for i in range(40)]
    canon = canonical_suetterlin_from_path(
        raw_path=vert + horiz, bbox=plus_cross_bbox, chart_path=plus_cross_chart_path, glyph="t", position="initial"
    )
    assert abs(canon["trace_meta"]["nib_radius_px"] - 8.0) < 2.0

    starts = canon["trace_meta"]["stroke_starts"]
    assert len(starts) == 2
    anchors = np.array(canon["trace_meta"]["pixel_anchors"])
    vert_xs = anchors[starts[0] : starts[1], 0]
    # The vertical stroke holds the centerline (x≈408) the whole way THROUGH the
    # crossing — the wide overlap blob did not pull it toward an edge (an
    # unsuppressed offset would dip it by the EDT excess, a few px off 408).
    assert np.abs(vert_xs - 408.0).max() < 2.5
    # And the rendered '+' still hugs the ink at one nib thickness.
    assert canon["trace_meta"]["quality"]["iou"] > 0.8


def test_verticalize_pulls_slanted_run_to_true_vertical():
    # A straight downstroke leaning ~8° from vertical (within the 15° gate) over
    # 1.6 x-heights — a real Sütterlin stem. Verticalisation must pull its core
    # onto a single x (true 90°) while never moving y.
    unit_px = 60.0
    n = 80
    ys = 100.0 + np.linspace(0.0, 1.6 * unit_px, n)
    xs = 200.0 + np.tan(np.deg2rad(8.0)) * (ys - ys[0])
    anchors = np.column_stack([xs, ys])
    out = _verticalize_downstrokes(anchors, [0], unit_px)
    core = slice(15, -15)  # drop the eased ends
    assert anchors[core, 0].max() - anchors[core, 0].min() > 4.0  # the input genuinely slants
    assert out[core, 0].max() - out[core, 0].min() < 0.5  # the core is now a true vertical
    assert np.allclose(out[:, 1], anchors[:, 1])  # y is never moved


def test_verticalize_leaves_a_curve_round():
    # A clear arc (a quarter-circle bowl) is NOT a downstroke: it fails the
    # straightness gate and must come back essentially unchanged, not flattened.
    unit_px = 60.0
    t = np.linspace(0.0, np.pi / 2, 60)
    anchors = np.column_stack([200.0 + 40.0 * np.cos(t), 100.0 + 40.0 * np.sin(t)])
    out = _verticalize_downstrokes(anchors, [0], unit_px)
    assert np.allclose(out, anchors, atol=1e-6)


def test_smoothing_preserves_endpoints_and_corners():
    unit_px = 50.0
    rng = np.random.default_rng(2)
    n = 60
    # Down the stem then right along the foot (a 90° corner), with ~1px skeleton
    # jitter on the off-axis coordinate of each leg.
    down = np.column_stack([100.0 + rng.normal(0, 1.0, n), np.linspace(0.0, 2 * unit_px, n)])
    foot = np.column_stack([np.linspace(100.0, 100.0 + 2 * unit_px, n), 2 * unit_px + rng.normal(0, 1.0, n)])
    corner = np.array([100.0, 2 * unit_px])
    stroke = np.vstack([down, foot])
    out = _smooth_snapped_strokes([stroke], unit_px)
    assert len(out) == 1
    sm = out[0]
    # Endpoints are pinned (round caps not eroded inward).
    assert np.hypot(*(sm[0] - stroke[0])) < 1.5
    assert np.hypot(*(sm[-1] - stroke[-1])) < 1.5
    # The 90° corner survives — smoothing splits there, so a point still lands on it.
    assert np.hypot(sm[:, 0] - corner[0], sm[:, 1] - corner[1]).min() < 0.15 * unit_px


def test_from_raw_path_only_roundtrip(synthetic_chart_path, synthetic_bbox):
    canon = canonical_suetterlin_from_path(
        raw_path=_vertical_path(), bbox=synthetic_bbox, chart_path=synthetic_chart_path, glyph="l", position="initial"
    )
    again = canonical_suetterlin_from_raw_path_only(
        glyph_row={"raw_path": canon["raw_path"], "glyph": "l", "position": "initial"},
        bbox=synthetic_bbox,
        chart_path=synthetic_chart_path,
        n_anchors=40,
    )
    assert again["glyph"] == "l"
    assert again["trace_meta"]["method"] == "suetterlin-gleichzug"
    assert len(again["anchors"]) >= 2
