"""Tests for the mark refit (`tools.pairlab.marks`, tintenfolger.md §7.3 A1).

The measure is one sentence — *after the body solve, move each mark onto the ink
the body did not claim, by a translation, and only when exactly one target is
nameable* — so the tests are the five ways that sentence can be broken:

* it is **off by default**, and with it off the harvest's chain path does not
  even reach this code (the trace bench's `chain` baseline IS what the harvest
  stores, so a silent change there would make every measured delta unreadable);
* a **displaced dot is found** and the mark travels to it rigidly;
* **two possible targets are refused**, and **two marks wanting one target** are
  both refused, rather than assigned by a coin flip;
* a target **beyond the search radius** is not reached for; and
* **no body stroke ever moves**, nor does a mark land on ink the body already
  accounts for or on a cluster too big to be a mark.

Everything is built by hand: a frame, a few polylines and a boolean ink array.
No fixtures, no solver, no DB.
"""

from __future__ import annotations

import numpy as np
import pytest

from tools.pairlab.marks import (
    MARK_MAX_INK_ARC_UNITS,
    MARK_SEARCH_RADIUS_UNITS,
    MarkRefitOptions,
    ink_clusters,
    mark_refit_summary,
    refit_word_marks,
    unclaimed_ink_mask,
)


XH = 40.0
BASELINE_ROW = 110.0
X_ORIGIN = 30.0
REGISTRATION = {"tx": X_ORIGIN, "ty": 0.0, "baseline_row": BASELINE_ROW}
SHAPE = (160, 220)  # (rows, cols) of the synthetic crop


def _px(points_units) -> np.ndarray:
    a = np.asarray(points_units, dtype=float).reshape(-1, 2)
    return np.column_stack([X_ORIGIN + a[:, 0] * XH, BASELINE_ROW - a[:, 1] * XH])


def _entry(points_units, *, segment: int, stroke_index: int, kind: str = "letter", slot: int | None = 0) -> dict:
    return {
        "kind": kind,
        "segment_index": segment,
        "slot_index": slot,
        "key": "i",
        "stroke_index": stroke_index,
        "points_px": _px(points_units),
    }


# A body stroke down in the Mittellänge (never a diacritic: stroke_index 0), and
# the mark the composition parked at (0.60, 1.40).
BODY = _entry([(0.20, 0.05), (0.60, 0.60), (1.00, 0.05)], segment=0, stroke_index=0)
MARK_AT = (0.60, 1.40)


def _mark(centre_units=MARK_AT, *, segment: int = 0, stroke_index: int = 1) -> dict:
    cx, cy = centre_units
    return _entry([(cx - 0.03, cy - 0.02), (cx + 0.03, cy + 0.02)], segment=segment, stroke_index=stroke_index, slot=0)


def _ink(*dots_units, half: int = 1) -> np.ndarray:
    """A blank crop with a small square blob of skeleton pixels per position."""
    ink = np.zeros(SHAPE, dtype=bool)
    for centre in dots_units:
        x, y = _px([centre])[0]
        ix, iy = int(round(x)), int(round(y))
        ink[iy - half : iy + half + 1, ix - half : ix + half + 1] = True
    return ink


def _centroid_px(entry: dict) -> np.ndarray:
    return np.asarray(entry["points_px"], dtype=float).reshape(-1, 2).mean(axis=0)


# --------------------------------------------------------------- the happy path


def test_a_displaced_dot_is_found_and_the_mark_travels_to_it() -> None:
    """The composed dot sits 0.3 xh left of the ink; the refit closes exactly that."""
    truth = (0.90, 1.40)
    entries, reports = refit_word_marks([[BODY, _mark()]], xh=XH, registration=REGISTRATION, skeleton=_ink(truth))

    assert [r.reason for r in reports] == ["ok"]
    assert reports[0].moved
    assert reports[0].shift_units == pytest.approx(0.30, abs=1e-3)
    assert reports[0].from_units == pytest.approx(MARK_AT, abs=1e-3)
    assert reports[0].to_units == pytest.approx(truth, abs=0.02)
    assert reports[0].target_ink_px == 9  # the 3x3 blob
    assert _centroid_px(entries[0][1]) == pytest.approx(_px([truth])[0], abs=0.6)


