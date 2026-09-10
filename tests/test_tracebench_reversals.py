"""Tests for the paper-reversal sensor (`tools.tracebench.reversals`).

The sensor exists because the FIRST count of the same defect was withdrawn:
it counted every reversal, including the ductus' own turning points inside the
ink, and put `Galoppieren` — a word the author calls good-looking — at the top
of its table (§14 „Kette K-E `sep09`"). The properties that correction rests on
are what is pinned here: a smooth line has no reversals, a doubling back has
exactly one, a ductus corner well above the cosine threshold is not one, and
the discretisation noise a short segment carries is thinned away before any
angle is read.
"""

from __future__ import annotations

import numpy as np

from tools.tracebench.reversals import COS_MAX, MIN_SEGMENT_PX, reversal_vertices


def test_smooth_arc_has_no_reversal() -> None:
    """A gentle arc turns continuously — no pair of segments ever opposes."""
    t = np.linspace(0.0, np.pi, 60)
    arc = np.column_stack([20.0 * np.cos(t), 20.0 * np.sin(t)])
    assert len(reversal_vertices(arc)) == 0


def test_retrace_is_one_reversal_at_the_turn() -> None:
    """Out and straight back: exactly one vertex, and it is the far end."""
    out = np.column_stack([np.arange(0.0, 21.0, 2.0), np.zeros(11)])
    path = np.vstack([out, out[::-1][1:] + np.array([0.0, 0.4])])
    verts = reversal_vertices(path)
    assert len(verts) == 1
    assert verts[0][0] == 20.0


def test_a_right_angle_is_not_a_reversal() -> None:
    """A 90° cusp sits at cos 0 — far above the threshold, so it stays ductus."""
    corner = np.array([[0.0, 0.0], [10.0, 0.0], [10.0, 10.0]])
    assert COS_MAX < 0.0
    assert len(reversal_vertices(corner)) == 0


def test_short_segments_are_thinned_before_the_angle_is_read() -> None:
    """A one-pixel jitter on a straight line is discretisation, not a reversal."""
    line = np.column_stack([np.arange(0.0, 30.0, 3.0), np.zeros(10)])
    jittered = np.insert(line, 5, line[4] + np.array([-0.2 * MIN_SEGMENT_PX, 0.0]), axis=0)
    assert len(reversal_vertices(jittered)) == 0


def test_a_polyline_shorter_than_three_points_cannot_reverse() -> None:
    assert len(reversal_vertices(np.array([[0.0, 0.0], [5.0, 5.0]]))) == 0
    assert len(reversal_vertices(np.empty((0, 2)))) == 0
