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


# ----------------------------------------------------------------- row gate (LF8)

from types import SimpleNamespace  # noqa: E402 — the row-gate block reads better as one unit

from core.laufform import (  # noqa: E402
    LAUFFORM_SPIKE_RATIO_MAX,
    anchor_spike_ratio,
    naturalness_gap,
    row_naturalness,
    spike_gate,
)


def test_spike_ratio_is_one_for_even_steps_and_the_jump_over_the_median_otherwise():
    assert anchor_spike_ratio(CHART, [0]) == pytest.approx(1.0)
    jumped = [list(p) for p in CHART]
    jumped[5] = [jumped[5][0] + 0.5, jumped[5][1]]  # one anchor leaves the line by 0.5
    ratio = anchor_spike_ratio(jumped, [0])
    steps = [math.hypot(jumped[i + 1][0] - jumped[i][0], jumped[i + 1][1] - jumped[i][1]) for i in range(10)]
    assert ratio == pytest.approx(max(steps) / sorted(steps)[5])
    assert ratio > 3.0


def test_spike_ratio_judges_each_stroke_against_its_own_median():
    """A pen lift is not a spike, and a short dot stroke is measured against its
    own steps, not the body's."""
    body = CHART
    dot = [[0.0 + i * 0.01, 1.5] for i in range(10)]  # tiny steps, far from the body
    chain = body + dot
    assert anchor_spike_ratio(chain, [0, 11]) == pytest.approx(1.0)
    spiked_dot = [list(p) for p in dot]
    spiked_dot[5] = [spiked_dot[5][0], 1.6]  # a 0.1 needle in a 0.01-step stroke
    assert anchor_spike_ratio(body + spiked_dot, [0, 11]) > 5.0
    # Pooled with a stroke that shares the dot's scale, the body's 0.11 steps
    # would hide that 0.1 needle (ratio < 1); per stroke it is a 10x spike.
    assert anchor_spike_ratio(spiked_dot, [0]) > 5.0
    assert anchor_spike_ratio(dot, [0]) == pytest.approx(1.0)


