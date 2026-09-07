"""Unit tests for tools/humanbench/tracearm.py — the FOLLOWED arm producer.

Two things decide whether a trace round shows the judge the right thing, and
neither is visible from a page that renders without error:

* the **frame**. A stored trace carries its own baseline row, an arm word is
  measured against the fixture entry's — get the fold wrong and the trace misses
  the specimen by whole x-heights while every file still parses.
* the **display**. A trace is a centerline, so the arm must carry no stroke
  width; the builder then has to emit no widths at all, because the page reads
  the mere presence of widths as „this panel draws ink" and drops the casing the
  centerline needs (menschliche-bewertung.md §3.5).

The producer/consumer seam is crossed once here for the same reason
`test_humanbench_wordarm.py` crosses it: a contract nothing walks over in a test
drifts, and the first witness is a judging session already paid for.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from tools.humanbench.build import Arm, ArmStroke, ArmWord, WordCase, _word_panel, draws_ink, load_arm
from tools.humanbench.tracearm import trace_words


BASELINES = {"die-2": 40.0, "auch": 55.0}

CANDIDATE = {
    "frame": "word_registration",
    "rows": [
        {
            "specimen_id": "die-2",
            "registration_px": {"tx": 7.0, "ty": 2.0, "baseline_row": 44.0},
            "xh_px": 33.0,
            "strokes": [[[0.0, 0.0], [0.5, 1.0]], [[0.6, 1.2], [0.7, 1.25]]],
            "status": "ok",
        },
        # A row whose registration names no baseline row falls back to the
        # entry's own, exactly as `BenchFrame.trace_to_bench` falls back.
        {
            "specimen_id": "auch",
            "registration_px": {"tx": 1.0},
            "xh_px": 30.0,
            "strokes": [[[0.0, 0.0], [1.0, 0.0]]],
            "status": "ok",
        },
    ],
}


def test_the_row_s_own_baseline_row_is_folded_into_ty():
    """The one piece of arithmetic in the module: the two frames differ by the
    two baseline rows, so `ty` absorbs the difference and nothing else moves."""
    words, skipped = trace_words(CANDIDATE, BASELINES)
    assert skipped == []
    # 44 (row) + 2 (row ty) − 40 (entry) = 6
    assert words["die-2"]["registration"] == {"xh_px": 33.0, "tx": 7.0, "ty": 6.0}
    # No baseline row of its own → the entry's, so the fold is exactly the row ty.
    assert words["auch"]["registration"] == {"xh_px": 30.0, "tx": 1.0, "ty": 0.0}


def test_a_trace_arm_carries_no_stroke_width():
    """A follower arm is judged as a CENTERLINE — the display of §3.5 — so it
    must not smuggle a weight the page would read as ink."""
    words, _ = trace_words(CANDIDATE, BASELINES)
    assert [len(s["points"]) for s in words["die-2"]["strokes"]] == [2, 2]
    assert all("width" not in stroke for word in words.values() for stroke in word["strokes"])


@pytest.mark.parametrize(
    "row, reason",
    [
        ({"specimen_id": "die-2", "status": "failed", "strokes": []}, "failed"),
        ({"specimen_id": "nowhere", "xh_px": 30.0, "strokes": [[[0, 0], [1, 1]]]}, "not a scorable entry"),
        ({"specimen_id": "auch", "xh_px": None, "strokes": [[[0, 0], [1, 1]]]}, "no xh_px"),
    ],
)
def test_a_row_that_cannot_be_drawn_is_named_not_dropped(row, reason):
    """A silently shortened round still looks complete — the same rule the
    builder applies to a word only one arm draws."""
    words, skipped = trace_words({"frame": "word_registration", "rows": [row]}, BASELINES)
    assert words == {}
    assert len(skipped) == 1 and reason in skipped[0]


def test_what_the_producer_writes_is_what_the_builder_reads(tmp_path):
    """The contract seam, crossed once."""
    words, _ = trace_words(CANDIDATE, BASELINES)
    path = tmp_path / "arm.json"
    path.write_text(json.dumps({"arm": "K-E2", "words": words}))
    arm = load_arm(path)
    assert arm.name == "K-E2"
    word = arm.words["die-2"]
    assert (word.xh, word.tx, word.ty) == (33.0, 7.0, 6.0)
    assert len(word.strokes) == 2 and word.strokes[0].width == 0.0
    assert word.fills == ()


def test_an_all_zero_widths_array_leaves_the_panel_as_a_centerline():
    """The builder's half of the display rule: the page switches to the ink
    display on the PRESENCE of widths, so a width-less arm must emit none."""
    arm = ArmWord(
        xh=30.0, tx=0.0, ty=0.0, strokes=(ArmStroke(points=np.array([[0.0, 0.0], [1.0, 1.0]]), width=0.0),), fills=()
    )
    case = WordCase(
        entry_id="die-2",
        text="die",
        crop=np.zeros((60, 90), dtype=np.uint8),
        baseline_row=40.0,
        xh=30.0,
        arms={"base": arm},
        peak=0.0,
    )
    panel = _word_panel(arm, case, (0, 0, 90, 60), 2)
    assert "strokes" in panel
    assert "widths" not in panel and "fills" not in panel


@pytest.mark.parametrize(
    "width, fills, ink",
    [
        (0.0, (), False),  # a trace arm: a bare centerline
        (0.145, (), True),  # a connector capsule of its own weight
        (0.0, ((np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]]),),), True),  # a silhouette
    ],
)
def test_the_question_follows_the_arms_not_a_flag(tmp_path, width, fills, ink):
    """„Echter geschrieben" has nothing to hold on to on a centerline, so the
    round's recorded question is read off the arms — otherwise a result file
    claims to answer a question the round never asked (§7, §8a)."""
    arm = Arm(
        name="X",
        path=tmp_path / "x.json",
        digest="0",
        words={
            "die-2": ArmWord(
                xh=30.0,
                tx=0.0,
                ty=0.0,
                strokes=(ArmStroke(points=np.array([[0.0, 0.0], [1.0, 1.0]]), width=width),),
                fills=fills,
            )
        },
        meta={},
    )
    assert draws_ink(arm) is ink
