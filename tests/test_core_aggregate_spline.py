"""core/aggregate.py — the spline-basis median of a Laufform row (LF11).

The estimator the audit of 2026-09-02 asked for: the median moves out of the
anchor space into a smooth basis, so it can no longer carry a wobble the drawn
form never had. These tests pin what the pre-registration promised — the median
stays a median, a corner survives it, a straight line comes back straight, and
every stroke too small for a basis keeps the old estimator and SAYS so.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from core.aggregate import SPLINE_MEDIAN_DEGREE, spline_basis_median


# A 2-xh straight run along x, 60 anchors — long enough for every rung of the
# pre-registered ladder {0.08, 0.16, 0.32} to fit a basis into it.
LINE = [[i * 2.0 / 59.0, 0.0] for i in range(60)]


def _jitter(anchors, amplitude, seed):
    """The defect itself: an alternating cross-path wobble, occurrence noise on
    top. Its period is two anchors — far under every rung of the ladder."""
    rng = np.random.default_rng(seed)
    return [
        [x + float(rng.normal(0.0, 0.001)), y + (amplitude if i % 2 else -amplitude)]
        for i, (x, y) in enumerate(anchors)
    ]


def test_smoothing_removes_the_alternating_wobble_the_anchor_median_keeps():
    """The point of the arm. Every occurrence carries the same two-anchor
    zigzag, so the per-anchor median reproduces it in full — a median cannot
    outvote a deviation all occurrences share. The basis has no function that
    fine, so it cannot represent it at all."""
    stack = np.asarray([_jitter(LINE, 0.02, seed) for seed in range(9)], dtype=float)

    plain = np.median(stack, axis=0)
    smooth, notes = spline_basis_median(stack, LINE, knot_spacing=0.16)

    assert notes == []
    assert np.abs(plain[:, 1]).max() > 0.018, "the control must still carry the defect"
    # Away from the clamped ends the wobble is gone; the ends are their own
    # story, pinned below.
    assert np.abs(smooth[3:-3, 1]).max() < 0.004


def test_the_clamped_ends_are_smoothed_least():
    """A known and REPORTED property, not a surprise (§14 LF11): a clamped
    B-spline's end control point sits on the data, so an occurrence's last
    anchor is followed further than its middle ones. The pre-registration
    deliberately left the ends free — pinning them would have added a second
    end mechanism beside LF5/LF6 and blurred what this arm measures — and put
    the head/tail movement in the per-row report and the head gate (LF9) on the
    result instead. The end still improves; it just improves least."""
    stack = np.asarray([_jitter(LINE, 0.02, seed) for seed in range(9)], dtype=float)
    smooth, _ = spline_basis_median(stack, LINE, knot_spacing=0.16)

    ends = float(np.abs(smooth[[0, -1], 1]).max())
    middle = float(np.abs(smooth[3:-3, 1]).max())
    assert middle < ends < 0.02, "the ends keep more of the wobble than the middle, but not all of it"


def test_a_straight_line_survives_unchanged():
    """No wobble in, no movement out: the estimator may not invent form. A
    least-squares projection of an exactly representable curve is itself."""
    stack = np.asarray([LINE] * 5, dtype=float)
    smooth, _ = spline_basis_median(stack, LINE, knot_spacing=0.16)
    assert np.abs(smooth - np.asarray(LINE)).max() < 1e-9


def test_it_is_a_median_not_a_mean():
    """One blown-up occurrence among five must not move the row — the property
    the anchor median was chosen for has to survive the change of basis."""
    good = [LINE] * 4
    outlier = [[x, y + 0.5] for x, y in LINE]
    smooth, _ = spline_basis_median(np.asarray([*good, outlier], dtype=float), LINE, knot_spacing=0.16)
    assert np.abs(smooth[:, 1]).max() < 0.01


def test_a_corner_stays_a_corner():
    """The chart's `corner_anchors` enter the knot vector at multiplicity
    `degree`, which is exactly the multiplicity that permits a C0 kink. Without
    it the basis would round the pen's own corner off."""
    half = 30
    corner = [[i * 0.05, 0.0] for i in range(half)] + [[(half - 1) * 0.05, (i + 1) * 0.05] for i in range(half)]
    stack = np.asarray([corner] * 5, dtype=float)

    # A knot spacing coarse against the corner's own scale — that is where the
    # difference between a knot and no knot is legible at all. At the fine rungs
    # of the ladder the uniform knots crowd the corner closely enough to track
    # it by themselves; a corner knot is what keeps that true when they do not.
    kept, _ = spline_basis_median(stack, corner, None, [half - 1], knot_spacing=0.5)
    rounded, _ = spline_basis_median(stack, corner, None, [], knot_spacing=0.5)

    def turn(pts):
        a = np.asarray(pts[half - 1]) - np.asarray(pts[half - 6])
        b = np.asarray(pts[half + 4]) - np.asarray(pts[half - 1])
        return math.degrees(abs(math.atan2(*b[::-1]) - math.atan2(*a[::-1])))

    assert turn(kept) == pytest.approx(90.0, abs=5.0)
    assert turn(kept) > turn(rounded) + 10.0


def test_short_strokes_keep_the_anchor_median_and_say_so():
    """An i's dot is shorter than two knot spans. It must not be dropped, must
    not be extrapolated, and the fallback must be visible rather than silent —
    at 0.32 xh this is what the i's dot stroke really did."""
    body = [[i * 0.05, 0.0] for i in range(40)]
    dot = [[1.0, 2.0], [1.02, 2.01], [1.04, 2.0]]
    anchors = body + dot
    stack = np.asarray([anchors, [[x + 0.01, y] for x, y in anchors]], dtype=float)

    smooth, notes = spline_basis_median(stack, anchors, [len(body)], knot_spacing=0.32)

    assert len(notes) == 1
    assert "40:43" in notes[0]
    plain = np.median(stack, axis=0)
    assert np.abs(smooth[len(body) :] - plain[len(body) :]).max() < 1e-12


def test_pen_lifts_are_fitted_separately():
    """Two strokes far apart: the basis must never bridge the lift, or the row
    would gain a line the pen never drew."""
    left = [[i * 0.05, 0.0] for i in range(30)]
    right = [[5.0 + i * 0.05, 3.0] for i in range(30)]
    anchors = left + right
    stack = np.asarray([anchors] * 4, dtype=float)
    smooth, notes = spline_basis_median(stack, anchors, [len(left)], knot_spacing=0.16)
    assert notes == []
    assert np.abs(smooth - np.asarray(anchors)).max() < 1e-9


def test_it_refuses_inputs_it_cannot_parameterise():
    stack = np.asarray([LINE] * 3, dtype=float)
    with pytest.raises(ValueError, match="knot_spacing"):
        spline_basis_median(stack, LINE, knot_spacing=0.0)
    with pytest.raises(ValueError, match="anchors"):
        spline_basis_median(stack, LINE[:10], knot_spacing=0.16)
    with pytest.raises(ValueError, match="n_occurrences"):
        spline_basis_median(np.asarray(LINE, dtype=float), LINE, knot_spacing=0.16)


def test_degree_is_the_lowest_with_continuous_curvature():
    """The sensor counts curvature sign changes, so the basis must have a
    curvature to speak of."""
    assert SPLINE_MEDIAN_DEGREE == 3