def test_the_move_is_a_rigid_translation() -> None:
    """Every point of the mark travels by the SAME vector — no scale, no rotation."""
    before = _mark()
    entries, _ = refit_word_marks([[BODY, before]], xh=XH, registration=REGISTRATION, skeleton=_ink((0.90, 1.45)))
    delta = np.asarray(entries[0][1]["points_px"]) - np.asarray(before["points_px"])
    assert delta == pytest.approx(np.repeat(delta[:1], len(delta), axis=0), abs=1e-9)


def test_the_summary_rolls_the_rows_up() -> None:
    _, reports = refit_word_marks([[BODY, _mark()]], xh=XH, registration=REGISTRATION, skeleton=_ink((0.90, 1.40)))
    summary = mark_refit_summary(reports)
    assert summary["marks"] == 1
    assert summary["moved"] == 1
    assert summary["refused"] == 0
    assert summary["reasons"] == {"ok": 1}
    assert summary["median_shift_units"] == pytest.approx(0.30, abs=1e-3)


# ------------------------------------------------------------- the refusals


def test_two_possible_targets_are_refused_rather_than_guessed() -> None:
    """Equidistant blobs left and right: proximity cannot decide, so nothing moves."""
    before = _mark()
    entries, reports = refit_word_marks(
        [[BODY, before]], xh=XH, registration=REGISTRATION, skeleton=_ink((0.30, 1.40), (0.90, 1.40))
    )
    assert [r.reason for r in reports] == ["ambiguous"]
    assert not reports[0].moved
    assert reports[0].shift_units == 0.0
    assert entries[0][1] is before  # untouched, not merely equal


def test_two_marks_wanting_the_same_ink_both_stay_put() -> None:
    """One blob, two marks — an assignment would have to invent one of them."""
    left, right = _mark((0.75, 1.40), segment=0), _mark((1.05, 1.40), segment=2, stroke_index=1)
    entries, reports = refit_word_marks(
        [[BODY, left, right]], xh=XH, registration=REGISTRATION, skeleton=_ink((0.90, 1.40))
    )
    assert [r.reason for r in reports] == ["contested", "contested"]
    assert entries[0][1] is left and entries[0][2] is right


def test_ink_beyond_the_search_radius_is_not_reached_for() -> None:
    before = _mark()
    beyond = (MARK_AT[0] + MARK_SEARCH_RADIUS_UNITS + 0.05, MARK_AT[1])
    entries, reports = refit_word_marks([[BODY, before]], xh=XH, registration=REGISTRATION, skeleton=_ink(beyond))
    assert [r.reason for r in reports] == ["no_candidate"]
    assert entries[0][1] is before

    inside = (MARK_AT[0] + MARK_SEARCH_RADIUS_UNITS - 0.05, MARK_AT[1])
    _, reached = refit_word_marks([[BODY, _mark()]], xh=XH, registration=REGISTRATION, skeleton=_ink(inside))
    assert [r.reason for r in reached] == ["ok"]


