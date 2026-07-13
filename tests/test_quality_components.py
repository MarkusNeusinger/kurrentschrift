"""Per-component isolation tests for the Sütterlin naturalness metric.

Each test pins the *direction* of one term (more vertical → higher, jaggier →
lower, …) on hand-built sample arrays — no fixtures, no DB. The decay constants
are calibration targets, so absolute scores are not asserted; only monotonicity
and applicability (a missing feature is not applicable, never an exception).
"""

from __future__ import annotations

import numpy as np
import pytest

from core.quality_suetterlin import (
    _locally_straight_mask,
    centerline_smoothness,
    corner_crispness,
    crossing_collinearity,
    retrace_fidelity,
    suetterlin_quality_for_glyph,
    suetterlin_quality_metrics,
    verticality,
)


UNIT_PX = 100.0


# ------------------------------------------------------------------ smoothness


def test_smoothness_straight_beats_zigzag():
    sy = np.linspace(0.0, 100.0, 80)
    straight = centerline_smoothness(np.full(80, 50.0), sy, [0], [], UNIT_PX)
    zigzag = centerline_smoothness(50.0 + 4.0 * (-1.0) ** np.arange(80), sy, [0], [], UNIT_PX)
    assert straight > 0.95
    assert zigzag < straight


def test_smoothness_does_not_penalise_a_declared_corner():
    """A sharp reversal at a declared corner is intentional, not a Zacke."""
    down = np.column_stack([np.full(60, 0.0), np.linspace(0.0, 60.0, 60)])
    up = np.column_stack([np.linspace(0.0, 40.0, 60), np.linspace(60.0, 20.0, 60)])
    pts = np.vstack([down, up[1:]])  # shared apex at the last 'down' point
    apex = len(down) - 1
    sx, sy = pts[:, 0], pts[:, 1]
    with_corner = centerline_smoothness(sx, sy, [0], [apex], UNIT_PX)
    without_corner = centerline_smoothness(sx, sy, [0], [], UNIT_PX)
    assert with_corner > without_corner  # excluding the apex stops it reading as roughness
    assert with_corner > 0.9


# ------------------------------------------------------------------ verticality


def test_verticality_perfect_vertical_is_clean():
    q, n = verticality(np.full(80, 5.0), np.linspace(0.0, 100.0, 80), [0], UNIT_PX)
    assert n == 1
    assert q > 0.99


def test_verticality_leaning_run_scores_lower():
    sy = np.linspace(0.0, 100.0, 80)
    q_vert, _ = verticality(np.full(80, 5.0), sy, [0], UNIT_PX)
    leaned = 5.0 + np.tan(np.deg2rad(10.0)) * sy  # 10° lean: still detected (<15°), but not vertical
    q_lean, n_lean = verticality(leaned, sy, [0], UNIT_PX)
    assert n_lean == 1
    assert q_lean < q_vert


def test_verticality_not_applicable_for_a_horizontal_run():
    q, n = verticality(np.linspace(0.0, 100.0, 80), np.full(80, 5.0), [0], UNIT_PX)
    assert n == 0  # nothing claims to be vertical → term not applicable
    assert q == 1.0


# ------------------------------------------------------------------ corner


