"""Tests for the crossing-landmark geometry (`tools.pairlab.landmarks`).

Pure geometry in, pure geometry out — no fixtures, no DB, no network. Two halves
matching the module's: the polyline's self-intersections (which the linearised
correspondence term stands on: a wrong chord parameter puts the term's claim on
the wrong point and nothing else in the objective would object) and the ink side,
where the load-bearing behaviour is the REFUSAL to assign an ambiguous target.
"""

from __future__ import annotations

import numpy as np
import pytest

from tools.pairlab.landmarks import (
    LANDMARK_MERGE_RADIUS_UNITS,
    LANDMARK_MIN_ANGLE_DEG,
    LANDMARK_MIN_ARC_SEPARATION_UNITS,
    landmark_crossings,
    nearest_unique_point,
    polyline_self_intersections,
    skeleton_branch_points,
)


def _lemniscate(k: int = 24, height: float = 0.35) -> np.ndarray:
    """A figure eight: one clean crossing at its waist, `(0.65, 0.6)`."""
    t = np.linspace(0.0, 2.0 * np.pi, k)
    return np.column_stack([0.65 + 0.45 * np.cos(t), 0.6 + height * np.sin(2.0 * t)])


# ------------------------------------------------------- the self-intersections


def test_a_figure_eight_crosses_itself_exactly_once() -> None:
    pts = _lemniscate()
    found = polyline_self_intersections(pts)
    assert len(found) == 1
    x = found[0]
    assert x.point == pytest.approx((0.65, 0.6), abs=0.01)
    assert x.angle_deg == pytest.approx(66.3, abs=0.5)
    assert x.arc_separation == pytest.approx(1.76, abs=0.02)


def test_the_two_chord_parameters_reproduce_the_same_point() -> None:
    """The whole linearisation rests on this identity holding to float noise."""
    pts = _lemniscate()
    for x in polyline_self_intersections(pts):
        on_i = pts[x.seg_i] + x.t_i * (pts[x.seg_i + 1] - pts[x.seg_i])
        on_j = pts[x.seg_j] + x.t_j * (pts[x.seg_j + 1] - pts[x.seg_j])
        assert on_i == pytest.approx(on_j, abs=1e-12)
        assert on_i == pytest.approx(np.asarray(x.point), abs=1e-12)
        assert 0.0 <= x.t_i < 1.0 and 0.0 <= x.t_j < 1.0
        assert x.seg_j - x.seg_i >= 2


def test_a_monotone_arc_never_crosses_itself() -> None:
    t = np.linspace(0.0, 1.0, 20)
    assert polyline_self_intersections(np.column_stack([t, 0.4 * np.sin(np.pi * t)])) == []
    # …nor does a sharp V, whose two chords only meet at their shared anchor
    assert polyline_self_intersections(np.array([[0.0, 1.0], [0.5, 0.0], [1.0, 1.0]])) == []


def test_a_chord_never_bridges_a_pen_lift() -> None:
    """The straight line between two strokes was never written, so it cannot cross.

    An `H` in three pen strokes — left stem, right stem, crossbar. Exactly two
    crossings are real; the lines the hand never drew (chords 1 and 3, each
    joining one stroke's end to the next one's start) cut across later strokes
    and fabricate more.
    """
    anchors = np.array([[0.0, 2.0], [0.0, 0.0], [1.0, 2.0], [1.0, 0.0], [-0.2, 1.0], [1.2, 1.0]], dtype=float)
    lifted = polyline_self_intersections(anchors, [0, 2, 4])
    bridged = polyline_self_intersections(anchors, None)
    assert [(x.seg_i, x.seg_j) for x in lifted] == [(0, 4), (2, 4)]  # crossbar x each stem
    phantoms = {(x.seg_i, x.seg_j) for x in bridged} - {(x.seg_i, x.seg_j) for x in lifted}
    assert phantoms  # the bridging chords do invent crossings…
    assert all(1 in pair or 3 in pair for pair in phantoms)  # …and every one of them is a bridge


def test_two_strokes_cross_regardless_of_arc_separation() -> None:
    """A t's crossbar over its stem: different passes by construction.

    Arc separation is a statement about ONE pass returning to itself, so it is
    infinite (never binding) between separate strokes.
    """
    stem = np.array([[0.5, 1.5], [0.5, 0.0]])
    bar = np.array([[0.2, 1.0], [0.8, 1.0]])
    found = polyline_self_intersections(np.vstack([stem, bar]), [0, 2])
    assert len(found) == 1
    assert found[0].arc_separation == float("inf")
    assert found[0].angle_deg == pytest.approx(90.0, abs=1e-9)
    assert landmark_crossings(np.vstack([stem, bar]), [0, 2]) == found


def test_parallel_and_degenerate_chords_are_skipped() -> None:
    """A retrace lying exactly on itself has no defined intersection point."""
    line = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 0.0], [0.0, 0.0]])
    assert polyline_self_intersections(line) == []
    assert polyline_self_intersections(np.zeros((5, 2))) == []
    assert polyline_self_intersections(np.zeros((1, 2))) == []


# ------------------------------------------------------------- the two thresholds


