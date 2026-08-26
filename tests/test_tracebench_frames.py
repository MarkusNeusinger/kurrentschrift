"""Tests for the bench frame and the stroke bookkeeping (`tools.tracebench.frames`).

The first test is the one the whole bench rests on: stored `(u, v)` coordinates
are not canonical, so two rows may describe the SAME crop pixels in different
labels — and must then land on the same bench points. Everything after it guards
a classification the reader would otherwise have to trust: what is a mark, what
is body, and where a pen lift sits.
"""

from __future__ import annotations

import numpy as np
import pytest

from tools.tracebench.frames import (
    LIFT_MATCH_RADIUS_UNITS,
    MARK_MAX_ARC_UNITS,
    BenchFrame,
    arc_length,
    classify_strokes,
    concat_body,
    concat_strokes,
    lift_positions,
    lift_stats,
    mark_centroids,
    match_marks,
    match_points,
)


# One frozen `word.json` entry: crop rows 200..300 of the page, Grundlinie at
# page row 270 (crop row 70), Mittellinie 30 px above it.
ENTRY = {"id": "die", "rect": [100, 200, 260, 300], "baseline_y": 270.0, "midband_y": 240.0}


def _crop_to_trace(px: np.ndarray, registration: dict, xh_px: float) -> np.ndarray:
    """The inverse of the app's `traceToCrop` — how a row LABELS given crop pixels."""
    pts = np.asarray(px, dtype=float).reshape(-1, 2)
    baseline = registration["baseline_row"] + registration.get("ty", 0.0)
    return np.column_stack([(pts[:, 0] - registration.get("tx", 0.0)) / xh_px, (baseline - pts[:, 1]) / xh_px])


# ------------------------------------------------------------------- the frame


def test_the_frame_comes_from_the_frozen_entry_alone() -> None:
    frame = BenchFrame.from_entry(ENTRY)
    assert frame.xh == 30.0  # baseline_y - midband_y
    assert frame.baseline_row == 70.0  # baseline_y - rect[1]
    assert frame.entry_id == "die"


def test_bench_and_crop_pixels_are_exact_inverses() -> None:
    frame = BenchFrame.from_entry(ENTRY)
    bench = np.array([[0.0, 0.0], [1.5, 1.0], [3.25, -0.4]])
    assert frame.crop_px_to_bench(frame.bench_to_crop_px(bench)) == pytest.approx(bench, abs=1e-12)


def test_two_registrations_of_the_same_pixels_map_to_the_same_bench_points() -> None:
    """THE property of §2.1 — the reason the bench does not compare stored labels.

    Both rows describe the identical crop pixels. One is an authored row (its
    `ty` folded into `baseline_row`, x-height 30 px, origin shifted); the other
    is a harvest row with a separate `ty`, half the x-height and a different
    origin. Their stored numbers share not one digit — and the bench sees one
    and the same path.
    """
    frame = BenchFrame.from_entry(ENTRY)
    crop_px = np.array([[10.0, 70.0], [25.5, 41.0], [44.0, 88.25], [61.0, 55.5]])

    authored = {"tx": 3.0, "ty": 0.0, "baseline_row": 70.0}
    harvested = {"tx": -4.0, "ty": 2.0, "baseline_row": 68.0}
    first = frame.trace_to_bench([_crop_to_trace(crop_px, authored, 30.0)], authored, 30.0)
    second = frame.trace_to_bench([_crop_to_trace(crop_px, harvested, 15.0)], harvested, 15.0)

    assert first[0] == pytest.approx(second[0], abs=1e-12)
    assert first[0] == pytest.approx(frame.crop_px_to_bench(crop_px), abs=1e-12)


def test_a_trace_without_a_stored_registration_falls_back_to_the_entry() -> None:
    """A hand-written row with no measurements keeps its baseline instead of collapsing to 0."""
    frame = BenchFrame.from_entry(ENTRY)
    out = frame.trace_to_bench([[[0.0, 0.0], [2.0, 1.0]]], None, None)
    assert out[0] == pytest.approx(np.array([[0.0, 0.0], [2.0, 1.0]]), abs=1e-12)


def test_a_broken_frame_is_refused_rather_than_measured() -> None:
    with pytest.raises(ValueError, match="x-height"):
        BenchFrame.from_entry({**ENTRY, "midband_y": 270.0})
    with pytest.raises(ValueError, match="xh_px"):
        BenchFrame.from_entry(ENTRY).trace_to_bench([[[0.0, 0.0]]], {"baseline_row": 70.0}, -3.0)


