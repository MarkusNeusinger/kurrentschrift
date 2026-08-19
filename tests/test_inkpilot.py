"""Unit tests for the ink pilot's ride geometry — no fixtures, no bench.

A synthetic cross (two straight skeleton bars) is enough to pin the three
behaviours the route lives on: the ride stays on the rails, the junction
decision follows the map, and bridge runs that never re-board are trimmed.
"""

import numpy as np
import pytest


pytest.importorskip("scipy")

from tools.inkpilot.pilot import PilotGraph, pilot_stroke, resample, strokes_to_word_units


def cross_skeleton(size: int = 41) -> np.ndarray:
    """A plus sign: horizontal and vertical bar crossing mid-image."""
    skel = np.zeros((size, size), dtype=bool)
    mid = size // 2
    skel[mid, 5 : size - 5] = True
    skel[5 : size - 5, mid] = True
    return skel


def test_ride_follows_the_horizontal_map() -> None:
    pg = PilotGraph(cross_skeleton())
    # The map runs straight along the horizontal bar, 1 px above it.
    xs = np.linspace(6.0, 34.0, 40)
    stroke = np.column_stack([xs, np.full_like(xs, 19.0)])
    out = pilot_stroke(pg, stroke, xh_px=10.0)
    assert len(out) >= 20
    # The ride sits ON the bar (y == 20) for essentially every point.
    on_bar = np.abs(out[:, 1] - 20.0) < 0.6
    assert on_bar.mean() > 0.95


def test_junction_choice_follows_the_map() -> None:
    pg = PilotGraph(cross_skeleton())
    # The map turns at the crossing: in along the horizontal, out UP the
    # vertical. The ride must turn too, not continue straight.
    a = np.column_stack([np.linspace(6.0, 20.0, 20), np.full(20, 20.0)])
    b = np.column_stack([np.full(20, 20.0), np.linspace(20.0, 7.0, 20)])
    out = pilot_stroke(pg, np.vstack([a, b]), xh_px=10.0)
    # It reaches the top arm of the vertical bar...
    assert out[:, 1].min() < 9.0
    # ...and never rides the right arm of the horizontal bar.
    right_arm = (out[:, 0] > 24.0) & (np.abs(out[:, 1] - 20.0) < 1.0)
    assert not right_arm.any()


def test_trailing_air_is_trimmed() -> None:
    pg = PilotGraph(cross_skeleton())
    # The map continues far past the ink's right end — pure air.
    xs = np.linspace(6.0, 60.0, 60)
    stroke = np.column_stack([xs, np.full_like(xs, 20.0)])
    out = pilot_stroke(pg, stroke, xh_px=10.0)
    # The bar ends at x = 35; the trimmed ride must not run into the air.
    assert out[:, 0].max() < 37.0


def test_mid_stroke_gap_is_bridged_not_trimmed() -> None:
    skel = cross_skeleton()
    skel[20, 15:25] = False  # break the horizontal bar in the middle
    skel[5 : 41 - 5, 20] = False  # remove the vertical bar entirely
    pg = PilotGraph(skel)
    xs = np.linspace(6.0, 34.0, 40)
    stroke = np.column_stack([xs, np.full_like(xs, 20.0)])
    out = pilot_stroke(pg, stroke, xh_px=10.0)
    # Both rail pieces are ridden and the gap between them stays connected:
    # no step may exceed the 10 px gap itself (samples near the break board
    # the rail ENDS, so the largest step is about half the gap).
    assert out[:, 0].min() < 9.0 and out[:, 0].max() > 31.0
    steps = np.hypot(*np.diff(out, axis=0).T)
    assert steps.max() < 8.0


def test_tail_runout_extends_to_the_rail_end() -> None:
    from tools.inkpilot.pilot import run_out_tails

    pg = PilotGraph(cross_skeleton())
    # A ride that stops mid-bar at x = 25; the bar's degree-1 end sits at
    # x = 35, i.e. 10 px = 1.0 xh away at xh = 10.
    ride = np.column_stack([np.arange(22.0, 26.0), np.full(4, 20.0)])
    out = run_out_tails([ride], pg, xh_px=10.0, max_units=1.2)[0]
    assert out[:, 0].max() >= 34.0
    # Too short a budget: no extension.
    out = run_out_tails([ride], pg, xh_px=10.0, max_units=0.3)[0]
    assert out[:, 0].max() < 27.0


