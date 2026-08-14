"""Tests for the scoring row, the block and the paired comparison (`summary`).

The scorer is graded the way a ruler has to be: on hand-built pairs whose answer
is known before the code runs. A pure translation perpendicular to the stroke
must come out as exactly that distance; a dropped i-dot must show up as one
missing mark AND in the recall chamfer half alone; a trace against itself must
be all zeros and all matched, which is the identity gate §14 makes a kill
criterion.

No fixtures and no DB — the entries are built in `tmp_path` from arrays.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from core.shaping import is_registry_glyph_key
from tools.tracebench.candidates import candidate_from_wire
from tools.tracebench.frames import BenchFrame
from tools.tracebench.reference import ReferenceEntry, ReferenceRow
from tools.tracebench.summary import (
    MARKS_PER_KEY,
    compare,
    direction_audit,
    expected_marks,
    identity_gate,
    print_block,
    print_rows,
    score_word,
    summarize,
)


XH_PX = 20.0
BASELINE_ROW = 30.0
# With `xh_px == frame.xh` and a zero origin, trace units and bench units
# coincide — so a test can state its geometry in the unit it reasons in.
REGISTRATION = {"tx": 0.0, "ty": 0.0, "baseline_row": BASELINE_ROW}

BODY = [[0.2, 0.5], [0.6, 0.5], [1.0, 0.5], [1.4, 0.5]]  # a horizontal stroke
MARK = [[0.7, 1.4], [0.75, 1.42]]  # short, floating above the midband: an i-dot


def _entry(tmp_path: Path, strokes: list, *, slots: list[str] | None = None) -> ReferenceEntry:
    """A hand-built reference entry: one frame, one stored row, one ink mask."""
    directory = tmp_path / "die"
    directory.mkdir(parents=True, exist_ok=True)
    mask = np.zeros((60, 60), dtype=bool)
    mask[18:22, 4:30] = True
    Image.fromarray((mask * 255).astype(np.uint8), mode="L").save(directory / "ref_mask.png")
    entry = {"id": "die", "word": "die", "kind": "word", "slots": [{"key": k} for k in (slots or ["d", "i", "e"])]}
    return ReferenceEntry(
        specimen_id="die",
        entry=entry,
        frame=BenchFrame(xh=XH_PX, baseline_row=BASELINE_ROW, entry_id="die"),
        row=ReferenceRow(
            specimen_id="die",
            kind="word",
            word="die",
            slots=slots or ["d", "i", "e"],
            provenance="authored",
            strokes=strokes,
            registration_px=dict(REGISTRATION),
            xh_px=XH_PX,
        ),
        directory=directory,
    )


def _candidate(strokes: list):
    return candidate_from_wire(strokes, dict(REGISTRATION), XH_PX)


def _shift(stroke: list, dx: float, dy: float) -> list:
    return [[x + dx, y + dy] for x, y in stroke]


# ------------------------------------------------------------- known numbers


def test_a_perpendicular_translation_is_reported_as_exactly_that_distance(tmp_path: Path) -> None:
    """The calibration case: two parallel strokes `d` apart.

    Every point of one is at least `d` from every point of the other, and the
    index-aligned path realises exactly `d` — so the DTW mean IS the shift, and
    a normalisation error (by the sequence length rather than the warping path)
    would show up immediately.
    """
    shift = 0.25
    row = score_word(_entry(tmp_path, [BODY]), _candidate([_shift(BODY, 0.0, shift)]))
    assert row["status"] == "ok"
    assert row["dtw_xh"] == pytest.approx(shift, abs=1e-9)
    assert row["chamfer_cand_ref_xh"] == pytest.approx(shift, abs=1e-9)
    assert row["chamfer_ref_cand_xh"] == pytest.approx(shift, abs=1e-9)


def test_a_trace_against_itself_is_zero_and_fully_matched(tmp_path: Path) -> None:
    """The identity gate — §14's third kill criterion, on the smallest case."""
    entry = _entry(tmp_path, [BODY, MARK])
    row = score_word(entry, _candidate([BODY, MARK]))
    assert row["dtw_xh"] == 0.0
    assert row["chamfer_cand_ref_xh"] == 0.0 and row["chamfer_ref_cand_xh"] == 0.0
    assert (row["marks_ref"], row["marks_matched"], row["marks_missing"], row["marks_spurious"]) == (1, 1, 0, 0)
    assert row["lift_delta"] == 0
    assert not row["dtw_reversed_better"]
    assert identity_gate([row]) == []


