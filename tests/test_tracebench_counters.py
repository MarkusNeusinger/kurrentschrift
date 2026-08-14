"""Tests for the structure counters (`tools.tracebench.counters`).

A distance cannot say "the loop is gone". These counters can, and the way they
say it has to survive two traps: the same structure must be found on both sides
by the SAME detector at the same discretisation, and a place that cannot be
assigned must be refused rather than guessed. The figure-eight of
`tests/test_pairlab_landmarks.py` is reused deliberately — it is the smallest
shape that has a crossing at all, and using the same one keeps the detector's
behaviour comparable between the two suites.

The last test pins the whole stack (frame -> classification -> metric ->
counters) on one fixed synthetic pair. It is a tripwire, not a claim about
quality: any change to any of the modules that moves a number will show up here
before it silently moves a baseline table.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.ndimage import binary_dilation

from tools.pairlab.landmarks import polyline_self_intersections
from tools.tracebench.counters import (
    RESAMPLE_STEP_UNITS,
    RETRACE_MIN_PAIRS,
    count_crossings,
    count_retraces,
    crossing_points,
    resampled_strokes,
    retrace_segments,
    structure_zones,
)
from tools.tracebench.frames import BenchFrame, classify_strokes, concat_body, concat_strokes, lift_stats, match_marks
from tools.tracebench.metric import aiou, chamfer, dtw, rasterise_strokes


def _lemniscate(k: int = 160, height: float = 0.35) -> np.ndarray:
    """A figure eight: one clean crossing at its waist, `(0.65, 0.6)`."""
    t = np.linspace(0.0, 2.0 * np.pi, k)
    return np.column_stack([0.65 + 0.45 * np.cos(t), 0.6 + height * np.sin(2.0 * t)])


def _out_and_back(x: float = 0.5, gap: float = 0.02, top: float = 1.2, k: int = 60) -> np.ndarray:
    """One pen stroke up and back down over its own ink — an `f`/`t` stem in miniature."""
    up = np.column_stack([np.full(k, x), np.linspace(0.0, top, k)])
    down = np.column_stack([np.full(k, x + gap), np.linspace(top, 0.0, k)])
    return np.vstack([up, down])


# ------------------------------------------------------------------- crossings


def test_the_figure_eight_reports_exactly_its_waist() -> None:
    found = crossing_points([_lemniscate()])
    assert len(found) == 1
    assert found[0] == pytest.approx((0.65, 0.6), abs=0.01)


def test_a_crossing_written_in_the_same_place_matches() -> None:
    same = count_crossings([_lemniscate()], [_lemniscate()])
    assert (same.ref, same.cand, same.matched, same.missing, same.spurious) == (1, 1, 1, 0, 0)
    assert same.pos_err_xh == pytest.approx(0.0, abs=1e-9)


def test_a_displaced_crossing_matches_and_carries_its_offset() -> None:
    """The §13a finding in miniature: the crossing is THERE, it sits too low."""
    shifted = count_crossings([_lemniscate()], [_lemniscate() + np.array([0.05, -0.2])])
    assert shifted.matched == 1 and shifted.missing == 0
    assert shifted.pos_err_xh == pytest.approx(np.hypot(0.05, 0.2), abs=0.01)


def test_a_lost_crossing_is_missing_and_an_invented_one_is_spurious() -> None:
    arc = np.column_stack([np.linspace(0.2, 1.1, 80), 0.6 + 0.3 * np.sin(np.linspace(0.0, np.pi, 80))])
    lost = count_crossings([_lemniscate()], [arc])
    assert (lost.ref, lost.cand, lost.matched, lost.missing, lost.spurious) == (1, 0, 0, 1, 0)
    invented = count_crossings([arc], [_lemniscate()])
    assert (invented.ref, invented.cand, invented.matched, invented.missing, invented.spurious) == (0, 1, 0, 0, 1)


def test_a_crossing_beyond_the_match_radius_is_two_defects_not_one() -> None:
    """Far enough apart and the pair stops being the same structure: missing AND spurious."""
    far = count_crossings([_lemniscate()], [_lemniscate() + np.array([0.0, -1.4])])
    assert (far.matched, far.missing, far.spurious) == (0, 1, 1)


def test_two_dense_crossings_match_a_trace_against_itself() -> None:
    # The §14 identity finding (unter/mit/linken): two TRUE crossings closer
    # than the old 0.20 xh refusal margin must still match at identity — the
    # population frame is one-to-one assignment, structurally without refusal.
    left = _lemniscate()
    right = _lemniscate() + np.asarray([0.12, 0.0])  # overlapping: waists + mutual crossings
    strokes = [left, right]
    points = crossing_points(strokes)
    gaps = np.hypot(*(points[:, None] - points[None, :]).transpose(2, 0, 1))
    np.fill_diagonal(gaps, np.inf)
    assert gaps.min() < 0.20  # the dense condition the old margin refused on
    same = count_crossings(strokes, strokes)
    assert same.ref == same.cand == same.matched >= 2
    assert (same.missing, same.spurious, same.ambiguous) == (0, 0, 0)
    assert same.pos_err_xh == pytest.approx(0.0)


def test_the_crossing_detector_never_bridges_a_pen_lift() -> None:
    """An `H` in three pen strokes: the crossbar crosses each stem and nothing else.

    Welded into ONE stroke, the two lines the hand never drew — end of a stem to
    the start of the next — cut across later strokes and fabricate crossings.
    Keeping the strokes apart is what stops the counter from grading a candidate
    on ink nobody wrote.
    """
    left = np.column_stack([np.full(30, 0.0), np.linspace(2.0, 0.0, 30)])
    right = np.column_stack([np.full(30, 1.0), np.linspace(2.0, 0.0, 30)])
    bar = np.column_stack([np.linspace(-0.2, 1.2, 30), np.full(30, 1.0)])
    assert len(crossing_points([left, right, bar])) == 2
    assert len(crossing_points([np.vstack([left, right, bar])])) > 2


# -------------------------------------------------------------------- retraces


def test_an_out_and_back_is_ONE_retrace_zone() -> None:
    """Both limbs belong to the same retrace — reporting two would break the identity gate.

    The zone sits between the two passes, and the arc counts the pen travel of
    both of them (the turn at the top is not flagged, so it is a little under
    the stroke's full length).
    """
    midpoints, arc = retrace_segments([_out_and_back()])
    assert len(midpoints) == 1
    assert midpoints[0] == pytest.approx((0.51, 0.52), abs=0.05)
    assert 1.5 < arc < 2.4  # the stroke's total arc is 2.4


def test_a_retrace_matches_itself_exactly() -> None:
    """The identity gate for this counter: same trace, same zones, zero offset."""
    trace = [_out_and_back()]
    same = count_retraces(trace, trace)
    assert (same.ref, same.cand, same.matched, same.missing, same.spurious, same.ambiguous) == (1, 1, 1, 0, 0, 0)
    assert same.pos_err_xh == pytest.approx(0.0, abs=1e-12)
    assert same.arc_ref == pytest.approx(same.arc_cand)


def test_a_candidate_that_wrote_only_one_pass_loses_the_zone() -> None:
    """The blind spot both data terms share (§3): one pass satisfies the ink, and only
    this counter and `arc_cand` say that the second one is missing."""
    single = np.column_stack([np.full(60, 0.5), np.linspace(0.0, 1.2, 60)])
    lost = count_retraces([_out_and_back()], [single])
    assert (lost.ref, lost.cand, lost.matched, lost.missing) == (1, 0, 0, 1)
    assert lost.arc_cand == 0.0
    assert lost.arc_ref > 1.5


def test_a_zone_thinner_than_the_minimum_is_dropped_as_a_graze() -> None:
    """`RETRACE_MIN_PAIRS` is a SAMPLE count, so it bites at the discretisation.

    The identical geometry is a retrace at the bench step and a graze once the
    path is sampled so coarsely that fewer than three samples fall inside the
    qualifying window — which is exactly why both sides are resampled to one
    common step before either is detected on.
    """
    short = [_out_and_back(top=0.6, k=40)]
    assert RETRACE_MIN_PAIRS == 3
    assert len(retrace_segments(short, resample_step=RESAMPLE_STEP_UNITS)[0]) == 1
    coarse_midpoints, coarse_arc = retrace_segments(short, resample_step=0.2)
    assert len(coarse_midpoints) == 0 and coarse_arc == 0.0


def test_a_stroke_that_never_doubles_back_has_no_retrace() -> None:
    plain = [np.column_stack([np.linspace(0.0, 2.0, 100), np.linspace(0.0, 1.0, 100)])]
    midpoints, arc = retrace_segments(plain)
    assert len(midpoints) == 0 and arc == 0.0


# ----------------------------------------------------------- the pinned stack


def _pinned_pair() -> tuple[list[np.ndarray], list[np.ndarray]]:
    """One fixed synthetic word and one fixed imperfect tracing of it.

    Reference: a looped body (one crossing) that runs into a retraced stem, plus
    a separate i-dot. Candidate: the same shape, shifted by 0.03 xh, with a
    slightly wider retrace gap and a dot placed 0.04 xh away — a plausible
    "close but not exact" follower rather than a caricature.
    """
    loop = _lemniscate()
    link = np.column_stack([np.linspace(1.1, 1.4, 20), np.linspace(0.6, 0.0, 20)])
    reference = [np.vstack([loop, link, _out_and_back(x=1.4, gap=0.02)]), np.array([[1.4, 1.45], [1.44, 1.5]])]
    candidate = [
        np.vstack([loop, link, _out_and_back(x=1.4, gap=0.05)]) + np.array([0.03, 0.0]),
        np.array([[1.44, 1.47], [1.48, 1.52]]),
    ]
    return reference, candidate


def test_the_whole_stack_is_pinned_on_one_synthetic_pair() -> None:
    """A tripwire across frame, classification, distances and counters.

    Every literal below was computed once, from this file's own inputs. A change
    that moves one of them is a re-baseline of the ruler and must be declared as
    one (`docs/proposals/tintenfolger.md` §2.4) — it is never a test to update
    in passing.
    """
    reference, candidate = _pinned_pair()
    ref_body, ref_marks = classify_strokes(reference)
    cand_body, cand_marks = classify_strokes(candidate)
    assert len(ref_body) == len(cand_body) == 1
    assert len(ref_marks) == len(cand_marks) == 1

    warp = dtw(concat_body(ref_body), concat_body(cand_body))
    assert warp.mean_xh == pytest.approx(0.0323851639822536, abs=1e-9)
    assert warp.path_len == 306
    assert warp.max_absorption == 2

    precision, recall = chamfer(concat_body(cand_body), concat_body(ref_body))
    assert precision == pytest.approx(0.027951645059684806, abs=1e-9)
    assert recall == pytest.approx(0.02204737684488429, abs=1e-9)

    crossings = count_crossings(reference, candidate)
    assert (crossings.ref, crossings.cand, crossings.matched, crossings.missing) == (1, 1, 1, 0)
    assert crossings.pos_err_xh == pytest.approx(0.029999569133293876, abs=1e-9)

    # ONE retrace zone since the v2 re-baseline (§14 `aug16`): the stem's
    # out-and-back. The figure eight's waist — the two lobes running
    # anti-parallel PAST each other — is exactly the owner's touch class now,
    # counted beside the retrace instead of as one.
    retraces = count_retraces(reference, candidate)
    assert (retraces.ref, retraces.cand, retraces.matched, retraces.spurious) == (1, 1, 1, 0)
    assert retraces.arc_ref == pytest.approx(2.059301790048808, abs=1e-9)
    assert retraces.arc_cand == pytest.approx(2.102443523166898, abs=1e-9)
    for side in (reference, candidate):
        zones = structure_zones(side)
        assert (len(zones.touch_mids), len(zones.overlap_mids)) == (1, 0)

    marks = match_marks(ref_marks, cand_marks)
    assert (marks.matched, marks.missing, marks.spurious) == (1, 0, 0)
    assert marks.pos_err_xh == pytest.approx(0.044721359549995836, abs=1e-9)

    lifts = lift_stats(ref_body, cand_body)
    assert lifts["lift_ref"] == 0 and lifts["lift_delta"] == 0

    # The AIoU side, the way the bench will use it: a dilated ink blob standing
    # in for `ref_mask.png`, the candidate rasterised into the same crop grid.
    frame = BenchFrame.from_entry({"id": "pin", "rect": [0, 0, 120, 90], "baseline_y": 70.0, "midband_y": 40.0})
    ink = binary_dilation(
        rasterise_strokes([frame.bench_to_crop_px(s) for s in reference], (90, 120)),
        structure=np.ones((3, 3), dtype=bool),
    )
    coverage = aiou([frame.bench_to_crop_px(s) for s in candidate], ink)
    assert coverage.value == pytest.approx(0.6858345021037868, abs=1e-9)
    assert coverage.k == 1
    assert coverage.iou_k0 == pytest.approx(0.3739565943238731, abs=1e-9)


def test_a_wobbly_out_and_back_is_a_retrace_not_a_crossing() -> None:
    # Owner question (2026-08-14): a hand-traced stroke that goes out and
    # comes back over itself can genuinely self-intersect under a shallow
    # angle — those wiggle crossings must land in the RETRACE channel, never
    # in the crossing counter (since v2 the pierce margin + arc-separation
    # guards are what sieve them out).
    k = 120
    up = np.column_stack([np.full(k, 0.5) + 0.008 * np.sin(np.linspace(0, 9, k)), np.linspace(0.0, 1.4, k)])
    back = np.column_stack([np.full(k, 0.5) + 0.015 * np.sin(np.linspace(1.3, 11, k)), np.linspace(1.4, 0.0, k)])
    stroke = np.vstack([up, back])
    assert len(crossing_points([stroke])) == 0
    mids, arc = retrace_segments([stroke])
    assert len(mids) == 1 and arc > 1.5


# ---- the §14 v2 owner verdicts, pinned (qualitaetsmetrik.md `aug16`) --------


def test_a_tangential_dip_is_not_a_crossing() -> None:
    """The unter-e verdict: a retrace that dips across and releases on the
    SAME side has a raw self-intersection but no pierce — no ring."""
    forth = [[0.0, 0.0], [2.0, 0.0]]
    back = [[2.0, 0.06], [1.05, 0.06], [1.0, -0.02], [0.95, 0.06], [0.0, 0.06]]
    stroke = np.asarray(forth + back, dtype=float)
    raw = polyline_self_intersections(*concat_strokes(resampled_strokes([stroke])))
    assert raw, "the premise: the dip really does intersect"
    assert len(crossing_points([stroke])) == 0


def test_a_shallow_antiparallel_crossing_is_retrace_internal() -> None:
    """v2.1: a 13-degree crossing between near-anti-parallel passes is the
    retrace detector's OWN pair (its anti-parallel tolerance is 25 degrees),
    so its incidental ring is retrace-internal — the owner's release rule
    outranks „a pierce counts however shallow". Every genuinely kept hand
    ring measures 45 degrees or more; the zwei-w release at 24 degrees is
    exactly what this suppresses."""
    stroke = np.asarray([[-1.0, 0.0], [2.0, 0.0], [3.0, 0.6], [-2.0, -0.55]], dtype=float)
    raw = polyline_self_intersections(*concat_strokes(resampled_strokes([stroke])))
    assert any(x.arc_separation >= 0.35 for x in raw), "the premise: the shallow pass really crosses"
    assert len(crossing_points([stroke])) == 0


def test_writing_past_each_other_is_a_touch_not_a_retrace() -> None:
    """The mit Kringel-gegen-Anstrich verdict: anti-parallel proximity with a
    long way in between is a TOUCH."""
    stroke = np.asarray(
        [[0.0, 0.5], [2.0, 0.5], [2.0, 2.0], [3.5, 2.0], [3.5, 0.55], [2.0, 0.55], [0.0, 0.55]], dtype=float
    )
    zones = structure_zones([stroke])
    assert len(zones.touch_mids) == 1
    assert len(zones.retrace_mids) == 0


def test_a_release_crossing_its_own_partner_limb_is_no_ring() -> None:
    """v2.1 (the unter-t / mit-t / zwei-w verdict): an out-and-back whose
    release limb incidentally crosses its OWN partner limb draws a real
    intersection, but it is retrace-internal — the pen branched off, it did
    not cross foreign ink. The linken Kringel passages, where a retrace
    crosses ink that is NOT its partner, keep their rings (pinned by the
    healthy-crossing tests above)."""
    up_down_release = np.asarray([[0.0, 0.0], [0.0, 1.5], [0.06, 1.5], [0.06, 0.6], [-0.4, 0.4]], dtype=float)
    raw = polyline_self_intersections(*concat_strokes(resampled_strokes([up_down_release])))
    assert any(x.arc_separation >= 0.35 for x in raw), "the premise: the release really crosses"
    assert len(crossing_points([up_down_release])) == 0


def test_a_diverging_cusp_is_no_zone_at_all() -> None:
    """The laden l-a verdict: a sharp cusp whose limbs immediately diverge
    grazes the proximity rule for a moment and is nothing."""
    stroke = np.asarray([[0.0, 0.0], [0.0, 2.0], [0.06, 2.0], [1.2, 0.0]], dtype=float)
    zones = structure_zones([stroke])
    assert len(zones.retrace_mids) == 0
    assert len(zones.touch_mids) == 0
    assert len(zones.overlap_mids) == 0
