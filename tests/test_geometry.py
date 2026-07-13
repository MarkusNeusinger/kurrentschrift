"""Direct unit tests for the reference-free geometry primitives (core/geometry.py).

These are pure, deterministic array-math helpers shared by the Sütterlin
naturalness metric (and, potentially, the generator). They were previously only
exercised transitively via the quality tests; pinning them here with known
inputs/outputs de-risks the upcoming core-dedup refactor (issue #185).
"""

from __future__ import annotations

import numpy as np
import pytest

from core.geometry import (
    acute_angle_between,
    arc_length,
    detect_crossing_passages,
    detect_retrace_pairs,
    detect_vertical_runs,
    discrete_curvature,
    fit_line_tls,
    point_line_perp_distance,
    run_is_straight_residual,
    stroke_bounds,
    unit_tangents,
)


# --------------------------------------------------------------- unit_tangents


def test_unit_tangents_axis_aligned_lines():
    horiz = unit_tangents(np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]]))
    assert np.allclose(horiz, [[1.0, 0.0]] * 3)
    vert = unit_tangents(np.array([[0.0, 0.0], [0.0, 1.0], [0.0, 2.0]]))
    assert np.allclose(vert, [[0.0, 1.0]] * 3)


def test_unit_tangents_are_unit_length():
    pts = np.array([[0.0, 0.0], [1.0, 1.0], [3.0, 2.0], [3.0, 5.0]])
    t = unit_tangents(pts)
    assert np.allclose(np.hypot(t[:, 0], t[:, 1]), 1.0)


def test_unit_tangents_degenerate_returns_zeros():
    assert np.array_equal(unit_tangents(np.array([[1.0, 2.0]])), np.zeros((1, 2)))
    assert unit_tangents(np.empty((0, 2))).shape == (0, 2)


# ------------------------------------------------------------------ arc_length


def test_arc_length_cumulative_chord():
    pts = np.array([[0.0, 0.0], [3.0, 0.0], [3.0, 4.0]])
    assert np.allclose(arc_length(pts), [0.0, 3.0, 7.0])


def test_arc_length_degenerate():
    assert np.array_equal(arc_length(np.array([[1.0, 1.0]])), np.zeros(1))
    assert arc_length(np.empty((0, 2))).shape == (0,)


# ----------------------------------------------------------- discrete_curvature


def test_discrete_curvature_straight_is_zero():
    pts = np.column_stack([np.zeros(10), np.linspace(0.0, 9.0, 10)])
    assert np.allclose(discrete_curvature(pts, unit_px=1.0), 0.0)


def test_discrete_curvature_right_angle_value():
    # A 90° corner: interior turning angle π/2, unit adjacent segments → κ = π/2.
    pts = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]])
    kappa = discrete_curvature(pts, unit_px=1.0)
    assert kappa[0] == 0.0 and kappa[-1] == 0.0  # endpoints undefined → 0
    assert kappa[1] == pytest.approx(np.pi / 2)


def test_discrete_curvature_scales_with_unit_px():
    pts = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]])
    assert discrete_curvature(pts, unit_px=2.0)[1] == pytest.approx(np.pi)


def test_discrete_curvature_guards():
    assert np.array_equal(discrete_curvature(np.array([[0.0, 0.0], [1.0, 1.0]]), 1.0), np.zeros(2))
    pts = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]])
    assert np.array_equal(discrete_curvature(pts, unit_px=0.0), np.zeros(3))


# ---------------------------------------------------- run_is_straight_residual


def test_run_is_straight_residual_zero_for_a_line():
    pts = np.column_stack([np.linspace(0.0, 10.0, 8), np.linspace(0.0, 5.0, 8)])
    assert run_is_straight_residual(pts) == pytest.approx(0.0, abs=1e-9)


def test_run_is_straight_residual_known_bow():
    # A single-point tent: chord length 2, apex 1 above the chord → residual 0.5.
    pts = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 0.0]])
    assert run_is_straight_residual(pts) == pytest.approx(0.5)


def test_run_is_straight_residual_degenerate_is_inf():
    assert run_is_straight_residual(np.array([[0.0, 0.0]])) == float("inf")
    assert run_is_straight_residual(np.array([[1.0, 1.0], [1.0, 1.0]])) == float("inf")


# ------------------------------------------------------------------ fit_line_tls


def test_fit_line_tls_recovers_direction_and_centroid():
    x = np.linspace(-5.0, 5.0, 11)
    pts = np.column_stack([x, 2.0 * x + 3.0])  # slope 2 line
    centroid, direction = fit_line_tls(pts)
    assert np.allclose(centroid, [0.0, 3.0])
    expected = np.array([1.0, 2.0]) / np.hypot(1.0, 2.0)
    assert abs(abs(np.dot(direction, expected)) - 1.0) < 1e-9  # collinear (sign-free)


def test_fit_line_tls_degenerate_defaults_to_x_axis():
    centroid, direction = fit_line_tls(np.array([[4.0, 7.0]]))
    assert np.allclose(centroid, [4.0, 7.0])
    assert np.allclose(direction, [1.0, 0.0])


# ------------------------------------------------------------ acute_angle_between


_DIAG = 1.0 / np.sqrt(2.0)


