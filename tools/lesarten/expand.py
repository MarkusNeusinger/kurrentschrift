"""Expand a hunspell dictionary (.dic + .aff) into its word forms.

One affix layer, the way `unmunch` would do it for the plain cases: every
stem carries flags; for each flag the .aff lists suffix (SFX) or prefix (PFX)
rules „strip this, add that, if the stem matches this condition". Stems
flagged ONLYINCOMPOUND (`o` in igerman98) are compound parts, not words;
stems flagged NEEDAFFIX (`h`) count only in their affixed forms. Compounding
itself (COMPOUNDBEGIN/MIDDLE/END) is not expanded — hunspell builds
Kirchenbuch from Kirchen + Buch at check time, and enumerating that space is
neither finite nor what a reading list wants.

Letter-only forms (German letters incl. umlauts and ß) are kept; anything
with digits, hyphens or apostrophes is dropped.

    uv run python -m tools.lesarten.expand   # prints the counts
"""

from __future__ import annotations

import collections
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DICT_DIR = REPO_ROOT / "data" / "corpora" / "igerman98"
DIC = DICT_DIR / "de_DE_frami.dic"
AFF = DICT_DIR / "de_DE_frami.aff"

LETTERS = re.compile(r"[A-Za-zÄÖÜäöüß]+")

# Rule = (strip, add, condition regex); prefix rules anchor at the start,
# suffix rules at the end.
Rule = tuple[str, str, str]


def parse_aff(text: str) -> tuple[dict[tuple[str, str], list[Rule]], str, str]:
    """(kind, flag) → rules, plus the ONLYINCOMPOUND and NEEDAFFIX flags."""
    rules: dict[tuple[str, str], list[Rule]] = collections.defaultdict(list)
    only_in_compound = ""
    need_affix = ""
    for line in text.splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "ONLYINCOMPOUND" and len(parts) > 1:
            only_in_compound = parts[1]
        elif parts[0] == "NEEDAFFIX" and len(parts) > 1:
            need_affix = parts[1]
        elif parts[0] in ("SFX", "PFX") and len(parts) >= 5:
            kind, flag, strip, add = parts[0], parts[1], parts[2], parts[3]
            cond = parts[4] if len(parts) > 4 else "."
            rules[(kind, flag)].append(("" if strip == "0" else strip, "" if add == "0" else add.split("/")[0], cond))
    return rules, only_in_compound, need_affix


def _apply(word: str, kind: str, rules: list[Rule]) -> list[str]:
    out: list[str] = []
    for strip, add, cond in rules:
        if kind == "SFX":
            if strip and not word.endswith(strip):
                continue
            if cond != "." and not re.search(cond + "$", word):
                continue
            out.append((word[: -len(strip)] if strip else word) + add)
        else:
            if strip and not word.startswith(strip):
                continue
            if cond != "." and not re.match(cond, word):
                continue
            out.append(add + (word[len(strip) :] if strip else word))
    return out


def expand(dic_text: str, aff_text: str) -> set[str]:
    """Every letter-only word form the dictionary licenses on its own."""
    rules, only_in_compound, need_affix = parse_aff(aff_text)
    forms: set[str] = set()
    lines = dic_text.splitlines()
    for line in lines[1:]:  # the first line is the entry count
        word, _, flags = line.partition("/")
        word = word.strip()
        if not word or not LETTERS.fullmatch(word):
            continue
        if only_in_compound and only_in_compound in flags:
            continue
        if not (need_affix and need_affix in flags):
            forms.add(word)
        for flag in flags:
            for kind in ("SFX", "PFX"):
                rule_list = rules.get((kind, flag))
                if rule_list:
                    forms.update(f for f in _apply(word, kind, rule_list) if LETTERS.fullmatch(f))
    return forms


def load_forms(dic: Path = DIC, aff: Path = AFF) -> set[str]:
    if not dic.exists() or not aff.exists():
        raise SystemExit(
            f"dictionary missing under {DICT_DIR} — run `uv run python {DICT_DIR / 'fetch_igerman98.py'}` first"
        )
    return expand(dic.read_text(encoding="latin-1"), aff.read_text(encoding="latin-1"))


def main() -> int:
    forms = load_forms()
    print(f"{len(forms):,} forms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
