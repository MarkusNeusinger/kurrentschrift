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
from tools.tracebench.k0eval import AIOU_LOSER_GATE, eval_candidate, pair_rows, report_rows
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


# ------------------------------------------------------------------ report_rows


def test_the_report_view_drops_the_strokes_and_nothing_else() -> None:
    rows = {"die": ok_row(1, 0.5, STROKES), "mit": {"status": "skipped"}}
    report = report_rows(rows)
    assert "strokes" not in report["die"]
    assert report["die"]["soll_dist"] == 1 and report["die"]["aiou"] == 0.5
    assert report["mit"] == {"status": "skipped"}
    assert rows["die"]["strokes"] == STROKES  # the working rows keep theirs
