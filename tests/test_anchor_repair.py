"""Unit tests for `tools.pairlab.anchors` — the stranded-anchor repair.

The detector's own behaviour (marking, pen lifts, short strokes) is pinned in
`tests/test_gradlab.py`; this file pins the REPAIR: where an interpolated
anchor lands, that a run of flagged anchors is repaired as one piece, that a
declared pen lift is never crossed, and that an untouched chain comes back as
the SAME object — a caller may skip logging by identity, without comparing.
"""

from __future__ import annotations

import numpy as np

from tools.pairlab.anchors import repair_stranded_anchors, stranded_anchors


def _even_chain(n: int = 12, step: float = 1.0) -> np.ndarray:
    """A chain whose every step is exactly `step`, along y = 0."""
    return np.column_stack([np.arange(n, dtype=float) * step, np.zeros(n)])


def _even_line(k: int = 8) -> np.ndarray:
    """`tests/test_gradlab.py`'s stroke: k anchors from x = 0 to 1 on y = 0."""
    return np.column_stack([np.linspace(0.0, 1.0, k), np.zeros(k)])


def test_an_even_chain_is_returned_untouched_and_identical() -> None:
    pts = _even_chain()
    out, repaired = repair_stranded_anchors(pts, [0])
    assert repaired == []
    assert out is pts  # identity, not just equality — absence must mean untouched


def test_a_single_needle_lands_exactly_on_the_chord() -> None:
    """The measured defect shape: out one step, back the next. The repair puts
    the anchor at the linear interpolation of its nearest unflagged stroke
    neighbours — here t = 1/2, so exactly the midpoint of anchors 5 and 7."""
    pts = _even_chain()
    pts[6, 1] = 5.0
    out, repaired = repair_stranded_anchors(pts, [0])
    assert repaired == [6]
    assert out[6].tolist() == [6.0, 0.0]
    # ...and no other anchor moved a bit
    mask = np.ones(len(pts), dtype=bool)
    mask[6] = False
    assert np.array_equal(out[mask], pts[mask])
    assert out is not pts  # the input array itself is never mutated
    assert pts[6, 1] == 5.0


def test_a_run_of_two_flagged_anchors_is_repaired_across_the_run() -> None:
    """Two consecutive stranded anchors are replaced as ONE piece: both move
    onto the chord from anchor 4 to anchor 7, each at its index-proportional
    position — never interpolated from each other."""
    pts = _even_chain()
    pts[5, 1] = 6.0
    pts[6, 1] = -6.0
    assert set(stranded_anchors(pts, [0])) == {5, 6}
    out, repaired = repair_stranded_anchors(pts, [0])
    assert repaired == [5, 6]
    np.testing.assert_allclose(out[5], [5.0, 0.0], atol=1e-12)
    np.testing.assert_allclose(out[6], [6.0, 0.0], atol=1e-12)


def test_a_declared_pen_lift_is_never_crossed() -> None:
    """The two-stroke geometry of `tests/test_gradlab.py`: a lift is the hand
    setting down elsewhere, not a discontinuity of a line — the long jump
    between the strokes is never a stranding, so nothing is repaired."""
    left, right = _even_line(), _even_line() + np.array([4.0, 3.0])
    pts = np.vstack([left, right])
    out, repaired = repair_stranded_anchors(pts, [0, 8])
    assert repaired == []
    assert out is pts
    # ...and a needle INSIDE the second stroke is repaired from that stroke's
    # own neighbours (global 8 and 10), never from across the lift.
    needled = pts.copy()
    needled[9, 1] += 5.0
    out2, repaired2 = repair_stranded_anchors(needled, [0, 8])
    assert repaired2 == [9]
    np.testing.assert_allclose(out2[9], 0.5 * (needled[8] + needled[10]), atol=1e-12)


def test_an_excursion_at_a_stroke_edge_is_left_untouched() -> None:
    """A stroke's first and last anchor have only ONE step each, so an
    excursion there is never a two-sided stranding — the repair has no
    unflagged neighbour pair to interpolate from and must leave the chain
    alone rather than half-repair it."""
    pts = _even_chain()
    pts[0, 1] = 9.0
    pts[-1, 1] = 9.0
    out, repaired = repair_stranded_anchors(pts, [0])
    assert repaired == []
    assert out is pts
