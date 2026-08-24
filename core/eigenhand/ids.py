"""The id vocabulary of the capture chain — hand, Bogen, Streifen, Fassung.

Every one of these becomes a directory name locally AND a row key on the
server, so both surfaces have to agree on what is a legal id. The predicates
are pure and total: they answer yes or no. The CLI wraps them in the refusals
that suit a terminal (``tools/eigenhand/store.py``), the API in 4xx responses
— neither invents its own idea of a well-formed id.

`[0-9]` rather than `\\d`, and `fullmatch` rather than `match`: `\\d` also
matches non-ASCII digits, and `$` also matches before a trailing newline.
"""

from __future__ import annotations

import re


# The known style ids (styles table seed, migration 0004) — a hand id is
# `<schreiber>-<stil>` and the style is inferred from its suffix.
STYLE_IDS = ("kurrent", "suetterlin", "offenbacher")

HAND_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*-(?:" + "|".join(STYLE_IDS) + r")")
SHEET_ID = re.compile(r"B[0-9]{4,}")
STRIP_ID = re.compile(r"S[0-9]{4,}")
FASSUNG_ID = re.compile(r"F[0-9]{2,}")

# The Siebung's verdicts. `angenommen` is training data, `verworfen` is
# recorded but never filed, `zurueckgezogen` is an explicit withdrawal
# (tools/eigenhand/redo.py --retire).
STATUSES = ("angenommen", "verworfen", "zurueckgezogen")


def is_hand_id(value: str) -> bool:
    return bool(HAND_ID.fullmatch(value))


def is_sheet_id(value: str) -> bool:
    return bool(SHEET_ID.fullmatch(value))


def is_strip_id(value: str) -> bool:
    return bool(STRIP_ID.fullmatch(value))


def is_fassung_id(value: str) -> bool:
    return bool(FASSUNG_ID.fullmatch(value))


def style_of_hand(hand: str) -> str | None:
    """The style a `<schreiber>-<stil>` id names, or None if it names none."""
    for style in STYLE_IDS:
        if hand.endswith(f"-{style}"):
            return style
    return None
