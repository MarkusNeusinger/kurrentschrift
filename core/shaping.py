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
   fully syllable-aware rule (round s at morpheme boundaries) is post-MVP and
   reserved for ``core/orthography.py`` (planaenderungen.md Vorschlag D) —
   this module is the pragmatic "ſ unless word-final" mapper until then, with
   one manual escape hatch: a Fuge marker ``|`` in the input forces the round
   s at a compound's inner morpheme boundary (``Haus|tür``, ``Arbeits|amt``)
   the length heuristic gets wrong. The s right before the ``|`` renders round,
   no ligature spans the boundary, and the marker carries no glyph. Strip it
   for display with ``strip_fugen``.
2. The closed ligature set ch · ck · tz · ſt · qu · ß are *taught units* with
   their own template, not exit→entry chains (architektur.md §4), detected
   greedily but only when the cluster starts on a lowercase letter.

Everything else (arbitrary letter pairs) is connected by generated Übergänge
at compose time — the whole point of avoiding a bigram table.
"""

from __future__ import annotations

from dataclasses import dataclass


Position = str  # 'initial' | 'medial' | 'final'

# The Fuge marker: a morpheme boundary the caller places in a compound so the
# preceding s renders round (Schluss-s) and no ligature spans it. Mirrors the
# TS ``FUGE`` in app/src/domain/shaping.ts.
FUGE = "|"


def strip_fugen(text: str) -> str:
    """Drop Fuge markers for any human-facing display; render keeps the marked form."""
    return text.replace(FUGE, "")


@dataclass(frozen=True)
class GlyphSlot:
    """One shaped slot: a canonical glyph_key to render, or a gap.

    ``key`` is None for a space / a character with no glyph at all, which
    composes as an advance-only gap. ``text`` keeps the source character(s)
    for availability notices. ``joins`` is False for the detached glyph
    classes (digits, punctuation): they render but no Übergang ever enters or
    leaves them — the composer places them by ink clearance instead
    (architektur.md §4: connections are generated between letters only).
    Mirrors the TS ``GlyphSlot``.
    """

    key: str | None
    text: str
    position: Position | None
    ligature: bool
    space: bool
    joins: bool = True


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

# Non-joining glyphs: digits and punctuation are written detached — no
# Übergang ever enters or leaves them. They still fan out across the three
# positions like letters (uniform admin authoring/lock machinery); the
# position is resolved within their own run, and their templates are
# identical across positions. Bases are ascii-safe glyph_key bases.
_DIGITS: dict[str, str] = {c: c for c in "0123456789"}
_PUNCT: dict[str, str] = {
    ".": "period",
    ",": "comma",
    ";": "semicolon",
    ":": "colon",
    "!": "exclam",
    "?": "question",
    "'": "apostrophe",
    "’": "apostrophe",  # ’ typographic apostrophe
    "„": "quote-low",  # „ German opening quote
    "“": "quote-high",  # “ German closing quote
    "”": "quote-high",  # ” tolerated as closing
    "-": "hyphen",  # written as the historical double oblique stroke ⸗ (U+2E17)
    "‐": "hyphen",
    "‑": "hyphen",
    "–": "dash",  # Gedankenstrich
    "—": "dash",
    "(": "paren-open",
    ")": "paren-close",
    "§": "section",
}
_NONJOINING: dict[str, tuple[str, dict[str, str]]] = {c: (b, {}) for c, b in {**_DIGITS, **_PUNCT}.items()}

# The straight double quote is ambiguous: German writing opens low („) and
# closes high (“). Resolved by occurrence parity within the word — first "
# opens low, second closes high — so a quote after other punctuation, ("Ja"),
# still opens low.
_STRAIGHT_QUOTE = '"'


def _key_for(entry: tuple[str, dict[str, str]], position: Position) -> str:
    base, overrides = entry
    return overrides.get(position, f"{base}-{position}")


def _is_lowercase_letter(c: str) -> bool:
    """A cased lowercase letter (an uppercase initial never folds into a ligature)."""
    return c == c.lower() and c != c.upper()


# ------------------------------------------------------------------- tokenise


@dataclass(frozen=True)
class _RawToken:
    entry: tuple[str, dict[str, str]] | None  # None => unknown char or deferred allograph
    text: str
    ligature: bool
    s_allograph: bool  # lowercase s/ſ whose long-vs-round form depends on position
    force_round: bool  # an s immediately before a Fuge — always the round allograph
    joins: bool = True  # False: digits/punctuation/unknown — detached, no Übergang
    quote_allograph: bool = False  # a straight " resolved low/high by occurrence parity


def _tokenize_word(word: str) -> list[_RawToken]:
    """Greedy left-to-right tokeniser over one whitespace-free word."""
    chars = list(word)
    tokens: list[_RawToken] = []
    i = 0
    while i < len(chars):
        c = chars[i]
        nxt = chars[i + 1] if i + 1 < len(chars) else None
        # Fuge marker: a morpheme boundary carrying no glyph. Consumed here; its
        # only effect is on the preceding s (handled in the s branch below).
        if c == FUGE:
            i += 1
            continue
        if nxt is not None and _is_lowercase_letter(c):
            pair = (c + nxt).lower()
            if pair in ("ch", "ck", "tz", "qu"):
                tokens.append(_RawToken(_LIGATURES[pair], c + nxt, True, False, False))
                i += 2
                continue
            # ſt-ligature: the s before t is always a long-s context; accept
            # both the typed 's' and an already-long 'ſ'. A Fuge between them
            # (`Aus|tritt`) blocks it — nxt is then the marker, not t.
            if pair in ("st", "ſt"):
                tokens.append(_RawToken(_LIGATURES["ſt"], c + nxt, True, False, False))
                i += 2
                continue
        if c == "ß":
            tokens.append(_RawToken(_LIGATURES["ß"], c, True, False, False))
            i += 1
            continue
        # Lowercase s/ſ: defer the long-vs-round choice to position assignment,
        # unless a Fuge follows — then it's the round Schluss-s of a compound's
        # inner boundary (`Haus|tür`), regardless of position.
        if c in ("s", "ſ") and _is_lowercase_letter(c):
            tokens.append(_RawToken(None, c, False, True, nxt == FUGE))
            i += 1
            continue
        # Straight double quote: low vs high resolved by occurrence parity
        # (see _STRAIGHT_QUOTE); typographic quotes were already caught above.
        if c == _STRAIGHT_QUOTE:
            tokens.append(_RawToken(None, c, False, False, False, joins=False, quote_allograph=True))
            i += 1
            continue
        # Digits and punctuation: real glyphs, but detached (no Übergang).
        nonjoining = _NONJOINING.get(c)
        if nonjoining is not None:
            tokens.append(_RawToken(nonjoining, c, False, False, False, joins=False))
            i += 1
            continue
        entry = _LETTERS.get(c)
        tokens.append(_RawToken(entry, c, False, False, False, joins=entry is not None))
        i += 1
    return tokens


def _position_of(index: int, count: int) -> Position:
    if count == 1 or index == 0:
        return "initial"
    if index == count - 1:
        return "final"
    return "medial"


def _assign_positions(tokens: list[_RawToken]) -> list[GlyphSlot]:
    # Positions are assigned per RUN of same-joins-class tokens: a trailing
    # comma or a digit block must not steal the word-final position from the
    # last letter — "Haus," keeps the round Schluss-s — and a detached block
    # ("1922") resolves its own initial/medial/final internally.
    runs: list[list[_RawToken]] = []
    for t in tokens:
        if runs and runs[-1][-1].joins == t.joins:
            runs[-1].append(t)
        else:
            runs.append([t])
    out: list[GlyphSlot] = []
    straight_quotes = 0  # occurrences within this word, for low/high pairing
    for run in runs:
        for run_idx, t in enumerate(run):
            position = _position_of(run_idx, len(run))
            if t.s_allograph:
                # Long-s in initial/medial position, round s at the end of its
                # letter run — or forced round at a Fuge boundary.
                entry = _LETTERS["s"] if (t.force_round or position == "final") else _LETTERS["ſ"]
                out.append(GlyphSlot(_key_for(entry, position), t.text, position, False, False))
                continue
            if t.quote_allograph:
                # Straight double quote ("): German quotes pair low-then-high
                # („Ja“). Resolved by occurrence parity within the word, so a
                # quote after other punctuation — ("Ja") — still opens low.
                base = "quote-low" if straight_quotes % 2 == 0 else "quote-high"
                straight_quotes += 1
                out.append(GlyphSlot(_key_for((base, {}), position), t.text, position, False, False, joins=False))
                continue
            if t.entry is None:
                out.append(GlyphSlot(None, t.text, None, False, False, joins=False))
                continue
            out.append(GlyphSlot(_key_for(t.entry, position), t.text, position, t.ligature, False, joins=t.joins))
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
            out.append(GlyphSlot(None, " ", None, False, True, joins=False))
        out.extend(shape_word(part))
    return out


def glyph_keys_of(slots: list[GlyphSlot]) -> list[str]:
    """Distinct glyph_keys a text needs — what the composer fetches (deduped)."""
    seen: dict[str, None] = {}
    for s in slots:
        if s.key:
            seen.setdefault(s.key)
    return list(seen)


def expected_glyph_key(glyph: str, position: Position) -> str | None:
    """The canonical glyph_key the registry assigns to (glyph, position).

    None for a glyph outside the registry subset — callers fall back to the
    `{base}-{position}` naming convention. Used by the admin write path to
    reject a trace whose URL key and payload identity disagree (the template
    upsert conflicts on (style, glyph, position, variant), so a mismatched
    pair would silently rewrite another row's glyph_key).
    """
    entry = _LETTERS.get(glyph) or _LIGATURES.get(glyph) or _NONJOINING.get(glyph)
    if entry is None:
        return None
    return _key_for(entry, position)


# Every glyph_key the registry owns, across all three positions — so the admin
# write path can refuse a registry-owned key claimed by an out-of-registry
# glyph (e.g. glyph "☘" posting to "n-medial" would otherwise pass the bare
# suffix convention and collide with the real n row).
_REGISTRY_KEYS: frozenset[str] = frozenset(
    _key_for(entry, position)
    for registry in (_LETTERS, _LIGATURES, _NONJOINING)
    for entry in registry.values()
    for position in ("initial", "medial", "final")
)


def is_registry_glyph_key(glyph_key: str) -> bool:
    """Whether a registry glyph owns this key (in any position)."""
    return glyph_key in _REGISTRY_KEYS


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