def test_a_cluster_too_big_to_be_a_mark_is_not_a_target() -> None:
    """A stroke the fit missed is unclaimed ink, but it is not an i-dot."""
    long_stroke = np.zeros(SHAPE, dtype=bool)
    x, y = _px([(0.90, 1.40)])[0]
    span = int(MARK_MAX_INK_ARC_UNITS * XH) + 10
    long_stroke[int(y), int(x) - span // 2 : int(x) + span // 2] = True
    before = _mark()
    entries, reports = refit_word_marks([[BODY, before]], xh=XH, registration=REGISTRATION, skeleton=long_stroke)
    assert [r.reason for r in reports] == ["no_candidate"]
    assert entries[0][1] is before


def test_ink_the_body_already_accounts_for_is_not_a_target() -> None:
    """An ascender running past the mark owns its own ink — the mark may not take it."""
    ascender = _entry([(0.90, 0.10), (0.90, 1.80)], segment=2, stroke_index=0, slot=1)
    on_the_ascender = (0.90, 1.40)
    before = _mark()
    entries, reports = refit_word_marks(
        [[BODY, ascender, before]], xh=XH, registration=REGISTRATION, skeleton=_ink(on_the_ascender)
    )
    assert [r.reason for r in reports] == ["no_candidate"]
    assert entries[0][2] is before


def test_without_ink_every_mark_says_so() -> None:
    before = _mark()
    entries, reports = refit_word_marks([[BODY, before]], xh=XH, registration=REGISTRATION, skeleton=None)
    assert [r.reason for r in reports] == ["no_ink"]
    assert entries[0][1] is before


def test_a_word_without_marks_reports_nothing_and_changes_nothing() -> None:
    entries, reports = refit_word_marks([[BODY]], xh=XH, registration=REGISTRATION, skeleton=_ink((0.90, 1.40)))
    assert reports == []
    assert entries[0][0] is BODY


# ------------------------------------------------------- the body is untouchable


def test_no_body_stroke_is_ever_moved() -> None:
    """Only entries the assembler emits as their own diacritic stroke are touched."""
    connector = _entry([(1.00, 0.05), (1.40, 0.20)], segment=1, stroke_index=0, kind="connector", slot=None)
    second = _entry([(1.40, 0.20), (1.90, 0.05)], segment=2, stroke_index=0, slot=1)
    body_before = [np.asarray(e["points_px"]).copy() for e in (BODY, connector, second)]

    entries, reports = refit_word_marks(
        [[BODY, connector, second, _mark()]], xh=XH, registration=REGISTRATION, skeleton=_ink((0.90, 1.40))
    )
    assert [r.reason for r in reports] == ["ok"]  # the mark DID move — the body still did not
    for original, kept, after in zip(body_before, (BODY, connector, second), entries[0][:3], strict=True):
        assert after is kept
        assert np.asarray(after["points_px"]) == pytest.approx(original)


def test_a_moved_mark_is_a_copy_so_the_solve_keeps_its_own_output() -> None:
    """The refit changes what the trace SHOWS, not what the harvest MEASURES.

    The gates, the connector QC and the occurrence rows all read
    `fit.stroke_polylines_px` after the assembly, so a refit that MUTATED the
    fit's entries would silently move a measurement too.
    """
    before = _mark()
    original = np.asarray(before["points_px"]).copy()
    entries, _ = refit_word_marks([[BODY, before]], xh=XH, registration=REGISTRATION, skeleton=_ink((0.90, 1.40)))

    assert entries[0][1] is not before
    assert np.asarray(before["points_px"]) == pytest.approx(original)


def test_the_body_claim_and_the_clusters_are_readable_on_their_own() -> None:
    """The two helper steps, checked without the assignment on top of them."""
    ink = _ink((0.60, 0.60), (0.90, 1.40))  # one blob ON the body arc, one free
    free = unclaimed_ink_mask(ink, [np.asarray(BODY["points_px"])], claim_px=0.15 * XH)
    assert free.sum() == 9  # the body's own blob is claimed, the mark's is not
    centroids, masses = ink_clusters(free)
    assert len(centroids) == 1
    assert masses.tolist() == [9]
    assert centroids[0] == pytest.approx(_px([(0.90, 1.40)])[0], abs=0.6)


def test_the_options_are_the_module_constants() -> None:
    """The dataclass defaults ARE the KS_MARK_* constants, so a sweep reaches them."""
    assert MarkRefitOptions().search_radius_units == MARK_SEARCH_RADIUS_UNITS
    assert MarkRefitOptions().max_ink_arc_units == MARK_MAX_INK_ARC_UNITS
