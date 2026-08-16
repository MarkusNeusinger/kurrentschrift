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