def test_a_lost_mark_is_counted_and_inflates_the_recall_chamfer_only(tmp_path: Path) -> None:
    """A dropped i-dot is a STRUCTURE defect, and it must be visible as one.

    `marks_missing` counts it (the co-primary gate), and of the two chamfer
    halves only the recall one moves — the candidate still lies exactly on the
    human path, it just does not cover all of it. A symmetric mean would have
    halved precisely this signal.
    """
    entry = _entry(tmp_path, [BODY, MARK])
    row = score_word(entry, _candidate([BODY]))
    assert row["marks_ref"] == 1 and row["marks_cand"] == 0
    assert row["marks_missing"] == 1 and row["marks_spurious"] == 0
    assert row["chamfer_cand_ref_xh"] == pytest.approx(0.0, abs=1e-9)
    assert row["chamfer_ref_cand_xh"] > 0.0
    assert identity_gate([row])  # …and it can never pass as an identity


def test_a_spurious_mark_is_counted_on_its_own_side(tmp_path: Path) -> None:
    entry = _entry(tmp_path, [BODY])
    row = score_word(entry, _candidate([BODY, MARK]))
    assert row["marks_ref"] == 0 and row["marks_cand"] == 1
    assert row["marks_spurious"] == 1 and row["marks_missing"] == 0


def test_a_candidate_written_backwards_is_flagged_but_not_re_aligned(tmp_path: Path) -> None:
    """Direction is ductus truth: the DTW stays forward-only and pays for it,
    and the report-only columns say that the reverse reads better."""
    entry = _entry(tmp_path, [BODY])
    row = score_word(entry, _candidate([BODY[::-1]]))
    assert row["dtw_reversed_better"] is True
    assert row["dtw_xh"] > 0.0
    assert row["direction_uncertain"] == 1 and row["direction_checked"] == 1


def test_the_direction_audit_pairs_strokes_in_writing_order() -> None:
    forward = [np.array([[0.0, 0.0], [1.0, 0.0]]), np.array([[0.0, 1.0], [1.0, 1.0]])]
    mixed = [forward[0], forward[1][::-1]]
    assert direction_audit(forward, forward) == (0, 2)
    assert direction_audit(forward, mixed) == (1, 2)


def test_a_candidate_that_never_arrived_is_still_a_row(tmp_path: Path) -> None:
    entry = _entry(tmp_path, [BODY])
    row = score_word(entry, candidate_from_wire([], REGISTRATION, XH_PX), label="chain")
    assert row["status"] == "failed" and row["dtw_xh"] is None
    assert row["ref_strokes"] == 1 and row["candidate"] == "chain"


# ------------------------------------------------------------- the mark set


def test_every_mark_bearing_key_is_a_real_registry_key() -> None:
    """The set is glyph KEYS (ä → "ae"), so a typo must fail here, not silently
    report "this word expects no marks"."""
    assert all(is_registry_glyph_key(key) for key in MARKS_PER_KEY)
    assert {"i", "u", "ae", "oe", "ue"} <= set(MARKS_PER_KEY)


def test_expected_marks_counts_the_words_own_slots() -> None:
    assert expected_marks(["d", "i", "e"]) == 1
    assert expected_marks(["u", "n", "d"]) == 1
    assert expected_marks(["m", "u", "ss"]) == 1
    assert expected_marks(["l", "a", "d", "e", "n"]) == 0


