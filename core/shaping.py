"""Text shaping for the German cursive scripts — Python twin of the SPA's shaping.

Turns a typed word or sentence into the ordered sequence of canonical
glyph_keys the composer renders and connects. Mirrors
``app/src/domain/shaping.ts`` (and the registry subset of
``app/src/domain/glyphs.ts`` it needs) so the server-side word endpoint shapes
text exactly like the client's quiz word-bank gating does — keep the two in
sync when either changes.

Two orthographic rules carry the historical look (architektur.md §3/§4):

1. Long-s vs round-s (Lang-s ſ / Schluss-s s): the long-s writes at the start
   and in the middle of a word, the round s only at the end. Separate
   allographs with their own ductus (historical keys: ſ-medial → ``s-medial``,
   round-s medial → ``s-round-medial``), not one letter with a transition. The
   syllable-aware rule (round s at morpheme boundaries) is post-MVP and
   reserved for ``core/orthography.py`` (planaenderungen.md Vorschlag D) —
   this module is the pragmatic "ſ unless word-final" mapper until then.
2. The closed ligature set ch · ck · tz · ſt · qu · ß are *taught units* with
   their own template, not exit→entry chains (architektur.md §4), detected
   greedily but only when the cluster starts on a lowercase letter.

Everything else (arbitrary letter pairs) is connected by generated Übergänge
at compose time — the whole point of avoiding a bigram table.
"""

from __future__ import annotations

from dataclasses import dataclass


Position = str  # 'initial' | 'medial' | 'final'


@dataclass(frozen=True)
class GlyphSlot:
    """One shaped slot: a canonical glyph_key to render, or a gap.

    ``key`` is None for a space / a character with no glyph (punctuation,
    digits), which composes as an advance-only gap. ``text`` keeps the source
    character(s) for availability notices. Mirrors the TS ``GlyphSlot``.
    """

    key: str | None
    text: str
    position: Position | None
    ligature: bool
    space: bool


# --------------------------------------------------------------- the registry
# Subset of app/src/domain/glyphs.ts: char → (glyph_key base, per-position key
# overrides). The overrides preserve historical DB keys — never change them.

_LOWER_EXTRA = {"ä": "ae", "ö": "oe", "ü": "ue"}
_UPPER_EXTRA = {"Ä": "Ae", "Ö": "Oe", "Ü": "Ue"}

# char → (base, overrides). Round s keeps its historical final key `s-final`;
# its medial gets `s-round-medial` so it never collides with long-s' `s-medial`.
_LETTERS: dict[str, tuple[str, dict[str, str]]] = {}
for _c in "abcdefghijklmnopqrtuvwxyz":  # s handled explicitly below
    _LETTERS[_c] = (_c, {})
_LETTERS["s"] = ("s", {"medial": "s-round-medial"})
_LETTERS["ſ"] = ("longs", {"medial": "s-medial"})
for _c, _base in _LOWER_EXTRA.items():
    _LETTERS[_c] = (_base, {})
for _c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    _LETTERS[_c] = (_c, {})
for _c, _base in _UPPER_EXTRA.items():
    _LETTERS[_c] = (_base, {})

# The closed ligature set, keyed by its written form (architektur.md §4).
_LIGATURES: dict[str, tuple[str, dict[str, str]]] = {
    "ch": ("ch", {}),
    "ck": ("ck", {}),
    "tz": ("tz", {}),
    "ſt": ("longst", {}),
    "qu": ("qu", {}),
    "ß": ("sz", {}),
}


def _key_for(entry: tuple[str, dict[str, str]], position: Position) -> str:
    base, overrides = entry
    return overrides.get(position, f"{base}-{position}")


def _is_lowercase_letter(c: str) -> bool:
    """A cased lowercase letter (an uppercase initial never folds into a ligature)."""
    return c == c.lower() and c != c.upper()


# ------------------------------------------------------------------- tokenise


@dataclass(frozen=True)
class _RawToken:
    entry: tuple[str, dict[str, str]] | None  # None => unknown char or deferred s-allograph
    text: str
    ligature: bool
    s_allograph: bool  # lowercase s/ſ whose long-vs-round form depends on position