def test_a_shallow_fold_is_not_a_landmark() -> None:
    """Below the angle threshold the intersection slides along the shared
    direction — an ill-conditioned point to hang a data term on."""
    shallow = np.array([[0.0, 0.0], [2.0, 0.02], [2.0, 0.5], [0.0, -0.02], [-0.2, 0.5]])
    found = polyline_self_intersections(shallow)
    assert len(found) == 1
    assert found[0].angle_deg < LANDMARK_MIN_ANGLE_DEG
    assert landmark_crossings(shallow) == []
    # the same crossing at a steeper angle IS a landmark
    steep = shallow.copy()
    steep[3] = [0.0, -1.0]
    assert len(landmark_crossings(steep)) == 1


def test_a_tight_wiggle_inside_one_stroke_is_not_a_landmark() -> None:
    """Arc separation separates a real return-and-cross from a fold-over."""
    scale = 0.1 * LANDMARK_MIN_ARC_SEPARATION_UNITS
    wiggle = np.array([[0.0, 0.0], [scale, scale], [2 * scale, -scale], [-scale, 0.5 * scale]])
    found = polyline_self_intersections(wiggle)
    assert found and found[0].arc_separation < LANDMARK_MIN_ARC_SEPARATION_UNITS
    assert landmark_crossings(wiggle) == []
    # the identical shape, scaled up past the threshold, qualifies
    big = wiggle * (LANDMARK_MIN_ARC_SEPARATION_UNITS / scale)
    assert len(landmark_crossings(big)) == 1


def test_co_located_crossings_merge_to_their_best_conditioned_member() -> None:
    """One geometric crossing reported by several chord pairs is ONE landmark.

    The term normalises by the landmark count, so leaving duplicates in would
    silently double the weight of a grazing crossing.
    """
    # a long chord crossed by a shallow zig-zag whose two legs both cut it
    eps = 0.2 * LANDMARK_MERGE_RADIUS_UNITS
    pts = np.array([[0.0, 0.0], [2.0, 0.0], [1.0, 1.0], [1.0 - eps, -1.0], [1.0 + eps, -1.0], [1.0, 1.0]])
    raw = [x for x in polyline_self_intersections(pts) if x.angle_deg >= LANDMARK_MIN_ANGLE_DEG]
    merged = landmark_crossings(pts)
    assert len(raw) > len(merged) >= 1
    kept = merged[0]
    assert kept.angle_deg == max(x.angle_deg for x in raw if abs(x.point[0] - kept.point[0]) < 0.1)


def test_the_frozen_thresholds_are_the_census_thresholds() -> None:
    """§13a's numbers, pinned so a later tweak has to be a deliberate one."""
    assert (LANDMARK_MIN_ANGLE_DEG, LANDMARK_MIN_ARC_SEPARATION_UNITS) == (15.0, 0.35)


# ------------------------------------------------------------------- the ink side


def _stamp_x(shape: tuple[int, int], centres, arm: int = 1) -> np.ndarray:
    skel = np.zeros(shape, dtype=bool)
    for cx, cy in centres:
        for d in range(-arm, arm + 1):
            skel[cy + d, cx + d] = True
            skel[cy - d, cx + d] = True
    return skel


def test_an_x_has_exactly_one_branch_point_at_its_centre() -> None:
    branches = skeleton_branch_points(_stamp_x((40, 40), [(20, 15)], arm=3))
    assert branches.shape == (1, 2)
    assert branches[0] == pytest.approx((20.0, 15.0))


def test_adjacent_branch_pixels_collapse_to_one_centroid() -> None:
    """A thinned crossing often leaves TWO touching branch pixels; two candidates
    for one crossing would make every assignment look ambiguous."""
    skel = np.zeros((20, 20), dtype=bool)
    r, c = 8, 10
    for pt in ((r - 1, c - 1), (r - 1, c + 1), (r, c), (r + 1, c), (r + 2, c - 1), (r + 2, c + 1)):
        skel[pt] = True
    nb_branch = skeleton_branch_points(skel)
    assert nb_branch.shape == (1, 2)
    assert nb_branch[0] == pytest.approx((float(c), r + 0.5))


def test_a_plain_line_and_an_empty_image_have_no_branch_points() -> None:
    line = np.zeros((20, 20), dtype=bool)
    line[10, 3:17] = True
    assert skeleton_branch_points(line).shape == (0, 2)
    assert skeleton_branch_points(np.zeros((20, 20), dtype=bool)).shape == (0, 2)


def test_the_nearest_candidate_is_only_taken_when_it_is_unambiguous() -> None:
    cand = np.array([[10.0, 10.0], [10.0, 14.0], [80.0, 80.0]])
    # unambiguous: nearest at 1, runner-up 4 away, margin 2
    got, reason, dist = nearest_unique_point(cand[[0, 2]], (11.0, 10.0), radius=5.0, margin=2.0)
    assert reason == "ok" and dist == pytest.approx(1.0)
    assert got == pytest.approx((10.0, 10.0))
    # ambiguous: two candidates within the margin of each other
    got, reason, _ = nearest_unique_point(cand, (10.0, 12.0), radius=5.0, margin=2.0)
    assert (got, reason) == (None, "ambiguous")
    # nothing inside the radius
    got, reason, dist = nearest_unique_point(cand, (50.0, 50.0), radius=5.0, margin=2.0)
    assert (got, reason) == (None, "no_candidate")
    assert dist > 5.0
    # no candidates at all
    assert nearest_unique_point(np.zeros((0, 2)), (0.0, 0.0), radius=5.0, margin=2.0)[1] == "no_candidate"