# --------------------------------------------------------- marks versus body


def test_a_dot_above_the_midband_is_a_mark_and_the_first_stroke_never_is() -> None:
    body_stroke = np.array([[0.0, 0.0], [0.3, 0.9], [0.5, 0.0]])
    dot = np.array([[0.4, 1.45], [0.44, 1.5]])
    body, marks = classify_strokes([body_stroke, dot])
    assert len(body) == 1 and len(marks) == 1
    assert marks[0] == pytest.approx(dot)

    # …and the same dot leading the list is body: a word does not open with its
    # own diacritic, so a first stroke up there is a misordered trace, not a mark.
    body, marks = classify_strokes([dot, body_stroke])
    assert marks == [] and len(body) == 2


def test_a_crossbar_that_dips_through_the_midband_is_body() -> None:
    """The t-bar: short enough for a mark, but it does not float above the midband."""
    bar = np.array([[0.2, 1.05], [0.5, 0.98], [0.8, 0.95]])
    assert arc_length(bar) < MARK_MAX_ARC_UNITS
    body, marks = classify_strokes([np.array([[0.5, 0.0], [0.5, 1.6]]), bar])
    assert marks == [] and len(body) == 2


def test_a_long_floating_stroke_is_body_however_high_it_sits() -> None:
    """A capital's ornament lives in the Oberlänge and is still a written form.

    Lengthened when the cap moved 0.8 -> 1.5 (§14 „Lineal L-U"): the old
    synthetic ornament measured 1.35 xh and would now pass as a mark. It has to
    be what the cap is actually for — a stroke too long to be an accent over
    one letter — so it spans two letter widths.
    """
    ornament = np.column_stack([np.linspace(0.0, 2.0, 60), 1.4 + 0.3 * np.sin(np.linspace(0.0, 3.0, 60))])
    assert arc_length(ornament) > MARK_MAX_ARC_UNITS
    body, marks = classify_strokes([np.array([[0.0, 0.0], [0.0, 1.0]]), ornament])
    assert marks == [] and len(body) == 2


def test_a_u_bow_sized_floating_stroke_is_a_mark() -> None:
    """The other side of the same boundary — the reason the cap moved.

    A u-Bogen of the reference hand measures 1.04-1.31 xh and floats entirely
    above the midband. Under the old 0.8 cap it was body, which forced the
    monotone body DTW to pair it against the following letters; the ruler's own
    `MARKS_PER_KEY` has always called it a mark.
    """
    bow = np.column_stack([np.linspace(0.0, 1.1, 40), 1.5 + 0.12 * np.sin(np.linspace(0.0, 3.14, 40))])
    assert 1.0 < arc_length(bow) <= MARK_MAX_ARC_UNITS
    body, marks = classify_strokes([np.array([[0.5, 0.0], [0.5, 1.0]]), bow])
    assert len(marks) == 1 and len(body) == 1


def test_the_cap_is_a_parameter_so_a_re_baseline_can_measure_both_values() -> None:
    """A frozen ruler is changed by measuring the change against itself."""
    bow = np.column_stack([np.linspace(0.0, 1.1, 40), 1.5 + 0.12 * np.sin(np.linspace(0.0, 3.14, 40))])
    strokes = [np.array([[0.5, 0.0], [0.5, 1.0]]), bow]
    assert classify_strokes(strokes, 0.8)[1] == []
    assert len(classify_strokes(strokes, 1.5)[1]) == 1


# ------------------------------------------------------- concatenation + lifts


def test_the_body_concatenates_in_writing_order_with_its_stroke_starts() -> None:
    first = np.array([[0.0, 0.0], [1.0, 0.0]])
    second = np.array([[2.0, 0.0], [3.0, 0.0], [4.0, 0.0]])
    points, starts = concat_strokes([first, second])
    assert starts == [0, 2]
    assert points.tolist() == [*first.tolist(), *second.tolist()]
    assert concat_body([second, first]).tolist() == [*second.tolist(), *first.tolist()]  # order is the truth
    empty_points, empty_starts = concat_strokes([])
    assert empty_points.shape == (0, 2) and empty_starts == []


def test_lift_positions_are_where_the_pen_left_the_paper() -> None:
    strokes = [np.array([[0.0, 0.0], [1.0, 0.2]]), np.array([[1.4, 0.2], [2.0, 0.0]])]
    assert lift_positions(strokes).tolist() == [[1.0, 0.2]]
    assert lift_positions(strokes[:1]).shape == (0, 2)


