"""core/laufform.py — the end blend of a Laufform row's stroke ends (LF5/LF6)."""

import math

import pytest

from core.laufform import LAUFFORM_END_WINDOW, blend_stroke_ends


# A 1-xh straight diagonal chart stroke, 11 anchors along the x axis; every
# step is hypot(0.1, 0.05) of arc — the window arithmetic reads cleanly.
CHART = [[i * 0.1, i * 0.05] for i in range(11)]
STEP = math.hypot(0.1, 0.05)
DIR = (0.1 / STEP, 0.05 / STEP)  # the stroke's direction (also its end directions)


def _assert_close(actual, expected, tol=1e-4):
    assert len(actual) == len(expected)
    worst = max(math.hypot(p[0] - q[0], p[1] - q[1]) for p, q in zip(actual, expected, strict=True))
    assert worst <= tol, f"max anchor distance {worst} > {tol}"


def _split(vec):
    """(longitudinal, transverse) components of `vec` against DIR."""
    along = vec[0] * DIR[0] + vec[1] * DIR[1]
    par = (along * DIR[0], along * DIR[1])
    return par, (vec[0] - par[0], vec[1] - par[1])


def test_default_window_is_off_until_a_gate_adopts_one():
    """§14 LF5 was rejected, LF6 is measured on the ladder {0.25, 0.5}; the
    builder blends only once a rung passed its gates."""
    assert LAUFFORM_END_WINDOW in (0.0, 0.25, 0.5)


def test_uniform_shift_is_a_fixed_point_in_both_modes():
    """Width/placement live in the Laufform: a rigidly shifted running form
    passes through the blend untouched (the chart end piece is attached at the
    Laufform's own placement, so there is nothing to blend back)."""
    shifted = [[x + 0.3, y - 0.12] for x, y in CHART]
    _assert_close(blend_stroke_ends(CHART, shifted, [0], window=0.25), shifted)
    _assert_close(blend_stroke_ends(CHART, shifted, [0], window=0.25, transverse_only=False), shifted)


def test_zero_window_returns_the_anchors_verbatim():
    drifted = [[x, y] for x, y in CHART]
    drifted[0] = [0.08, -0.1]
    _assert_close(blend_stroke_ends(CHART, drifted, [0], window=0.0), drifted)


def test_transverse_drift_is_removed_and_longitudinal_extent_kept():
    """The t case (LF6): the first anchor drifted across the stroke toward
    neighbouring ink AND slid a little along it. The transverse part goes back
    to the chart line, the longitudinal part — the lead-in's own extent —
    stays; the interior beyond the window is untouched."""
    drifted = [[x, y] for x, y in CHART]
    par, perp = _split((0.1, -0.05))
    drifted[0] = [CHART[0][0] + par[0] + perp[0], CHART[0][1] + par[1] + perp[1]]
    out = blend_stroke_ends(CHART, drifted, [0], window=0.25)
    # Edge = anchor 3 (arc 3 * STEP >= 0.25), T = 0 there. At the end w = 0:
    # chart + longitudinal residual only.
    _assert_close(out[:1], [[CHART[0][0] + par[0], CHART[0][1] + par[1]]])
    # The end now lies ON the chart's end line (transverse residual 0).
    _, perp_out = _split((out[0][0] - CHART[0][0], out[0][1] - CHART[0][1]))
    assert math.hypot(*perp_out) < 1e-4
    _assert_close(out[3:], drifted[3:])


def test_full_blend_removes_the_whole_residual_at_the_end():
    """LF5 mode: the end anchor becomes the chart's (attached at T = 0)."""
    drifted = [[x, y] for x, y in CHART]
    drifted[0] = [0.1, -0.05]
    out = blend_stroke_ends(CHART, drifted, [0], window=0.25, transverse_only=False)
    _assert_close(out[:1], CHART[:1])
    _assert_close(out[3:], drifted[3:])