def test_a_reference_whose_marks_disagree_with_its_slots_is_flagged(tmp_path: Path) -> None:
    """The cross-check is reported, never enforced: `marks_uncertain` tells the
    reader the mark columns rest on a count nobody verified."""
    plain = score_word(_entry(tmp_path, [BODY, MARK], slots=["d", "i", "e"]), _candidate([BODY, MARK]))
    assert plain["marks_expected"] == 1 and not plain["marks_uncertain"]
    odd = score_word(_entry(tmp_path, [BODY], slots=["d", "i", "e"]), _candidate([BODY]))
    assert odd["marks_expected"] == 1 and odd["marks_uncertain"]


# ---------------------------------------------------------------- the block


def test_the_block_carries_the_pre_registered_keys(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    entry = _entry(tmp_path, [BODY, MARK])
    rows = [score_word(entry, _candidate([BODY, MARK]), label="authored", split="dev")]
    summary = summarize(rows, excluded={"frame_stale": 2})
    print_rows(rows)
    print_block(summary, label="authored", split="dev")
    printed = capsys.readouterr().out
    for key in (
        "dtw_xh_median",
        "dtw_xh_p90",
        "aiou_median",
        "chamfer_cand_ref_median",
        "chamfer_ref_cand_median",
        "marks_missing",
        "cross_missing",
        "cross_spurious",
        "retrace_arc_ratio_median",
        "dtw_reversed_better",
        "words_failed",
        "words_skipped",
    ):
        assert f"{key}:" in printed
    assert "frame_stale=2" in printed
    assert summary["scored"] == 1 and summary["excluded"] == {"frame_stale": 2}


def test_the_block_counts_failures_instead_of_averaging_them(tmp_path: Path) -> None:
    entry = _entry(tmp_path, [BODY])
    rows = [score_word(entry, _candidate([BODY])), score_word(entry, candidate_from_wire([], REGISTRATION, XH_PX))]
    summary = summarize(rows)
    assert (summary["rows"], summary["scored"], summary["failed"]) == (2, 1, 1)
    assert summary["dtw_xh_median"] == 0.0  # the failed row is not averaged in


# ----------------------------------------------------------- the comparison


def test_compare_uses_the_chainbenchs_sign_test_and_never_its_own() -> None:
    """One project, one definition of the statistic — imported, not restated."""
    from tools.pairlab import chainbench  # noqa: PLC0415
    from tools.tracebench import summary as summary_mod  # noqa: PLC0415

    assert summary_mod._sign_test() is chainbench.sign_test


def test_compare_pairs_per_word_and_reports_the_gates(tmp_path: Path) -> None:
    entry = _entry(tmp_path, [BODY, MARK])
    baseline = [score_word(entry, _candidate([_shift(BODY, 0.0, 0.4), MARK]), label="chain")]
    better = [score_word(entry, _candidate([_shift(BODY, 0.0, 0.1), MARK]), label="follow")]
    result = compare(baseline, better)
    assert result["paired"] == 1
    assert result["dtw_delta_median"] == pytest.approx(-0.3, abs=1e-9)
    assert result["dtw_rel_median"] == pytest.approx(-0.75, abs=1e-9)
    assert result["sign_test"]["neg"] == 1
    assert result["marks_missing_ab"] == (0, 0)  # the co-primary gate held
    assert result["per_word"][0]["id"] == "die"


def test_compare_names_the_words_only_one_side_scored(tmp_path: Path) -> None:
    """A word one run could not score is NAMED, never compared against a hole."""
    entry = _entry(tmp_path, [BODY])
    scored = [score_word(entry, _candidate([BODY]))]
    lost = [score_word(entry, candidate_from_wire([], REGISTRATION, XH_PX))]
    result = compare(scored, lost)
    assert result["paired"] == 0
    assert result["unpaired"] == ["die"]
    assert result["failed_ab"] == (0, 1)