def _tokenize_word(word: str) -> list[_RawToken]:
    """Greedy left-to-right tokeniser over one whitespace-free word."""
    chars = list(word)
    tokens: list[_RawToken] = []
    i = 0
    while i < len(chars):
        c = chars[i]
        nxt = chars[i + 1] if i + 1 < len(chars) else None
        if nxt is not None and _is_lowercase_letter(c):
            pair = (c + nxt).lower()
            if pair in ("ch", "ck", "tz", "qu"):
                tokens.append(_RawToken(_LIGATURES[pair], c + nxt, True, False))
                i += 2
                continue
            # ſt-ligature: the s before t is always a long-s context; accept
            # both the typed 's' and an already-long 'ſ'.
            if pair in ("st", "ſt"):
                tokens.append(_RawToken(_LIGATURES["ſt"], c + nxt, True, False))
                i += 2
                continue
        if c == "ß":
            tokens.append(_RawToken(_LIGATURES["ß"], c, True, False))
            i += 1
            continue
        if c in ("s", "ſ") and _is_lowercase_letter(c):
            tokens.append(_RawToken(None, c, False, True))
            i += 1
            continue
        tokens.append(_RawToken(_LETTERS.get(c), c, False, False))
        i += 1
    return tokens


def _position_of(index: int, count: int) -> Position:
    if count == 1 or index == 0:
        return "initial"
    if index == count - 1:
        return "final"
    return "medial"


def _assign_positions(tokens: list[_RawToken]) -> list[GlyphSlot]:
    out: list[GlyphSlot] = []
    for idx, t in enumerate(tokens):
        position = _position_of(idx, len(tokens))
        if t.s_allograph:
            # Long-s in initial/medial position, round s word-final.
            entry = _LETTERS["s"] if position == "final" else _LETTERS["ſ"]
            out.append(GlyphSlot(_key_for(entry, position), t.text, position, False, False))
            continue
        if t.entry is None:
            out.append(GlyphSlot(None, t.text, None, False, False))
            continue
        out.append(GlyphSlot(_key_for(t.entry, position), t.text, position, t.ligature, False))
    return out


# ----------------------------------------------------------------- public API


def shape_word(word: str) -> list[GlyphSlot]:
    """One word → its ordered glyph slots (positions + allographs resolved)."""
    if not word:
        return []
    return _assign_positions(_tokenize_word(word))


def shape_text(text: str) -> list[GlyphSlot]:
    """A whole line → slots, with a space slot between words (breaks the join)."""
    out: list[GlyphSlot] = []
    for part in text.split():
        if out:
            out.append(GlyphSlot(None, " ", None, False, True))
        out.extend(shape_word(part))
    return out


def glyph_keys_of(slots: list[GlyphSlot]) -> list[str]:
    """Distinct glyph_keys a text needs — what the composer fetches (deduped)."""
    seen: dict[str, None] = {}
    for s in slots:
        if s.key:
            seen.setdefault(s.key)
    return list(seen)


def decompose_ligature_slot(slot: GlyphSlot) -> list[GlyphSlot] | None:
    """Fallback for a ligature whose canonical is missing: split into letters.

    A closed-set cluster without a template decomposes into its constituent
    letters so the word still writes with a generated Übergang instead of a
    connector-severing hole. Sub-letters inherit the cluster's word position
    (first keeps ``initial``, last keeps ``final``, the rest is medial). ß
    stays atomic: its historic decomposition (ſs/ſz) is itself an allograph
    question — a naive split would write ſſ mid-word. Mirrors the TS
    ``decomposeLigatureSlot``.
    """
    if not slot.ligature or not slot.position:
        return None
    chars = list(slot.text)
    if len(chars) < 2:  # ß
        return None
    out: list[GlyphSlot] = []
    for i, raw in enumerate(chars):
        if i == 0 and slot.position == "initial":
            position = "initial"
        elif i == len(chars) - 1 and slot.position == "final":
            position = "final"
        else:
            position = "medial"
        c = raw.lower()
        if c in ("s", "ſ"):
            entry = _LETTERS["s"] if position == "final" else _LETTERS["ſ"]
        else:
            entry = _LETTERS.get(c)
        out.append(GlyphSlot(_key_for(entry, position) if entry else None, raw, position, False, False))
    return out
