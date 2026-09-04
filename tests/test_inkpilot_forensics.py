"""Unit tests for the Lotse departure sensor — no fixtures, no bench.

The parts worth pinning are the ones a wrong answer would quietly poison:
the signed distance from the inked BODY (not from the skeleton), the field
read at points that fall off the crop, and the blame rule that decides
whether a departure was inherited from the map or made by the ride.
"""

import numpy as np
import pytest


pytest.importorskip("scipy")

from tools.inkpilot.forensics import (
    CAUSE_FORCED,
    CAUSE_RAIL,
    JumpEvent,
    _assemble_traced,
    blame,
    ink_slack_field,
    sample_field,
)
from tools.inkpilot.pilot import PilotGraph


def bar_skeleton(size: int = 41) -> np.ndarray:
    """A single horizontal skeleton bar across the middle of the image."""
    skel = np.zeros((size, size), dtype=bool)
    skel[size // 2, 5 : size - 5] = True
    return skel


def test_slack_is_measured_from_the_ink_body_not_the_skeleton() -> None:
    skel = bar_skeleton()
    widths = np.zeros_like(skel, dtype=float)
    widths[skel] = 3.0  # a body 3 px thick on either side of the bar
    field = ink_slack_field(skel, widths)
    mid = skel.shape[0] // 2
    # On the bar and one body radius away: inside the ink (negative slack).
    assert field[mid, 20] == pytest.approx(-3.0)
    assert field[mid - 2, 20] < 0.0
    # Just past the body: outside, and the slack grows with the distance.
    assert field[mid - 4, 20] == pytest.approx(1.0)
    assert field[mid - 6, 20] == pytest.approx(3.0)


def test_without_widths_the_body_collapses_to_the_skeleton() -> None:
    skel = bar_skeleton()
    field = ink_slack_field(skel, None)
    mid = skel.shape[0] // 2
    assert field[mid, 20] == pytest.approx(0.0)
    assert field[mid - 3, 20] == pytest.approx(3.0)
    assert (field >= 0.0).all()


def test_sample_field_reads_points_and_penalises_leaving_the_crop() -> None:
    skel = bar_skeleton()
    widths = np.zeros_like(skel, dtype=float)
    widths[skel] = 2.0
    field = ink_slack_field(skel, widths)
    mid = float(skel.shape[0] // 2)
    inside, outside = sample_field(field, np.asarray([[20.0, mid], [20.0, mid - 5.0]]))
    assert inside < 0.0
    assert outside > 0.0
    # A point well off the crop is scored as off the ink, not clamped to it.
    far = sample_field(field, np.asarray([[20.0, -30.0]]))[0]
    assert far > outside


def test_rail_availability_survives_a_forced_window_label() -> None:
    """The reason `no_rail` is a flag and not a cause.

    A forced-window sample is pushed into the bridge state by construction and
    always carries the `forced_window` cause. Its rail availability therefore
    has to be recorded separately, or a sample the map placed over blank paper
    inside a window would be invisible to the count.
    """
    pg = PilotGraph(bar_skeleton())
    samples = np.asarray([[20.0, 20.0], [20.0, 5.0]])  # on the bar, then far off it
    seq = [None, None]  # forced windows ride the map: both are bridge states
    causes, pinned = [CAUSE_FORCED, CAUSE_FORCED], np.zeros(2, dtype=bool)
    no_rail_in = np.asarray([False, True])

    _, out_causes, _, out_no_rail = _assemble_traced(pg, samples, seq, None, causes, pinned, no_rail_in)

    assert out_causes == [CAUSE_FORCED, CAUSE_FORCED]  # the cause still names the mechanism
    assert out_no_rail == [False, True]  # and the empty boarding neighbourhood survives it


def test_ride_points_are_never_flagged_as_railless() -> None:
    pg = PilotGraph(bar_skeleton())
    loc = pg.locs[0]
    samples = np.asarray([[20.0, 20.0], [21.0, 20.0]])
    _, out_causes, _, out_no_rail = _assemble_traced(
        pg, samples, [loc, loc], None, [CAUSE_RAIL, CAUSE_RAIL], np.zeros(2, dtype=bool), np.ones(2, dtype=bool)
    )
    assert set(out_causes) == {CAUSE_RAIL}
    assert not any(out_no_rail)  # a point ON a rail cannot lack one


def _event(**kw) -> JumpEvent:
    base = {"word": "w", "stroke": 0, "first": 0, "last": 1, "cause": "double_zone"}
    return JumpEvent(**{**base, **kw})


def test_blame_calls_a_departure_inherited_when_the_map_was_already_out() -> None:
    e = _event(max_slack_xh=0.20, map_slack_xh=0.20, modifiers={"pin": 2})
    assert blame(e) == "inherited"


def test_blame_names_the_mechanism_that_exceeded_the_map() -> None:
    assert blame(_event(max_slack_xh=0.20, map_slack_xh=0.02, modifiers={"pin": 2})) == "pin"
    assert blame(_event(max_slack_xh=0.20, map_slack_xh=0.02, modifiers={"untwist": 1})) == "untwist"
    assert blame(_event(max_slack_xh=0.20, map_slack_xh=0.02, modifiers={})) == "ride"
    # The mirror outranks the pin when both touched the run.
    both = _event(max_slack_xh=0.20, map_slack_xh=0.02, modifiers={"pin": 1, "untwist": 1})
    assert blame(both) == "untwist"


def test_blame_tolerance_is_the_boundary_not_a_gate() -> None:
    e = _event(max_slack_xh=0.05, map_slack_xh=0.035, modifiers={"pin": 1})
    assert blame(e, tol_xh=0.02) == "inherited"
    assert blame(e, tol_xh=0.01) == "pin"
