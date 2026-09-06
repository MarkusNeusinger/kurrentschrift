"""Unit tests for `tools.pairlab.anchors` — the stranded-anchor repair.

The detector's own behaviour (marking, pen lifts, short strokes) is pinned in
`tests/test_gradlab.py`; this file pins the REPAIR: where an interpolated
anchor lands, that a run of flagged anchors is repaired as one piece, that a
declared pen lift is never crossed, and that an untouched chain comes back as
the SAME object — a caller may skip logging by identity, without comparing.

The last block pins `LOOP_AWARE_REPAIR` (LF14): that it ships off, that passing
loop ranges with the switch off changes nothing, and that with it on the
exception reaches the flagged anchors inside a range and no others.
"""

from __future__ import annotations

import numpy as np

from tools.pairlab.anchors import LOOP_AWARE_REPAIR, repair_stranded_anchors, stranded_anchors


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


def test_the_repair_never_snaps_to_ink_it_only_interpolates() -> None:
    """The distinction that separates this from the hinge rejected in §8.

    The interpolated position depends on the two unflagged NEIGHBOURS and on
    nothing else — no ink, no field, no nearest branch — so translating the
    whole chain translates the repair with it. A snap could not do that, and
    that is exactly why at a crossing it picks the wrong stroke.
    """
    pts = _even_chain()
    pts[6, 1] = 5.0
    here, _ = repair_stranded_anchors(pts, [0])
    offset = np.array([100.0, -70.0])
    there, _ = repair_stranded_anchors(pts + offset, [0])
    np.testing.assert_allclose(there - offset, here, atol=1e-12)


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


# --------------------------------------------------- LOOP_AWARE_REPAIR (LF14)


def test_the_switch_ships_off_and_loop_ranges_then_change_nothing() -> None:
    """The default is loop-BLIND, and a caller that passes ranges anyway gets
    exactly the historical repair — the property every stored occurrence of the
    `sep05` root rests on."""
    assert LOOP_AWARE_REPAIR is False
    pts = _even_chain()
    pts[5, 1] = 6.0
    blind, repaired_blind = repair_stranded_anchors(pts, [0])
    passed, repaired_passed = repair_stranded_anchors(pts, [0], [(3, 8)])
    assert repaired_blind == repaired_passed == [5]
    np.testing.assert_array_equal(blind, passed)


def test_loop_aware_leaves_a_flagged_anchor_inside_a_loop_range_alone() -> None:
    pts = _even_chain()
    pts[5, 1] = 6.0
    out, repaired = repair_stranded_anchors(pts, [0], [(3, 8)], loop_aware=True)
    assert repaired == []
    assert out is pts


def test_loop_aware_still_repairs_everything_outside_the_ranges() -> None:
    """The exception is narrow: the same call repairs an excursion one anchor
    past the range's end, so the switch cannot be read as softening the detector."""
    pts = _even_chain()
    pts[5, 1] = 6.0
    pts[9, 1] = 6.0
    out, repaired = repair_stranded_anchors(pts, [0], [(3, 8)], loop_aware=True)
    assert repaired == [9]
    np.testing.assert_allclose(out[5], pts[5], atol=1e-12)
    np.testing.assert_allclose(out[9], 0.5 * (pts[8] + pts[10]), atol=1e-12)


def test_loop_aware_without_ranges_is_the_historical_repair() -> None:
    """A glyph whose ductus closes no loop hands an EMPTY range list, and must
    then be repaired exactly as before — otherwise the arm would silently
    disable the repair for most of the alphabet."""
    pts = _even_chain()
    pts[5, 1] = 6.0
    out, repaired = repair_stranded_anchors(pts, [0], (), loop_aware=True)
    assert repaired == [5]
    np.testing.assert_allclose(out[5], [5.0, 0.0], atol=1e-12)
