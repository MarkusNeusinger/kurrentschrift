"""Tests for the standing k0-protocol evaluation (`tools.tracebench.k0eval`).

The scorer feeds the §14 identity and loser gates, so its two halves are
pinned separately: `eval_candidate`'s per-word status handling over a real
(tiny) fixture tree with a candidate file, and `pair_rows` — the paired
classification (soll-distance movement, stroke identity on the parsed
strokes, the standing −0.003 aiou-loser gate, the unscored breakdown) — as
pure arithmetic over hand-built rows. Everything lives in `tmp_path`: no
fixtures, no DB, no network, so these run in CI where the real fixture roots
are gitignored.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from tests.test_tracebench_reference import STROKES, row, write_root
from tools.tracebench.candidates import CANDIDATE_FRAME
from tools.tracebench.k0eval import (
    AIOU_LOSER_GATE,
    STACK_FLAGS,
    eval_candidate,
    guard_outcome,
    guard_stack,
    pair_rows,
    report_rows,
    scoring_ids,
)
from tools.tracebench.reference import load_reference
from tools.tracebench.soll import SollRow


def soll(sid: str, crossings: int, zones: int) -> tuple[SollRow, SollRow]:
    """The (letters, composition) pair `ductus_soll` returns; k0eval reads [1]."""
    return (
        SollRow(label=f"{sid} letters", strokes=3, crossings=crossings, zones=zones),
        SollRow(label=f"{sid} composition", strokes=None, crossings=crossings, zones=zones),
    )


def write_candidate(path: Path, ids: list[str]) -> Path:
    path.write_text(json.dumps({"frame": CANDIDATE_FRAME, "rows": [row(i) for i in ids]}))
    return path


# --------------------------------------------------------------- eval_candidate


def test_a_scored_word_carries_counts_soll_distance_aiou_and_its_strokes(tmp_path: Path) -> None:
    reference = load_reference(write_root(tmp_path, [row("die")]))
    soll_rows = {"die": soll("die", crossings=2, zones=1)}
    rows = eval_candidate(write_candidate(tmp_path / "cand.json", ["die"]), reference, soll_rows, ["die"])
    scored = rows["die"]
    assert scored["status"] == "ok"
    assert scored["soll_cross"] == 2 and scored["soll_zones"] == 1
    assert scored["soll_dist"] == abs(scored["cross"] - 2) + abs(scored["zones"] - 1)
    assert 0.0 <= scored["aiou"] <= 1.0
    assert scored["strokes"] == STROKES  # the parsed wire data, not a serialization


def test_a_word_the_candidate_file_lacks_keeps_its_provider_status(tmp_path: Path) -> None:
    reference = load_reference(write_root(tmp_path, [row("die"), row("mit")]))
    soll_rows = {sid: soll(sid, crossings=1, zones=0) for sid in ("die", "mit")}
    rows = eval_candidate(write_candidate(tmp_path / "cand.json", ["die"]), reference, soll_rows, ["die", "mit"])
    assert rows["die"]["status"] == "ok"
    assert rows["mit"] == {"status": "skipped"}


# -------------------------------------------------------------------- pair_rows


def ok_row(soll_dist: int, aiou: float, strokes: list) -> dict[str, object]:
    return {"status": "ok", "soll_dist": soll_dist, "aiou": aiou, "strokes": strokes}


def test_the_paired_classification_covers_every_class() -> None:
    moved = [[[0.0, 0.0], [1.0, 1.0]]]
    base = {
        "same-id": ok_row(2, 0.60, STROKES),
        "better": ok_row(3, 0.60, STROKES),
        "worse": ok_row(1, 0.60, STROKES),
        "both-out": {"status": "skipped"},
        "one-out": ok_row(1, 0.60, STROKES),
    }
    cand = {
        "same-id": ok_row(2, 0.60, STROKES),  # untouched: same strokes, same distance
        "better": ok_row(1, 0.61, moved),  # moved and improved
        "worse": ok_row(2, 0.59, moved),  # moved, worse distance, aiou below the gate
        "both-out": {"status": "skipped"},
        "one-out": {"status": "failed"},
    }
    ids = list(base)
    pairing = pair_rows(base, cand, ids)
    assert pairing["better"] == ["better"] and pairing["worse"] == ["worse"]
    assert pairing["same"] == ["same-id"]
    assert pairing["identical"] == ["same-id"] and pairing["moved"] == ["better", "worse"]
    assert pairing["unscored"] == Counter({"skipped": 1})
    assert pairing["mismatched"] == ["one-out"]
    assert [sid for sid, _ in pairing["losers"]] == ["worse"]
    assert pairing["losers"][0][1] < AIOU_LOSER_GATE
    assert sorted(pairing["moved_deltas"]) == pytest.approx([-0.01, 0.01])


def test_identity_is_the_parsed_strokes_not_their_serialization() -> None:
    """`1` vs `1.0` serialize differently but are the same wire geometry."""
    base = {"w": ok_row(1, 0.5, [[[1, 1], [2, 0]]])}
    cand = {"w": ok_row(1, 0.5, [[[1.0, 1.0], [2.0, 0.0]]])}
    assert pair_rows(base, cand, ["w"])["identical"] == ["w"]


# ------------------------------------------------------------------ scoring_ids


def test_an_empty_soll_set_is_a_hard_error_not_a_quiet_zero() -> None:
    """The soll distance is the core metric — without targets the run is
    meaningless and must refuse, not print '0 words' and continue."""
    assert scoring_ids(["die", "mit"], {"mit": soll("mit", 1, 0)}) == ["mit"]
    with pytest.raises(SystemExit, match="no words with a composition soll"):
        scoring_ids(["die", "mit"], {})


# ------------------------------------------------------------------ report_rows


def test_the_report_view_drops_the_strokes_and_nothing_else() -> None:
    rows = {"die": ok_row(1, 0.5, STROKES), "mit": {"status": "skipped"}}
    report = report_rows(rows)
    assert "strokes" not in report["die"]
    assert report["die"]["soll_dist"] == 1 and report["die"]["aiou"] == 0.5
    assert report["mit"] == {"status": "skipped"}
    assert rows["die"]["strokes"] == STROKES  # the working rows keep theirs


# ----------------------------------------------------------- the stack sensor


def _round(number: int, **guard) -> dict:
    return {"round": number, "energy_after": 0.001, **guard}


def test_guard_stack_reads_the_flags_off_the_first_row_with_weights(tmp_path: Path) -> None:
    """A base and an arm are only a pair when they differ in the one knob under test.

    The unguarded follower was paired against a guarded arm twice in two days
    (the L-U "Kette" row, the v5 measurement); the flags now come off the file.
    """
    weights = {"structure_guard": True, "structure_guard_soll": True, "soll_source": "composition", "other": 1}
    rows = [row("die"), row("mit", meta={"weights": weights})]
    path = tmp_path / "cand.json"
    path.write_text(json.dumps({"frame": CANDIDATE_FRAME, "rows": rows}))
    stack = guard_stack(path)
    assert set(stack) == set(STACK_FLAGS)
    assert stack["structure_guard"] is True and stack["soll_source"] == "composition"
    assert stack["structure_guard_ratchet"] is None  # absent flags read as None, never as False
    assert "other" not in stack


def test_guard_stack_is_empty_for_a_file_without_follower_meta(tmp_path: Path) -> None:
    # A stored `traced` row, an InkSight or a routeg candidate: not a follower stack.
    assert guard_stack(write_candidate(tmp_path / "plain.json", ["die"])) == {}


@pytest.mark.parametrize(
    ("meta", "outcome"),
    [
        (None, "no-rounds"),
        ({"rounds": []}, "no-rounds"),
        ({"rounds": [[_round(1), _round(2)]]}, "unguarded"),
        ({"rounds": [[_round(1, structure_rejected=False, structure_retries=0)]]}, "clean"),
        ({"rounds": [[_round(1, structure_rejected=False, structure_retries=2)]]}, "halved"),
        (
            {"rounds": [[_round(1, structure_rejected=False, structure_zonal={"pinned": 99, "accepted": True})]]},
            "zonal",
        ),
        ({"rounds": [[_round(1, structure_rejected=True)]]}, "revert-init"),
        ({"rounds": [[_round(1, structure_rejected=False), _round(2, structure_rejected=True)]]}, "revert-r1"),
    ],
)
def test_guard_outcome_names_the_tier_the_word_landed_in(meta: dict | None, outcome: str) -> None:
    """The tiers of the aug26 autopsy, read off the round records.

    `revert-init` is the one that matters most: round 1 rejected means the word
    keeps the chain init and was never followed at all — 13 of the 63 words on
    aug26, carrying 58 % of the aiou loss.
    """
    assert guard_outcome(meta) == outcome


def test_a_rejection_wins_over_a_zonal_acceptance_in_an_earlier_round() -> None:
    # Round 1 accepted zonally, round 2 rejected: the word keeps round 1 — that
    # is a revert, and the tally has to say so rather than "zonal".
    meta = {
        "rounds": [
            [
                _round(1, structure_rejected=False, structure_zonal={"pinned": 5, "accepted": True}),
                _round(2, structure_rejected=True),
            ]
        ]
    }
    assert guard_outcome(meta) == "revert-r1"


def test_eval_candidate_carries_the_guard_outcome_per_word(tmp_path: Path) -> None:
    reference = load_reference(write_root(tmp_path, [row("die")]))
    soll_rows = {"die": soll("die", crossings=2, zones=1)}
    rows = [row("die", meta={"weights": {"structure_guard": True}, "rounds": [[_round(1, structure_rejected=True)]]})]
    path = tmp_path / "cand.json"
    path.write_text(json.dumps({"frame": CANDIDATE_FRAME, "rows": rows}))
    scored = eval_candidate(path, reference, soll_rows, ["die"])["die"]
    assert scored["guard"] == "revert-init"
    assert "guard" in report_rows({"die": scored})["die"]  # the report keeps it; only the strokes go