def test_tail_runout_never_crosses_a_junction() -> None:
    from tools.inkpilot.pilot import run_out_tails

    pg = PilotGraph(cross_skeleton())
    # The ride ends BEFORE the centre junction; the forward rail ends at the
    # degree-4 node, so nothing may be appended in that direction.
    ride = np.column_stack([np.arange(8.0, 15.0), np.full(7, 20.0)])
    out = run_out_tails([ride], pg, xh_px=10.0, max_units=2.0)[0]
    assert out[:, 0].max() < 20.0


def test_units_roundtrip() -> None:
    reg = {"tx": 3.0, "ty": -2.0, "xh_px": 25.0}
    strokes = [np.asarray([[10.0, 40.0], [20.0, 30.0]])]
    units = strokes_to_word_units(strokes, reg, baseline_row=50.0)
    (u0, v0), (u1, v1) = units[0]
    assert u0 == pytest.approx((10.0 - 3.0) / 25.0, abs=1e-4)
    assert v0 == pytest.approx((50.0 - (40.0 + 2.0)) / 25.0, abs=1e-4)
    assert v1 > v0  # higher on the page = larger v


def test_resample_is_arc_regular() -> None:
    stroke = np.asarray([[0.0, 0.0], [10.0, 0.0], [10.0, 10.0]])
    out = resample(stroke, step_px=1.0)
    steps = np.hypot(*np.diff(out, axis=0).T)
    assert np.all(steps < 1.5)
    assert len(out) >= 18


def test_crossing_knots_anchor_on_the_junction() -> None:
    from tools.inkpilot.pilot import map_crossing_knots

    pg = PilotGraph(cross_skeleton())
    # Two map strokes crossing at (22, 18) — 2 px off the skeleton's
    # junction at (20, 20). The knot must carry the offset onto the node.
    a = resample(np.asarray([[12.0, 8.0], [32.0, 28.0]]), step_px=1.2)
    b = resample(np.asarray([[12.0, 28.0], [32.0, 8.0]]), step_px=1.2)
    knots = map_crossing_knots(pg, [a, b], xh_px=10.0)
    assert knots[0] and knots[1]
    _, off = knots[0][0]
    assert off == pytest.approx([-2.0, 2.0], abs=0.75)


def test_pin_map_runs_moves_the_run_onto_the_anchor() -> None:
    from tools.inkpilot.pilot import _pin_map_runs

    pg = PilotGraph(cross_skeleton())
    samples = resample(np.asarray([[12.0, 8.0], [32.0, 28.0]]), step_px=1.2)
    seq = [None] * len(samples)  # a pure map run: no boundary offsets
    run_mask = np.ones(len(samples), dtype=bool)
    mid = len(samples) // 2
    out = _pin_map_runs(pg, samples, seq, run_mask, [(mid, np.asarray([-2.0, 2.0]))])
    # One knot, no boundaries: the whole run shifts by the constant anchor
    # offset, so the former crossing point now sits on the junction.
    assert out[mid] == pytest.approx(samples[mid] + [-2.0, 2.0], abs=1e-9)
    assert out[0] == pytest.approx(samples[0] + [-2.0, 2.0], abs=1e-9)


def test_pin_map_runs_interpolates_between_knots() -> None:
    from tools.inkpilot.pilot import _pin_map_runs

    pg = PilotGraph(cross_skeleton())
    samples = np.column_stack([np.linspace(6.0, 34.0, 15), np.full(15, 19.0)])
    # Rail boundaries at both ends, one anchor knot in the middle: the run
    # must blend linearly between the three offsets instead of passing the
    # raw map through its interior (the merged-window failure of v0.9).
    seq: list = [None] * 15
    seq[0] = min(pg.locs, key=lambda loc: float(np.hypot(*(pg.px_of(loc) - samples[0]))))
    seq[-1] = min(pg.locs, key=lambda loc: float(np.hypot(*(pg.px_of(loc) - samples[-1]))))
    run_mask = np.zeros(15, dtype=bool)
    run_mask[1:-1] = True
    out = _pin_map_runs(pg, samples, seq, run_mask, [(7, np.asarray([0.0, 3.0]))])
    assert out[7, 1] == pytest.approx(22.0)
    # Beyond the anchor's plateau, towards the right boundary, the offset
    # must blend strictly between the two — not pass the raw sample through.
    assert 19.0 < out[12, 1] < 22.0