def test_a_fragmented_candidate_reports_its_extra_lifts() -> None:
    """One reference lift, three candidate lifts — one matched, two spurious.

    The matched one carries a position error; the two the reference has no
    counterpart for are counted, not averaged away, because a lift in the middle
    of a letter is a defect the body DTW barely notices.
    """
    reference = [np.array([[0.0, 0.0], [1.0, 0.0]]), np.array([[1.5, 0.0], [3.0, 0.0]])]
    candidate = [
        np.array([[0.0, 0.0], [1.05, 0.03]]),
        np.array([[1.5, 0.0], [2.0, 0.0]]),
        np.array([[2.0, 0.0], [2.5, 0.0]]),
        np.array([[2.5, 0.0], [3.0, 0.0]]),
    ]
    stats = lift_stats(reference, candidate)
    assert stats["lift_ref"] == 1 and stats["lift_cand"] == 3
    assert stats["lift_delta"] == 2
    assert stats["lift_matched"] == 1 and stats["lift_unmatched_cand"] == 2
    assert stats["lift_pos_err_xh"] == pytest.approx(np.hypot(0.05, 0.03))


def test_a_lift_beyond_the_cap_is_refused_rather_than_paired() -> None:
    reference = [np.array([[0.0, 0.0], [1.0, 0.0]]), np.array([[1.2, 0.0], [2.0, 0.0]])]
    far = [np.array([[0.0, 0.0], [1.0 + 2 * LIFT_MATCH_RADIUS_UNITS, 0.0]]), np.array([[2.4, 0.0], [3.0, 0.0]])]
    stats = lift_stats(reference, far)
    assert stats["lift_delta"] == 0  # same COUNT…
    assert stats["lift_matched"] == 0  # …in a different place
    assert stats["lift_pos_err_xh"] is None


# ------------------------------------------------------------- the mark gate


def test_a_written_mark_matches_its_reference_and_a_lost_one_is_missing() -> None:
    reference = [np.array([[0.4, 1.45], [0.44, 1.5]])]
    written = [np.array([[0.45, 1.48], [0.49, 1.53]])]
    hit = match_marks(reference, written)
    assert (hit.ref, hit.cand, hit.matched, hit.missing, hit.spurious) == (1, 1, 1, 0, 0)
    assert hit.pos_err_xh == pytest.approx(0.05, abs=0.02)

    lost = match_marks(reference, [])
    assert (lost.matched, lost.missing, lost.spurious, lost.pos_err_xh) == (0, 1, 0, None)
    extra = match_marks([], written)
    assert (extra.matched, extra.missing, extra.spurious) == (0, 0, 1)


def test_two_equally_close_candidates_are_refused_not_guessed() -> None:
    """`nearest_unique_point`'s refusal, carried through to the mark gate.

    An umlaut written as one blot and a reference of two dots: proximity cannot
    say which dot the blot is, and a coin flip would report a small position
    error for an unresolved structure.
    """
    reference = [np.array([[0.5, 1.5]])]
    twins = [np.array([[0.5, 1.42]]), np.array([[0.5, 1.58]])]
    refused = match_marks(reference, twins)
    assert refused.ambiguous == 1
    assert refused.matched == 0 and refused.missing == 1 and refused.spurious == 2


def test_a_claimed_candidate_leaves_the_pool() -> None:
    """Two reference marks cannot both land on one candidate blot."""
    reference = np.array([[0.0, 1.5], [0.35, 1.5]])
    single = np.array([[0.02, 1.5]])
    result = match_points(reference, single, radius=0.6, margin=0.25)
    assert result.matched == 1 and result.missing == 1 and result.spurious == 0


def test_mark_centroids_ignore_empty_strokes() -> None:
    assert mark_centroids([np.zeros((0, 2)), np.array([[1.0, 2.0], [3.0, 4.0]])]).tolist() == [[2.0, 3.0]]


def test_the_mark_threshold_matches_the_harvests_rule():
    # DIACRITIC_MIN_Y is re-declared in frames.py (the harvest import would
    # transitively pull matplotlib into the ruler); this pin is what makes the
    # re-declaration safe — a drift on either side fails here.
    from tools.laufform.harvest import DIACRITIC_MIN_Y as harvest_value
    from tools.tracebench.frames import DIACRITIC_MIN_Y

    assert DIACRITIC_MIN_Y == harvest_value
