"""tools.lesarten.expand — one affix layer of a hunspell dictionary."""

from __future__ import annotations

from tools.lesarten.expand import expand


AFF = """SET ISO8859-1
ONLYINCOMPOUND o
NEEDAFFIX h

SFX N Y 2
SFX N 0 n .
SFX N e en e

PFX U Y 1
PFX U 0 un .
"""

DIC = """5
Mühle/N
Kirche/o
frag/hN
schön/U
Straße-1
"""


def test_expands_suffixes_and_prefixes_and_keeps_the_stem() -> None:
    forms = expand(DIC, AFF)
    assert {"Mühle", "Mühlen"} <= forms
    assert {"schön", "unschön"} <= forms


def test_compound_only_and_needaffix_stems_are_not_words_on_their_own() -> None:
    forms = expand(DIC, AFF)
    assert "Kirche" not in forms  # ONLYINCOMPOUND
    assert "frag" not in forms and "fragn" in forms  # NEEDAFFIX: only the affixed form counts


def test_only_letter_forms_survive() -> None:
    forms = expand(DIC, AFF)
    assert not any("-" in f or f[0].isdigit() for f in forms)
    assert "Straße-1" not in forms