def test_untwist_removes_a_weave_pair_and_keeps_a_lone_crossing() -> None:
    from tools.inkpilot import pilot as P
    from tools.inkpilot.pilot import _chain_intersections, untwist_strokes

    # Stroke A: a straight horizontal line. Stroke B: runs parallel below it,
    # pokes across it in a short wiggle (two crossings 0.3 xh apart), then
    # much later crosses it once for real and stays above.
    xh = 10.0
    a = np.column_stack([np.linspace(0.0, 60.0, 121), np.full(121, 20.0)])
    xs = np.linspace(0.0, 60.0, 121)
    ys = np.full(121, 22.0)
    ys[(xs > 10.0) & (xs < 13.0)] = 18.0  # the weave: across and back
    ys[xs > 40.0] = 16.0  # the real crossing, far from any partner
    b = np.column_stack([xs, ys])

    def events_of(strokes):
        chain = np.vstack(strokes)
        seg = np.vstack([np.zeros((1, 2)), np.diff(chain, axis=0)])
        arc = np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))
        lift = len(strokes[0]) - 1  # the virtual segment between the strokes
        raw = _chain_intersections(chain, P.MAP_CROSSING_MIN_ARC_UNITS * xh, arc)
        return [e for e in raw if e[0] != lift and e[1] != lift]

    assert len(events_of([a, b])) == 3  # two weave events + one real crossing

    out, n = untwist_strokes([a, b], xh_px=xh, window_units=0.8)
    assert n == 1  # exactly one pair untwisted
    assert len(events_of(out)) == 1  # the lone real crossing survives
    # Direction and point count untouched; stroke A never moved.
    assert np.allclose(out[0], a)
    assert len(out[1]) == len(b)
    assert np.all(np.diff(out[1][:, 0]) >= 0.0)


def test_soll_budget_protects_a_real_close_pair_and_frees_a_weave(monkeypatch) -> None:
    from tools.inkpilot import pilot as P
    from tools.inkpilot.pilot import untwist_strokes

    # A close REAL double crossing (two crossings 0.4 xh apart, like mit's t):
    # B pokes across A and back — geometrically identical to a weave. Without
    # the budget the wide window untwists it; with soll = 2 crossings in that
    # neighbourhood it is protected. A weave with soll = 0 still falls.
    xh = 10.0
    a = np.column_stack([np.linspace(0.0, 60.0, 121), np.full(121, 20.0)])
    xs = np.linspace(0.0, 60.0, 121)
    ys = np.full(121, 22.0)
    ys[(xs > 10.0) & (xs < 14.0)] = 18.0  # the "real double" site (soll 2)
    ys[(xs > 40.0) & (xs < 44.0)] = 18.0  # the weave site (soll 0)
    b = np.column_stack([xs, ys])
    monkeypatch.setattr(P, "UNTWIST_SOLL_BUDGET", True)
    soll = np.asarray([[10.0, 20.0], [14.0, 20.0]])  # the map crosses twice at site 1
    out, n = untwist_strokes([a, b], xh_px=xh, window_units=0.8, soll_points=soll)
    assert n == 1  # only the soll-free weave fell
    kept = out[1]
    site1 = kept[(kept[:, 0] > 10.0) & (kept[:, 0] < 14.0), 1]
    site2 = kept[(kept[:, 0] > 40.0) & (kept[:, 0] < 44.0), 1]
    assert site1.min() < 19.0  # the protected double still pokes across
    assert site2.min() > 21.0  # the weave was mirrored away


def test_untwist_leaves_separate_crossings_alone() -> None:
    from tools.inkpilot.pilot import untwist_strokes

    # Two genuine crossings 2.5 xh apart — no pair within the window.
    xh = 10.0
    a = np.column_stack([np.linspace(0.0, 60.0, 121), np.full(121, 20.0)])
    xs = np.linspace(0.0, 60.0, 121)
    ys = np.where((xs > 15.0) & (xs < 40.0), 24.0, 16.0)
    b = np.column_stack([xs, ys])
    out, n = untwist_strokes([a, b], xh_px=xh, window_units=0.8)
    assert n == 0
    assert np.allclose(out[1], b)


def test_pin_map_runs_fuses_overlapping_plateaus_rigidly() -> None:
    from tools.inkpilot.pilot import _pin_map_runs

    pg = PilotGraph(cross_skeleton())
    samples = np.column_stack([np.linspace(6.0, 34.0, 24), np.full(24, 19.0)])
    seq: list = [None] * 24
    run_mask = np.ones(24, dtype=bool)
    # Two anchors three samples apart: their plateaus overlap and must fuse
    # into ONE rigid interval carrying the mean offset — a dense crossing
    # cluster translates as a whole instead of shearing (the v0.10 negative).
    knots = [(10, np.asarray([0.0, 2.0])), (13, np.asarray([0.0, 4.0]))]
    out = _pin_map_runs(pg, samples, seq, run_mask, knots)
    d10 = out[10] - samples[10]
    d13 = out[13] - samples[13]
    assert d10 == pytest.approx([0.0, 3.0], abs=1e-9)
    assert d13 == pytest.approx(d10, abs=1e-9)
