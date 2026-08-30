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

import re
from collections import Counter

from core.eigenhand.plan import shaping_form_of
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
    """The ordered glyph-position items of one shaped word — EVERY keyed slot.

    Letters and ligatures, but also the detached glyph classes (digits,
    punctuation, ``joins=False``): the hand has to learn ``7`` and ``§`` too
    (owner, 2026-08-22), so they carry Soll like any glyph. They still
    contribute no JOIN items — the composer places them by ink clearance.
    """
    return [
        f"{slot.key}{POSITION_SEP}{slot.position}"
        for slot in shape_word(word)
        if slot.key is not None and slot.position is not None
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


def plan_items(plan: dict) -> Counter[str]:
    """Item counts the whole strip plan carries — shaped through the plan's forms.

    The denominator of everything: what a hand will hold once every planned
    strip is written. Reads the plan's own ``forms`` map, so it needs no
    curation source (that lives in ``tools/eigenhand/corpus.py``, which the
    API does not have).
    """
    counts: Counter[str] = Counter()
    for strip in plan["strips"].values():
        for word in strip["words"]:
            counts.update(word_items(shaping_form_of(plan, word)))
    return counts


_LIGATURES = {"ch", "ck", "tz", "longst", "St", "qu", "sz"}
_LOWER_EXTRA = {"ae", "oe", "ue", "longs"}
_UPPER_EXTRA = {"Ae", "Oe", "Ue"}


def classify_key(key: str) -> str:
    """Bucket a glyph_key: klein · gross · ligatur · ziffer · zeichen."""
    if key in _LIGATURES:
        return "ligatur"
    if key.isdigit():
        return "ziffer"
    if key in _LOWER_EXTRA or (len(key) == 1 and key.islower()):
        return "klein"
    if key in _UPPER_EXTRA or (len(key) == 1 and key.isupper()):
        return "gross"
    return "zeichen"


def split_items(items: Counter[str]) -> tuple[Counter[str], Counter[str]]:
    """Split coverage items into (per glyph_key counts, per join counts).

    Glyph-position items (``e@medial``) collapse onto their key: the question
    a Bestand answers is "has this letter been written", not "in which of its
    three positions" — the positions are render context, not separate library
    units (architektur.md §3).
    """
    glyphs: Counter[str] = Counter()
    joins: Counter[str] = Counter()
    for item, count in items.items():
        if JOIN_SEP in item:
            joins[item] += count
        else:
            glyphs[item.split(POSITION_SEP)[0]] += count
    return glyphs, joins


def target_for_weight(weight: float, max_weight: float) -> int:
    """The two-tier Soll for one item given its Übergangsraum weight."""
    if max_weight <= 0 or weight <= 0:
        return TARGET_FLOOR
    scaled = TARGET_FLOOR + (TARGET_CEIL - TARGET_FLOOR) * (weight / max_weight) ** 0.5
    return max(TARGET_FLOOR, min(TARGET_CEIL, round(scaled)))


def soll_from_weights(weights: dict[str, float]) -> tuple[dict[str, float], dict[str, int]]:
    """The Soll model `(weights, targets)` over a COMPLETE Übergangsraum table.

    The ONE derivation of the two-tier targets, shared by the local chain
    (`tools/eigenhand/pool.py::soll_model`, after its pool union) and the
    server (the stored `eigenhand_uebergangsraum` row, which already holds the
    union). "Complete" matters: every target is scaled against the table's own
    maximum, so a filtered or partial table would rescale every Soll at once.
    """
    table = dict(weights)
    max_weight = max(table.values(), default=1.0) or 1.0
    return table, {item: target_for_weight(w, max_weight) for item, w in table.items()}


_ITEM_KEY = re.compile(r"^[A-Za-z0-9-]+(?:>[A-Za-z0-9-]+|@(?:initial|medial|final))$")


def matches_item(wanted: str, items: list[str]) -> bool:
    """Whether a word's items hold `wanted` — an item key, or a bare glyph key.

    A bare key (`a`, `longs`) stands for the glyph in EVERY position: the
    coverage grid shows one cell per glyph, and clicking it should bring up
    every written word that holds the letter, wherever it sits. A join
    (`a>b`) and a positioned glyph (`a@medial`) match exactly. A bare key
    never matches a join — `a` is not `a>b`, the join has its own cell.
    """
    if JOIN_SEP in wanted or POSITION_SEP in wanted:
        return wanted in items
    prefix = f"{wanted}{POSITION_SEP}"
    return any(item.startswith(prefix) for item in items)


_GLYPH_KEY = re.compile(r"^[A-Za-z0-9-]+$")


def is_item_filter(text: str) -> bool:
    """Whether `text` may narrow a listing: an item key, or a bare glyph key.

    The Soll universe holds only joins and positioned glyphs (`is_item_key`);
    a filter additionally takes the bare key the coverage grid shows one cell
    for, so that cell can ask for its glyph in every position at once.
    """
    return is_item_key(text) or bool(_GLYPH_KEY.match(text))


def is_item_key(item: str) -> bool:
    """Whether a string is spelled like a coverage item (`l>e` or `e@medial`).

    A syntax check, not a vocabulary check: the server validates a pushed
    table with it, and the glyph-key registry lives in `core/shaping.py`.
    """
    return bool(_ITEM_KEY.match(item))