def test_transverse_weight_is_linear_in_arc_length():
    """A transverse offset that begins mid-stroke fades in linearly from the
    end: weight 0 at the end, 1 from the window edge on — while a longitudinal
    offset of the same shape is kept in full."""
    perp_unit = (-DIR[1], DIR[0])
    lifted = [
        [x + (0.2 * perp_unit[0] if i >= 3 else 0.0), y + (0.2 * perp_unit[1] if i >= 3 else 0.0)]
        for i, (x, y) in enumerate(CHART)
    ]
    out = blend_stroke_ends(CHART, lifted, [0], window=0.3)
    # Edge = anchor 3 (arc 3 * STEP = 0.335 >= 0.3); T = 0.2 * perp_unit.
    expected = []
    for i in range(3):
        w = i * STEP / 0.3
        # chart + T + w * (lifted - chart - T) with lifted - chart = 0 → chart + (1 - w) * T
        expected.append([CHART[i][0] + (1 - w) * 0.2 * perp_unit[0], CHART[i][1] + (1 - w) * 0.2 * perp_unit[1]])
    _assert_close(out[:3], expected)
    _assert_close(out[3:], lifted[3:])
    slid = [
        [x + (0.2 * DIR[0] if i >= 3 else 0.0), y + (0.2 * DIR[1] if i >= 3 else 0.0)] for i, (x, y) in enumerate(CHART)
    ]
    out = blend_stroke_ends(CHART, slid, [0], window=0.3)
    # Longitudinal: T = 0.2 * DIR at the edge, residual inside = -T (along) → kept: out = chart.
    _assert_close(out[:3], CHART[:3])
    _assert_close(out[3:], slid[3:])


def test_both_ends_blend_independently():
    drifted = [[x, y] for x, y in CHART]
    perp_unit = (-DIR[1], DIR[0])
    drifted[0] = [CHART[0][0] + 0.1 * perp_unit[0], CHART[0][1] + 0.1 * perp_unit[1]]
    drifted[-1] = [CHART[-1][0] - 0.1 * perp_unit[0], CHART[-1][1] - 0.1 * perp_unit[1]]
    out = blend_stroke_ends(CHART, drifted, [0], window=0.25)
    _assert_close(out[:1], CHART[:1])
    _assert_close(out[-1:], CHART[-1:])
    _assert_close(out[4:7], drifted[4:7])


def test_strokes_are_blended_per_stroke():
    """A second stroke's start is a free end of its own (the t's loop stroke),
    and the first stroke's finish is a free end even though the next stroke
    begins right there in the anchor list."""
    chart = CHART + [[1.0 + i * 0.1, 0.5 - i * 0.05] for i in range(1, 11)]
    starts = [0, 11]
    lauf = [list(p) for p in chart]
    perp_unit = (-DIR[1], DIR[0])
    lauf[10] = [chart[10][0] + 0.1 * perp_unit[0], chart[10][1] + 0.1 * perp_unit[1]]  # first stroke's finish drifted
    lauf[11] = [chart[11][0], chart[11][1] - 0.2]  # second stroke's start drifted
    out = blend_stroke_ends(chart, lauf, starts, window=0.25)
    _assert_close(out[10:11], chart[10:11])
    # The second stroke runs at -26.6°; its start drift (0, -0.2) has a
    # longitudinal part that stays and a transverse part that goes.
    d2 = (0.1 / STEP, -0.05 / STEP)
    along = -0.2 * d2[1]
    _assert_close(out[11:12], [[chart[11][0] + along * d2[0], chart[11][1] + along * d2[1]]])
    _assert_close(out[:8], chart[:8])
    _assert_close(out[14:], chart[14:])


def test_short_stroke_keeps_the_chart_shape_at_the_laufform_placement():
    """A stroke shorter than two windows (an i-dot, a t-bar) has no interior
    to speak of: it becomes the chart shape, moved to the Laufform's mean
    position."""
    chart = [[0.0, 1.2], [0.05, 1.22], [0.1, 1.2]]
    lauf = [[0.3, 1.5], [0.42, 1.35], [0.4, 1.5]]  # a jagged dot
    out = blend_stroke_ends(chart, lauf, [0], window=0.25)
    mean_dx = sum(q[0] - c[0] for q, c in zip(lauf, chart, strict=True)) / 3
    mean_dy = sum(q[1] - c[1] for q, c in zip(lauf, chart, strict=True)) / 3
    _assert_close(out, [[x + mean_dx, y + mean_dy] for x, y in chart])


def test_anchor_count_mismatch_raises():
    with pytest.raises(ValueError):
        blend_stroke_ends(CHART, CHART[:-1], [0], window=0.25)


def test_output_is_rounded_like_every_derivation_output():
    shifted = [[x + 1 / 3, y] for x, y in CHART]
    out = blend_stroke_ends(CHART, shifted, [0], window=0.25)
    assert all(round(v, 4) == v for p in out for v in p)
    _assert_close(out, shifted)