@pytest.mark.parametrize(
    ("u1", "u2", "expected"),
    [
        ((1.0, 0.0), (1.0, 0.0), 0.0),
        ((1.0, 0.0), (-1.0, 0.0), 0.0),  # unsigned: anti-parallel reads 0
        ((1.0, 0.0), (0.0, 1.0), np.pi / 2),
        ((1.0, 0.0), (_DIAG, _DIAG), np.pi / 4),  # inputs are expected unit vectors
    ],
)
def test_acute_angle_between(u1, u2, expected):
    assert acute_angle_between(np.array(u1), np.array(u2)) == pytest.approx(expected)


# ------------------------------------------------------- point_line_perp_distance


def test_point_line_perp_distance():
    centroid, direction = np.array([0.0, 0.0]), np.array([1.0, 0.0])
    assert point_line_perp_distance(np.array([5.0, 3.0]), centroid, direction) == pytest.approx(3.0)
    assert point_line_perp_distance(np.array([5.0, 0.0]), centroid, direction) == pytest.approx(0.0)


# ------------------------------------------------------------------ stroke_bounds


def test_stroke_bounds_no_starts_is_one_stroke():
    assert stroke_bounds(10, None) == [(0, 10)]
    assert stroke_bounds(10, []) == [(0, 10)]


def test_stroke_bounds_splits_and_sanitises():
    assert stroke_bounds(10, [4]) == [(0, 4), (4, 10)]
    # 0 is implicit, duplicates collapse, out-of-range starts are dropped.
    assert stroke_bounds(10, [0, 4, 4, 7, 10, 99, -3]) == [(0, 4), (4, 7), (7, 10)]


# ---------------------------------------------------------- detect_vertical_runs


def test_detect_vertical_runs_finds_a_straight_downstroke():
    sy = np.linspace(0.0, 60.0, 20)  # 60px > 0.45 * unit_px (=45)
    sx = np.full(20, 5.0)
    runs = detect_vertical_runs(sx, sy, None, unit_px=100.0)
    assert runs == [(0, 19)]


def test_detect_vertical_runs_ignores_horizontal():
    sx = np.linspace(0.0, 60.0, 20)
    sy = np.full(20, 5.0)
    assert detect_vertical_runs(sx, sy, None, unit_px=100.0) == []


def test_detect_vertical_runs_respects_pen_lifts():
    # Two separate vertical strokes must not bridge into one run across the lift.
    sy = np.concatenate([np.linspace(0.0, 60.0, 20), np.linspace(0.0, 60.0, 20)])
    sx = np.concatenate([np.full(20, 5.0), np.full(20, 40.0)])
    runs = detect_vertical_runs(sx, sy, [20], unit_px=100.0)
    assert runs == [(0, 19), (20, 39)]


# ------------------------------------------------------- detect_crossing_passages


def test_detect_crossing_passages_flags_an_x():
    # A horizontal stroke crossed by a vertical one at the origin.
    a = np.column_stack([np.linspace(-10.0, 10.0, 41), np.zeros(41)])
    b = np.column_stack([np.zeros(41), np.linspace(-10.0, 10.0, 41)])
    pts = np.vstack([a, b])
    passages = detect_crossing_passages(pts[:, 0], pts[:, 1], [len(a)], prox_px=2.0)
    assert passages, "the transversal crossing must be detected"
    # Each passage's blanked blob sits near the crossing (origin).
    for _lo, _hi, blank_lo, blank_hi, partner in passages:
        mid = (blank_lo + blank_hi) // 2
        assert np.hypot(*pts[mid]) < 3.0
        assert partner >= 0


def test_detect_crossing_passages_none_for_a_single_line():
    a = np.column_stack([np.linspace(-10.0, 10.0, 41), np.zeros(41)])
    assert detect_crossing_passages(a[:, 0], a[:, 1], None, prox_px=2.0) == []


# ---------------------------------------------------------- detect_retrace_pairs


def test_detect_retrace_pairs_matches_an_out_and_back():
    # Two close anti-parallel passes over the same column (a doubled stem).
    y = np.linspace(0.0, 10.0, 21)
    up = np.column_stack([np.zeros(21), y])
    down = np.column_stack([np.full(21, 0.5), y[::-1]])
    pts = np.vstack([up, down])
    idx, partner = detect_retrace_pairs(pts[:, 0], pts[:, 1], [len(up)], prox_px=2.0)
    assert len(idx) > 0
    assert len(idx) == len(partner)
    # Every matched partner lands on the opposite pass (crosses the pen lift).
    assert np.all((idx < len(up)) != (partner < len(up)))


def test_detect_retrace_pairs_none_for_a_single_pass():
    y = np.linspace(0.0, 10.0, 21)
    pts = np.column_stack([np.zeros(21), y])
    idx, partner = detect_retrace_pairs(pts[:, 0], pts[:, 1], None, prox_px=2.0)
    assert len(idx) == 0 and len(partner) == 0


def test_detect_retrace_pairs_guards():
    idx, partner = detect_retrace_pairs(np.array([0.0]), np.array([0.0]), None, prox_px=2.0)
    assert len(idx) == 0 and len(partner) == 0