def _reversal(apex_arc_points: int) -> tuple[np.ndarray, np.ndarray, int]:
    """A down-then-up reversal; `apex_arc_points` extra points round the apex."""
    down = np.column_stack([np.full(60, 0.0), np.linspace(0.0, 60.0, 60)])
    if apex_arc_points:
        t = np.linspace(0.0, 1.0, apex_arc_points + 2)[1:-1]
        arc = np.column_stack([2.0 * t, 60.0 + 1.0 * t])  # a small rounded shoulder
    else:
        arc = np.empty((0, 2))
    up = np.column_stack([np.linspace(2.0, 40.0, 60), np.linspace(61.0, 20.0, 60)])
    pts = np.vstack([down, arc, up])
    apex = len(down) + (apex_arc_points // 2 if apex_arc_points else -1)
    return pts[:, 0], pts[:, 1], apex


def test_corner_sharp_beats_rounded():
    sx_s, sy_s, apex_s = _reversal(0)
    sx_r, sy_r, apex_r = _reversal(10)
    q_sharp, n_sharp = corner_crispness(sx_s, sy_s, [0], [apex_s], UNIT_PX)
    q_round, n_round = corner_crispness(sx_r, sy_r, [0], [apex_r], UNIT_PX)
    assert n_sharp == 1 and n_round == 1
    assert q_sharp > q_round


def test_corner_not_applicable_without_corners():
    q, n = corner_crispness(np.full(40, 0.0), np.linspace(0, 40, 40), [0], [], UNIT_PX)
    assert n == 0
    assert q == 1.0


# ------------------------------------------------------- locally-straight mask


def test_locally_straight_mask_flags_a_line_and_clears_a_corner():
    """The gate that confines the crossing/retrace terms to genuinely straight
    passes: a straight run reads all-True; a sharp reversal is not straight at
    the apex, so the mask must clear there."""
    line = np.column_stack([np.full(40, 5.0), np.linspace(0.0, 60.0, 40)])
    straight = _locally_straight_mask(line, [0], window_px=12.0, tol=0.1)
    assert straight.all()

    down = np.column_stack([np.full(30, 0.0), np.linspace(0.0, 30.0, 30)])
    up = np.column_stack([np.linspace(0.0, 30.0, 30), np.linspace(30.0, 0.0, 30)])
    corner = np.vstack([down, up[1:]])
    apex = len(down) - 1
    mask = _locally_straight_mask(corner, [0], window_px=12.0, tol=0.05)
    assert not mask[apex]  # the reversal apex is not "locally straight"
    assert mask[0] and mask[-1]  # the straight limbs still read straight


# ------------------------------------------------------------------ collinearity


def _crossing(kink_slope: float) -> tuple[np.ndarray, np.ndarray, list[int]]:
    """A vertical stroke (optionally kinked at the crossing) crossed by a horizontal one."""
    y = np.linspace(0.0, 100.0, 101)
    ax = np.full(101, 50.0)
    if kink_slope:
        ax = np.where(y <= 50.0, 50.0, 50.0 + (y - 50.0) * kink_slope)
    a = np.column_stack([ax, y])
    b = np.column_stack([np.linspace(0.0, 100.0, 101), np.full(101, 50.0)])
    pts = np.vstack([a, b])
    return pts[:, 0], pts[:, 1], [0, len(a)]


def test_collinearity_straight_through_beats_kinked():
    sx_c, sy_c, starts_c = _crossing(0.0)
    sx_k, sy_k, starts_k = _crossing(0.12)  # ~7° kink: within the applicability gate, but penalised
    q_col, n_col = crossing_collinearity(sx_c, sy_c, starts_c, prox_px=6.0, unit_px=UNIT_PX)
    q_kink, n_kink = crossing_collinearity(sx_k, sy_k, starts_k, prox_px=6.0, unit_px=UNIT_PX)
    assert n_col >= 1 and n_kink >= 1
    assert q_col > q_kink
    assert q_col > 0.9


def test_collinearity_no_crossing_is_not_applicable():
    q, n = crossing_collinearity(np.full(80, 5.0), np.linspace(0, 100, 80), [0], prox_px=6.0, unit_px=UNIT_PX)
    assert n == 0
    assert q == 1.0


# ------------------------------------------------------------------ retrace


def _doubled_stem_samples() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Two close anti-parallel STRAIGHT passes (a doubled stem) + the crop bar they trace."""
    y = np.linspace(12.0, 88.0, 60)
    up = np.column_stack([np.full(60, 46.0), y])
    down = np.column_stack([np.full(60, 54.0), y[::-1]])  # ~2-nib gap, anti-parallel, straight
    sx = np.r_[up[:, 0], down[:, 0]]
    sy = np.r_[up[:, 1], down[:, 1]]
    mask = np.zeros((100, 100), dtype=bool)
    mask[10:90, 40:60] = True  # the merged double-stroke ink (a 20px-wide bar)
    return sx, sy, mask


def test_retrace_fidelity_filled_beats_underfilled():
    """The render that FILLS the traced ink beats one that under-fills it (collapse/lens).

    The v2 retrace term is crop-referenced: a faithful render of the doubled stem
    covers the bar; a thin central line (the over-collapse the user rejected) leaves
    the bar's sides unrendered and must score lower. This pins the 2026-06-20
    re-baseline that inverted the old parallelism reward (coincident passes = perfect).
    """
    sx, sy, mask = _doubled_stem_samples()
    filled = np.zeros((100, 100), dtype=bool)
    filled[10:90, 40:60] = True  # covers the whole bar
    thin = np.zeros((100, 100), dtype=bool)
    thin[10:90, 48:52] = True  # collapsed: a thin central line, misses the bar's sides
    q_filled, n_filled = retrace_fidelity(
        sx, sy, [0], prox_px=20.0, unit_px=UNIT_PX, r_px=4.0, mask=mask, pred_mask=filled
    )
    q_thin, n_thin = retrace_fidelity(sx, sy, [0], prox_px=20.0, unit_px=UNIT_PX, r_px=4.0, mask=mask, pred_mask=thin)
    assert n_filled >= 3 and n_thin >= 3
    assert q_filled > q_thin
    assert q_filled > 0.9


def test_retrace_not_applicable_for_a_single_pass():
    blank = np.zeros((100, 100), dtype=bool)
    q, n = retrace_fidelity(
        np.full(80, 5.0),
        np.linspace(0, 100, 80),
        [0],
        prox_px=20.0,
        unit_px=UNIT_PX,
        r_px=4.0,
        mask=blank,
        pred_mask=blank,
    )
    assert n == 0
    assert q == 1.0


def test_retrace_excludes_passes_not_straight_over_a_stem_length():
    """A retrace must run over passes that are straight across a stem-length window.

    Two close anti-parallel STRAIGHT passes = a genuine doubled stem → applicable. The
    same two passes, now curved (so each bows out of tolerance over the stem-length
    window — like the n-like `e`'s arch limbs, which are anti-parallel and close but are
    one curve, not an out-and-back), drop to N/A. This pins the 2026-06-18 re-baseline
    that killed the `e` retrace false fire (kept across the 2026-06-20 fidelity rework).
    """
    bar = np.zeros((100, 100), dtype=bool)
    bar[0:100, 42:58] = True  # ink under the straight stem, so the region is non-empty (else N/A)
    y = np.linspace(0.0, 100.0, 120)
    stem = np.vstack([np.column_stack([np.full(120, 48.0), y]), np.column_stack([np.full(120, 52.0), y[::-1]])])
    _, n_stem = retrace_fidelity(
        stem[:, 0], stem[:, 1], [0], prox_px=20.0, unit_px=UNIT_PX, r_px=4.0, mask=bar, pred_mask=bar
    )
    assert n_stem >= 3
    bow = 12.0 * np.sin(2.0 * np.pi * y / 60.0)  # curved passes — not straight over a stem length
    arch = np.vstack([np.column_stack([48.0 + bow, y]), np.column_stack([52.0 + bow, y[::-1]])])
    _, n_arch = retrace_fidelity(
        arch[:, 0], arch[:, 1], [0], prox_px=20.0, unit_px=UNIT_PX, r_px=4.0, mask=bar, pred_mask=bar
    )
    assert n_arch == 0


# ------------------------------------------------------------------ aggregate


def _suetterlin_canonical(chart_path, bbox) -> dict:
    from core.suetterlin import canonical_suetterlin_from_path

    path = [{"x": 400.0, "y": float(200 + 400 * i / 39), "pressure": None, "t": float(i)} for i in range(40)]
    return canonical_suetterlin_from_path(
        raw_path=path, bbox=bbox, chart_path=chart_path, glyph="i", position="initial", n_anchors=20
    )


def _score(canon, bbox, chart_path):
    from core.chart import crop_with_mask, load_chart_grayscale
    from core.extract import binarize_adaptive, skeleton_and_width
    from core.quality import crop_local_anchors

    crop = crop_with_mask(load_chart_grayscale(chart_path), bbox, fill=1.0)
    mask = binarize_adaptive(crop)
    skel, width_map = skeleton_and_width(mask)
    tm = canon["trace_meta"]
    anchors_px = crop_local_anchors(tm["pixel_anchors"], bbox)
    return suetterlin_quality_metrics(
        anchors_px,
        np.asarray(tm["half_widths_px"], dtype=float),
        tm["stroke_starts"],
        mask,
        skel,
        width_map,
        unit_px=float(tm["unit_px"]),
        corner_anchors=tm.get("corner_anchors"),
    )


def test_aggregate_shape_and_bounds(synthetic_chart_path, synthetic_bbox):
    canon = _suetterlin_canonical(synthetic_chart_path, synthetic_bbox)
    q = _score(canon, synthetic_bbox, synthetic_chart_path)
    assert set(q["components"]) == {
        "smoothness",
        "verticality",
        "corner",
        "collinearity",
        "retrace",
        "coverage",
        "naturalness",
    }
    assert 0.0 <= q["loss"] <= 1.0
    assert 0.0 <= q["gate"] <= 1.0
    assert 0.0 <= q["naturalness"] <= 1.0
    # A clean vertical bar: the verticality term applies and is satisfied.
    assert q["applicable"]["vertical_runs"] >= 1
    assert q["components"]["verticality"] < 0.1


def test_aggregate_is_deterministic(synthetic_chart_path, synthetic_bbox):
    canon = _suetterlin_canonical(synthetic_chart_path, synthetic_bbox)
    assert _score(canon, synthetic_bbox, synthetic_chart_path) == _score(canon, synthetic_bbox, synthetic_chart_path)


def test_inflated_widths_lower_the_gate(synthetic_chart_path, synthetic_bbox):
    canon = _suetterlin_canonical(synthetic_chart_path, synthetic_bbox)
    good = _score(canon, synthetic_bbox, synthetic_chart_path)
    fat = {**canon, "trace_meta": {**canon["trace_meta"]}}
    fat["trace_meta"]["half_widths_px"] = [1.6 * w for w in canon["trace_meta"]["half_widths_px"]]
    fat_q = _score(fat, synthetic_bbox, synthetic_chart_path)
    assert fat_q["gate"] < good["gate"]
    assert fat_q["loss"] > good["loss"]


def test_stored_scorer_matches_stamped_quality(synthetic_chart_path, synthetic_bbox):
    """`suetterlin_quality_for_glyph` scores a STORED template with the SAME metric
    the derivation stamped — so /quality's `stored` is comparable to `candidate`.

    The /quality endpoint used to score `stored` with the Kurrent pixel metric
    while a constant-width `candidate` came from the naturalness metric: the
    before/after delta then subtracted incomparable scales, was systematically
    negative, and never reached 0 after a /resample write-back. Scoring the
    stored geometry here must reproduce the score the canonical carries (within
    the trace_meta px-rounding), which is what makes the delta converge.
    """
    canon = _suetterlin_canonical(synthetic_chart_path, synthetic_bbox)
    stored = suetterlin_quality_for_glyph(canon, synthetic_bbox, synthetic_chart_path)
    stamped = canon["trace_meta"]["quality"]
    assert stored["score"] == pytest.approx(stamped["score"], abs=0.5)
    assert set(stored["components"]) == set(stamped["components"])
