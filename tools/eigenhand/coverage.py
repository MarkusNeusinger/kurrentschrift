"""Shaped coverage bookkeeping: which joins and glyph positions a word carries.

Coverage is ALWAYS computed on shaped material (``core.shaping.shape_word``),
never on raw characters: ``Buch`` carries the join ``u>ch`` and no ``c>h``,
``Fuß`` shapes to ``F·u·sz`` and carries no s-join at all, a Fuge marker
blocks the ſt ligature, and digits/punctuation (``joins=False``) contribute
no joins. The item-key notation is ASCII-safe on purpose:

* join item:            ``"l>e"``   (left glyph_key ``>`` right glyph_key)
* glyph-position item:  ``"e@medial"`` (glyph_key ``@`` position)

Both item kinds share one Soll model (two tiers, mirroring mvp-roadmap M1's
"core ≥10, rest ≥3" and the ``LAUFFORM_MIN_OCCURRENCES = 3`` gate in
core/aggregate.py): every real item has a floor target of 3 recordings, and
frequent items climb toward 20 with the square root of their corpus weight —
frequency helps, but never drowns the rare tail.
"""

from __future__ import annotations

from collections import Counter

from core.shaping import GlyphSlot, shape_word


JOIN_SEP = ">"
POSITION_SEP = "@"

# Two-tier Soll (see module docstring): floor for everything real, ceiling for
# the most frequent items. target(w) = clamp(round(3 + 17 * sqrt(w/wmax)), 3, 20).
TARGET_FLOOR = 3
TARGET_CEIL = 20


def join_items(word: str) -> list[str]:
    """The ordered join items of one shaped word (may repeat within the word)."""
    slots = shape_word(word)
    out: list[str] = []
    prev: GlyphSlot | None = None
    for slot in slots:
        if slot.key is None or not slot.joins:
            prev = None
            continue
        if prev is not None:
            out.append(f"{prev.key}{JOIN_SEP}{slot.key}")
        prev = slot
    return out


def glyph_position_items(word: str) -> list[str]:
    """The ordered glyph-position items of one shaped word (letters only)."""
    return [
        f"{slot.key}{POSITION_SEP}{slot.position}"
        for slot in shape_word(word)
        if slot.key is not None and slot.joins and slot.position is not None
    ]


def word_items(word: str) -> list[str]:
    """All coverage items one word carries, joins first (ordered, with repeats)."""
    return join_items(word) + glyph_position_items(word)


def count_items(words: list[str]) -> Counter[str]:
    """Item → occurrence count over a word list (repetitions add up)."""
    counts: Counter[str] = Counter()
    for word in words:
        counts.update(word_items(word))
    return counts


def target_for_weight(weight: float, max_weight: float) -> int:
    """The two-tier Soll for one item given its Übergangsraum weight."""
    if max_weight <= 0 or weight <= 0:
        return TARGET_FLOOR
    scaled = TARGET_FLOOR + (TARGET_CEIL - TARGET_FLOOR) * (weight / max_weight) ** 0.5
    return max(TARGET_FLOOR, min(TARGET_CEIL, round(scaled)))