def test_spike_ratio_edge_cases():
    assert anchor_spike_ratio([], [0]) == 0.0
    assert anchor_spike_ratio([[0.0, 0.0]], [0]) == 0.0
    assert anchor_spike_ratio([[0.0, 0.0], [1.0, 0.0]], [0]) == pytest.approx(1.0)  # two anchors: exempt
    # Stands still (median step 0), then jumps: the very failure the ratio exists for.
    assert anchor_spike_ratio([[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [1.0, 0.0]], [0]) == math.inf


def test_spike_gate_reads_the_chart_stroke_starts_and_the_adopted_gate():
    chart = SimpleNamespace(anchors=CHART, half_widths=[0.05] * 11, trace_meta={"stroke_starts": [0]})
    assert LAUFFORM_SPIKE_RATIO_MAX is not None
    ok = spike_gate(chart, [[x + 0.3, y] for x, y in CHART])
    assert ok == {"ratio": pytest.approx(1.0), "max": LAUFFORM_SPIKE_RATIO_MAX, "exceeded": False}
    jumped = [list(p) for p in CHART]
    jumped[5] = [jumped[5][0] + 1.0, jumped[5][1]]
    bad = spike_gate(chart, jumped)
    assert bad["exceeded"] and bad["ratio"] > LAUFFORM_SPIKE_RATIO_MAX


def test_row_naturalness_ranks_a_jagged_stroke_below_a_smooth_one():
    """LF7's report column: the geometry-only §5 terms, sampled with the
    chart's plan; a zig-zag along the same line scores lower."""
    smooth = [[i * 0.1, 0.5] for i in range(21)]
    jagged = [[i * 0.1, 0.5 + (0.03 if i % 2 else -0.03)] for i in range(21)]
    hw = [0.05] * 21
    n_smooth = row_naturalness(smooth, hw, [0], None, 64.0)
    n_jagged = row_naturalness(jagged, hw, [0], None, 64.0)
    assert 0.0 <= n_jagged["naturalness"] < n_smooth["naturalness"] <= 1.0
    assert n_jagged["components"]["smoothness"] > n_smooth["components"]["smoothness"]
    chart = SimpleNamespace(anchors=smooth, half_widths=hw, trace_meta={"stroke_starts": [0], "unit_px": 64})
    assert naturalness_gap(chart, smooth)["gap"] == 0.0
    assert naturalness_gap(chart, jagged)["gap"] > 0.0


# ----------------------------------------------------------------- form distance (LF10)

from core.laufform import form_distance  # noqa: E402


# A straight 2-xh stroke along x, 21 anchors, nib radius 0.05 (so 1 nib radius
# = 0.05 xh); a second, separate stroke 1 xh above it for the stroke tests.
LINE = [[i * 0.1, 0.0] for i in range(21)]
NIB = 0.05
LINE_CHART = SimpleNamespace(anchors=LINE, half_widths=[NIB] * 21, trace_meta={"stroke_starts": [0]})


def test_identical_row_has_zero_form_distance():
    f = form_distance(LINE_CHART, LINE)
    assert f["nib_radius"] == pytest.approx(NIB)
    assert f["p90"] == 0.0 and f["median"] == 0.0 and f["max"] == 0.0
    assert f["correspondence"]["p90"] == 0.0


@pytest.mark.parametrize("k", [1.0, 2.5, 4.0])
def test_transverse_shift_by_k_nib_radii_measures_k(k):
    """A row shifted across the stroke by k nib radii sits k radii off the
    chart line in both directions — and the index-wise distance agrees."""
    shifted = [[x, y + k * NIB] for x, y in LINE]
    f = form_distance(LINE_CHART, shifted)
    assert f["row_to_chart"]["p90"] == pytest.approx(k, abs=1e-3)
    assert f["chart_to_row"]["p90"] == pytest.approx(k, abs=1e-3)
    assert f["median"] == pytest.approx(k, abs=1e-3) and f["p90"] == pytest.approx(k, abs=1e-3)
    assert f["correspondence"]["median"] == pytest.approx(k, abs=1e-3)


def test_sliding_along_the_stroke_is_invisible_to_the_line_distance_but_not_to_the_index_wise_one():
    """The longitudinal extent LF5/LF6 found to be the hand's own: a row slid
    along its chart line stays on the path (interior anchors at distance 0) —
    only the anchors pushed past the chart's end leave it, and the index-wise
    correspondence distance reports the full slide."""
    slid = [[x + 0.1, y] for x, y in LINE]  # one step = 2 nib radii along the line
    f = form_distance(LINE_CHART, slid)
    assert f["row_to_chart"]["median"] == 0.0
    assert f["chart_to_row"]["median"] == 0.0
    assert f["row_to_chart"]["max"] == pytest.approx(2.0, abs=1e-3)  # the last anchor overhangs the chart end
    assert f["correspondence"]["median"] == pytest.approx(2.0, abs=1e-3)


def test_local_defect_moves_p90_not_the_median():
    """A flat segment instead of the chart's line over 15 % of the anchors —
    the LF10 class (the v's diagonal): the median stays put, the p90 does not."""
    bent = [list(p) for p in LINE]
    for i in range(9, 12):
        bent[i][1] = 4 * NIB
    f = form_distance(LINE_CHART, bent)
    assert f["median"] < 0.5
    assert f["p90"] > 3.0
    assert f["p90_direction"] in ("row_to_chart", "chart_to_row")
    assert f["row_to_chart"]["argmax"] in (9, 10, 11)


def test_same_stroke_rule_does_not_let_another_stroke_rescue_a_displaced_one():
    """The E's cross stroke sitting sideways: measured against its OWN stroke
    it is far off; the nearest point of ANY stroke (sensitivity check e) may
    lie on the other stroke and hide it."""
    upper = [[i * 0.1, 1.0] for i in range(21)]
    chart = SimpleNamespace(anchors=LINE + upper, half_widths=[NIB] * 42, trace_meta={"stroke_starts": [0, 21]})
    # The second stroke of the row drops onto the first stroke's line.
    dropped = LINE + [[x, 0.0] for x, _ in upper]
    same = form_distance(chart, dropped)
    any_stroke = form_distance(chart, dropped, same_stroke=False)
    assert same["p90"] == pytest.approx(20.0, abs=1e-3)  # 1 xh / 0.05 = 20 nib radii, on the second stroke
    assert same["row_to_chart"]["values"][:21] == [0.0] * 21
    assert any_stroke["row_to_chart"]["p90"] == 0.0  # the dropped stroke lies on the first stroke's line
    assert any_stroke["chart_to_row"]["p90"] > 0.0  # but the chart's upper stroke is left uncovered


def test_polyline_and_rendered_agree_on_a_straight_stroke_and_the_count_must_match():
    f_rendered = form_distance(LINE_CHART, [[x, y + NIB] for x, y in LINE])
    f_polyline = form_distance(LINE_CHART, [[x, y + NIB] for x, y in LINE], rendered=False)
    assert f_rendered["p90"] == pytest.approx(f_polyline["p90"], abs=1e-3)
    with pytest.raises(ValueError):
        form_distance(LINE_CHART, LINE[:-1])
