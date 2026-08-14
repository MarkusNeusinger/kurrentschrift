"""Tests for the word-trace assembly (`tools.pairlab.trace`).

The assembler moved out of `tools.laufform.harvest` so the ink-follower can use
it without an import cycle. Two things are pinned here and nothing else — the
behaviour itself is exercised case by case in `tests/test_laufform_harvest.py`,
which imports the very same objects through the harvest:

* the **re-export identity**: every moved name is the SAME object under both
  import paths, so no consumer can end up with a second copy of the rule, and
* one **smoke case** per moved function, so an import that resolves is also an
  import that works.
"""

from __future__ import annotations

import numpy as np
import pytest

from tools.laufform import harvest as harvest_mod
from tools.pairlab import trace as trace_mod
from tools.pairlab.trace import _px_to_word_units, assemble_word_strokes, cap_word_strokes


XH = 40.0
BASELINE_ROW = 110.0
X_ORIGIN = 30.0
REGISTRATION = {"tx": X_ORIGIN, "ty": 0.0, "baseline_row": BASELINE_ROW}

MOVED = (
    "DIACRITIC_MIN_Y",
    "MAX_STROKE_POINTS",
    "MAX_WORD_STROKES",
    "SEAM_DEDUP_PX",
    "_is_diacritic",
    "_px_to_word_units",
    "assemble_word_strokes",
    "cap_word_strokes",
)


def _to_px(points_units) -> np.ndarray:
    a = np.asarray(points_units, dtype=float).reshape(-1, 2)
    return np.column_stack([X_ORIGIN + a[:, 0] * XH, BASELINE_ROW - a[:, 1] * XH])


def _entry(kind: str, segment: int, points_units, *, slot=None, key=None, stroke_index: int = 0) -> dict:
    return {
        "kind": kind,
        "segment_index": segment,
        "slot_index": slot,
        "key": key,
        "stroke_index": stroke_index,
        "points_px": _to_px(points_units),
    }


# ------------------------------------------------------------ the re-exports


@pytest.mark.parametrize("name", MOVED)
def test_the_harvest_re_exports_the_very_same_object(name: str) -> None:
    """`is`, not `==`: a copy would let the two paths drift apart silently."""
    assert getattr(harvest_mod, name) is getattr(trace_mod, name)


# --------------------------------------------------------------- smoke cases


def test_a_connector_welds_its_two_letters_into_one_pen_run() -> None:
    """The seam sample belongs to both sides and is written once."""
    entries = [
        _entry("letter", 0, [(0.2, 0.2), (1.0, 0.3)], slot=0, key="a", stroke_index=0),
        _entry("connector", 1, [(1.0, 0.3), (1.6, 0.3)]),
        _entry("letter", 2, [(1.6, 0.3), (2.4, 0.4)], slot=1, key="b", stroke_index=0),
    ]
    strokes = assemble_word_strokes(entries, traced_slots={0, 1}, xh=XH, registration=REGISTRATION)
    assert len(strokes) == 1
    assert len(strokes[0]) == 2 + 1 + 1  # both shared samples dropped
    assert strokes[0][0] == pytest.approx([0.2, 0.2], abs=1e-3)
    assert strokes[0][-1] == pytest.approx([2.4, 0.4], abs=1e-3)


def test_the_word_frame_puts_the_baseline_at_zero_and_the_midband_at_one() -> None:
    px = _to_px([(0.0, 0.0), (1.5, 1.0)])
    back = _px_to_word_units(px[:, 0], px[:, 1], XH, REGISTRATION)
    assert back == pytest.approx(np.array([[0.0, 0.0], [1.5, 1.0]]), abs=1e-4)


def test_the_wire_caps_hold(capsys: pytest.CaptureFixture) -> None:
    within = [[[0.0, 0.0], [1.0, 1.0]]]
    assert cap_word_strokes(within) == within
    assert capsys.readouterr().out == ""
    long_run = [[float(i) * 1e-3, 0.0] for i in range(trace_mod.MAX_STROKE_POINTS + 7)]
    capped = cap_word_strokes([long_run], label="smoke")
    assert len(capped[0]) == trace_mod.MAX_STROKE_POINTS
    assert "downsampled" in capsys.readouterr().out
