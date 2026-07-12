"""Unit tests for the jul11 coupling/placement branches of compose_word.

Hermetic and synthetic — tiny hand-built payloads drive exactly the guards
the golden-fixture words do not reach: the entry-couple index edge cases and
the high-exit word-final Auslauf conditions (level arm swings, a steeply
closing bow and a backward curl do not).
"""

from __future__ import annotations

import math

from core.compose import ENTRY_COUPLE_Y, SWING_HIGH_LAUNCH_DEG, _entry_couple_index, compose_word
from core.shaping import GlyphSlot


def _payload(centerline: list[list[float]]) -> dict:
    """A minimal one-stroke render payload in template units."""
    return {
        "centerlines_template": [centerline],
        "half_widths_template": [0.05] * len(centerline),
        "outline_paths": [],
        "template_guides": {"baseline": 0.0, "midband": 1.0, "ascender": 2.0, "descender": -1.0},
        "entry": {"xy": centerline[0]},
        "exit_pt": {"xy": centerline[-1]},
        "advance": 1.0,
    }


def _slot(key: str) -> GlyphSlot:
    return GlyphSlot(key=key, text=key[0], position="medial", ligature=False, space=False)


def _compose_one(centerline: list[list[float]]) -> dict:
    key = "x-medial"
    return compose_word([_slot(key)], {key: _payload(centerline)})


def test_entry_couple_index_finds_the_rising_flank_sample():
    line = [(0.0, 0.5), (0.1, 0.7), (0.2, 0.9), (0.3, 0.7)]
    i = _entry_couple_index(line)
    assert i > 0 and line[i][1] >= ENTRY_COUPLE_Y


def test_entry_couple_index_no_trim_when_already_at_couple_height():
    assert _entry_couple_index([(0.0, 0.9), (0.1, 0.5), (0.2, 0.0)]) == 0


def test_entry_couple_index_no_trim_when_head_turns_down_first():
    # A head falling before reaching the couple height is a real form, not a stub.
    assert _entry_couple_index([(0.0, 0.5), (0.1, 0.6), (0.2, 0.55), (0.3, 0.9)]) == 0


def test_entry_couple_index_no_trim_when_only_the_last_sample_reaches_it():
    # The trimmed line must keep two samples for the entry tangent.
    assert _entry_couple_index([(0.0, 0.5), (0.1, 0.6), (0.2, 0.9)]) == 0


def _generated_items(composed: dict) -> list[dict]:
    return [it for it in composed["items"] if "stroke_width" in it]


def test_high_forward_exit_earns_a_level_auslauf():
    # An r-arm-like ending: high (~0.86) and nearly level.
    composed = _compose_one([[0.0, 0.0], [0.1, 0.8], [0.7, 0.86]])
    swings = _generated_items(composed)
    assert len(swings) == 1
    line = swings[0]["centerline"]
    rise = line[-1][1] - line[0][1]
    run = line[-1][0] - line[0][0]
    assert run > 0
    # The Auslauf stays inside the level clamp band.
    assert SWING_HIGH_LAUNCH_DEG[0] - 1 <= math.degrees(math.atan2(rise, run)) <= SWING_HIGH_LAUNCH_DEG[1] + 1


def test_steeply_closing_high_bow_gets_no_auslauf():
    # A bow still rising steeply (> 45°) at its high end ends the word as-is.
    composed = _compose_one([[0.0, 0.0], [0.3, 0.2], [0.4, 0.9]])
    assert _generated_items(composed) == []


def test_backward_high_exit_gets_no_auslauf():
    # A curl travelling LEFT at its end never extends the word rightward.
    composed = _compose_one([[0.0, 0.0], [0.6, 0.85], [0.3, 0.9]])
    assert _generated_items(composed) == []
