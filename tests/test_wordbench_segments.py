"""score_word_segments: per-connector/per-glyph attribution on a synthetic word.

Fully synthetic (no fixtures, no DB): a straight horizontal "specimen" skeleton
and a composed word whose items either sit exactly on it (penalty ≈ 0) or are
displaced (penalty attributed to exactly the displaced segment).
"""

from __future__ import annotations

import numpy as np

from tools.wordbench.metric import score_word_segments


XH = 20.0  # px per x-height unit
WORD_META = {"rect": [0, 0, 200, 60], "baseline_y": 40, "midband_y": 20}
REGISTRATION = {"tx": 0.0, "ty": 0.0, "xh_px": XH}
NIB = 0.07


def _skeleton() -> np.ndarray:
    """Horizontal ink line at composed-frame y=0.5 (crop row 30), x = 10..190 px."""
    skel = np.zeros((60, 200), dtype=bool)
    skel[30, 10:190] = True
    return skel


def _line(x0: float, x1: float, y: float, n: int = 12) -> list[list[float]]:
    """Composed-frame polyline (x-height units, y up) along a constant height."""
    return [[x0 + (x1 - x0) * i / (n - 1), y] for i in range(n)]


def _word(connector_y: float = 0.5) -> dict:
    """Two glyphs joined by one connector, all on the skeleton row unless the
    connector is displaced via `connector_y`."""
    ring = [[[0.0, 0.0], [0.1, 0.0], [0.1, 0.1]]]  # presence marks the item as a glyph stroke
    return {
        "items": [
            {"centerline": _line(0.5, 2.0, 0.5), "rings": ring, "slot_index": 0, "glyph_key": "a-initial"},
            {
                "centerline": _line(2.0, 3.0, connector_y),
                "stroke_width": 0.1,
                "pair": ["a-initial", "b-final"],
                "from_slot": 0,
                "to_slot": 1,
            },
            {"centerline": _line(3.0, 4.5, 0.5), "rings": ring, "slot_index": 1, "glyph_key": "b-final"},
        ],
        "missing": [],
    }


def test_rows_in_writing_order_with_labels() -> None:
    rows = score_word_segments(_word(), WORD_META, _skeleton(), NIB, REGISTRATION)
    assert [r["kind"] for r in rows] == ["glyph", "connector", "glyph"]
    assert rows[0]["glyph_key"] == "a-initial" and rows[0]["slot_index"] == 0
    assert rows[1]["pair"] == ["a-initial", "b-final"]
    assert (rows[1]["from_slot"], rows[1]["to_slot"]) == (0, 1)
    assert rows[2]["glyph_key"] == "b-final"
    for r in rows:
        assert 0.0 <= r["penalty"] <= 1.0
        lo, hi = r["x_span_px"]
        assert lo < hi


def test_aligned_word_scores_near_zero() -> None:
    rows = score_word_segments(_word(), WORD_META, _skeleton(), NIB, REGISTRATION)
    assert all(r["penalty"] < 0.1 for r in rows)


def test_displaced_connector_is_blamed_not_the_glyphs() -> None:
    rows = score_word_segments(_word(connector_y=0.9), WORD_META, _skeleton(), NIB, REGISTRATION)
    glyph_rows = [r for r in rows if r["kind"] == "glyph"]
    connector = next(r for r in rows if r["kind"] == "connector")
    assert connector["penalty"] > 0.3
    assert connector["transition"] == connector["penalty"]
    assert all(r["penalty"] < 0.1 for r in glyph_rows)
    assert all(r["coverage"] == r["penalty"] for r in glyph_rows)


def test_deferred_diacritic_groups_with_its_glyph() -> None:
    word = _word()
    # A diacritic stroke flushed at the word end still belongs to slot 0. It
    # sits LEFT of the body's own x-span (body starts at 0.5), so the span
    # assertion below can only pass if the mark was actually merged into its
    # glyph's segment — not if it was dropped or given a row of its own.
    word["items"].append(
        {
            "centerline": _line(0.05, 0.35, 1.4, n=4),
            "rings": [[[0.0, 0.0], [0.1, 0.0], [0.1, 0.1]]],
            "slot_index": 0,
            "glyph_key": "a-initial",
            "diacritic": True,
        }
    )
    rows = score_word_segments(word, WORD_META, _skeleton(), NIB, REGISTRATION)
    assert [r["kind"] for r in rows] == ["glyph", "connector", "glyph"]  # no extra row
    assert rows[0]["x_span_px"][0] <= 0.35 * XH  # the mark widened its glyph's span leftward


def test_registration_shift_is_applied() -> None:
    """Segments explain THE SAME fit as score_word: with the specimen drawn
    shifted and the matching registration passed in, everything still scores
    near zero — while ignoring the shift would leave every segment misaligned."""
    shifted = np.zeros((60, 200), dtype=bool)
    shifted[24, 19:199] = True  # the _skeleton() line moved by (tx=+9, ty=-6)
    reg = {"tx": 9.0, "ty": -6.0, "xh_px": XH}
    rows = score_word_segments(_word(), WORD_META, shifted, NIB, reg)
    assert all(r["penalty"] < 0.1 for r in rows)
    lo, _hi = rows[0]["x_span_px"]
    assert lo == 0.5 * XH + 9.0  # spans are reported in shifted crop pixels
    # Dropping the shift misaligns every segment by 6 px vertically (sat = 12 px).
    unshifted = score_word_segments(_word(), WORD_META, shifted, NIB, REGISTRATION)
    assert all(r["penalty"] > 0.2 for r in unshifted)


def test_failed_or_empty_input_yields_no_rows() -> None:
    assert score_word_segments({"items": [], "missing": []}, WORD_META, _skeleton(), NIB, REGISTRATION) == []
    assert score_word_segments({"items": [], "missing": ["x-final"]}, WORD_META, _skeleton(), NIB, REGISTRATION) == []
    empty = np.zeros((60, 200), dtype=bool)
    assert score_word_segments(_word(), WORD_META, empty, NIB, REGISTRATION) == []
