"""Word-gap guards: the inter-word gap is a gap between INK, not between anchors.

`SPACE_ADV` advances the CURSOR, so a word whose first letter carries its ink
far left of its own origin (the Sütterlin capitals K/C/F/G/Q/O/A/I/X) used to
reach back into the word before it — „Die Federprobe" wrote the F inside „Die"
(owner report 2026-09-05). `WORD_INK_GAP` is the floor that makes the gap a
distance between the two words' INK; it sits below every boundary today's
anchor advance already writes wide enough, so ordinary words do not move.

No DB: two synthetic glyphs plus the frozen payloads of the golden fixture.
"""

from __future__ import annotations

import gzip
import json
import math
from pathlib import Path

from core.compose import SPACE_ADV, WORD_INK_GAP, compose_word
from core.shaping import GlyphSlot


GOLDEN = Path(__file__).parent / "fixtures" / "compose_golden.json.gz"
EPS = 1e-9


def _payload(centerline: list[tuple[float, float]], entry: tuple[float, float] | None = None) -> dict:
    """Minimal render payload: one stroke, no rings, entry where the pen lands."""
    return {
        "centerlines_template": [[list(p) for p in centerline]],
        "half_widths_template": [0.05] * len(centerline),
        "entry": {"xy": list(entry or centerline[0])},
        "outline_paths": [],
        "template_guides": {"midband": 1.0},
    }


def _slots(*keys: str | None) -> list[GlyphSlot]:
    return [
        GlyphSlot(
            key=k,
            text=" " if k is None else k,
            position=None if k is None else "isolated",
            ligature=False,
            space=k is None,
        )
        for k in keys
    ]


def _split_at_word(items: list[dict], first_slot: int) -> tuple[list[dict], list[dict]]:
    """Items of the word BEFORE the gap and of the word starting at ``first_slot``.

    Writing order is the split: everything up to the second word's first glyph
    belongs to the first word — its Endstrich included, which is exactly the
    ink the next word has to clear.
    """
    cut = next(i for i, it in enumerate(items) if it.get("slot_index") == first_slot)
    return items[:cut], items[cut:]


def _ink_x(items: list[dict]) -> tuple[float, float]:
    xs = [x for it in items for x, _y in it["centerline"]]
    return min(xs), max(xs)


# A body stroke that ends the first word: rises across the join band, ink and
# origin coincide. The second word's glyph reaches ``overhang`` units LEFT of
# its own entry — the capital bow the anchor advance is blind to.
_WORD_A = [(0.0, 0.0), (0.3, 0.25), (0.6, 0.5)]


def _second_word_start(overhang: float, *, hole: bool = False) -> dict:
    """Compose "a b" (or "a ?b", ``hole``: the slot before b has no template)."""
    stroke = [(overhang, 0.4), (0.0, 0.0), (0.35, 0.3), (0.7, 0.55)]
    keys = ("a", None, "hole", "b") if hole else ("a", None, "b")
    payloads: dict[str, dict | None] = {"a": _payload(_WORD_A), "b": _payload(stroke, entry=(0.0, 0.0))}
    if hole:
        payloads["hole"] = None
    composed = compose_word(_slots(*keys), payloads, provenance=True)
    first_word, second_word = _split_at_word(composed["items"], len(keys) - 1)
    return {
        "prev_ink_max": _ink_x(first_word)[1],
        "next_ink_min": _ink_x(second_word)[0],
        # sample 1 of the second word's stroke IS its entry anchor (sample 0 is
        # the overhang the stroke starts from).
        "next_entry_x": second_word[0]["centerline"][1][0],
    }


def test_ordinary_word_gap_is_the_unchanged_anchor_advance() -> None:
    # An ordinary letter overhangs its origin by ≈0.07 xh — far less than the
    # floor gives away, so the ink floor must not bind: the word still starts
    # SPACE_ADV past the cursor the first word left behind. Pinned numbers:
    # the first word's Endstrich ends at x = 0.767225, so the entry lands at
    # 1.317225 and the ink 0.07 left of it — byte for byte what this
    # composition wrote before the floor existed.
    got = _second_word_start(-0.07)
    assert math.isclose(got["next_entry_x"], 1.3172253460254780, abs_tol=1e-12)
    assert math.isclose(got["next_ink_min"], 1.2472253460254779, abs_tol=1e-12)
    assert math.isclose(got["next_entry_x"] - got["prev_ink_max"], SPACE_ADV, abs_tol=1e-12)
    # The realised ink gap is what the anchor advance happens to leave, ABOVE
    # the floor — the floor is a minimum, not a target.
    assert got["next_ink_min"] - got["prev_ink_max"] > WORD_INK_GAP


def test_overhanging_capital_is_pushed_clear_of_the_previous_word() -> None:
    # 0.8 xh of left overhang (the G/Q/O/A class) — more than SPACE_ADV, so
    # the anchor advance alone would write the capital INTO the word before it.
    got = _second_word_start(-0.8)
    assert math.isclose(got["next_ink_min"] - got["prev_ink_max"], WORD_INK_GAP, abs_tol=1e-9)
    # …and that is a real move right, not the cursor placement by luck.
    assert got["next_entry_x"] > got["prev_ink_max"] + SPACE_ADV


def test_unrenderable_slot_after_the_gap_keeps_the_ink_anchor() -> None:
    # "Die ?Kloster": the hole between the space and the capital only widens
    # the gap — it draws no ink — so the K still has to clear "Die". Two
    # advances (0.55 + 0.55) are less than the 1.64 xh a K reaches left, which
    # is why the anchor may not be dropped at the hole.
    got = _second_word_start(-0.8, hole=True)
    assert math.isclose(got["next_ink_min"] - got["prev_ink_max"], WORD_INK_GAP, abs_tol=1e-9)


def test_golden_payloads_write_das_glueck_without_collision() -> None:
    # Real 1922 payloads: „das Glück" is the multi-word entry of the golden
    # fixture, and G is one of the left-reaching capitals (bug report).
    entry = next(w for w in json.loads(gzip.decompress(GOLDEN.read_bytes()))["words"] if w["text"] == "das Glück")
    slots = [GlyphSlot(**s) for s in entry["slots"]]
    composed = compose_word(slots, entry["payloads"], provenance=True)
    space_at = next(i for i, s in enumerate(slots) if s.space)
    das, glueck = _split_at_word(composed["items"], space_at + 1)
    assert _ink_x(glueck)[0] - _ink_x(das)[1] >= WORD_INK_GAP - EPS
