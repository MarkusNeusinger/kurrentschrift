"""List Übergangsraum items the Wortvorrat cannot reach, with real carrier words.

The curation aid behind the ``rare-join`` layer of ``corpus.py``: for every
item (join or glyph position) that occurs in real vocabulary but in NO pool
word, print the top corpus words that carry it — ranked by frequency, so the
human curator picks common, unambiguously real words. The selection stays a
human act; this tool only surfaces candidates (proposal §4).

    uv run python -m tools.eigenhand.gaps --top 5
"""

from __future__ import annotations

import argparse
from collections import defaultdict

from core.eigenhand.coverage import word_items
from tools.eigenhand.corpus import pool_entries, shaping_form
from tools.eigenhand.store import CORPORA_DIR
from tools.eigenhand.universe import DE_WORD, EN_WORD, load_universe, read_list


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--top", type=int, default=5, help="carrier candidates per gap (default: %(default)s)")
    ap.add_argument("--joins-only", action="store_true", help="report join items only")
    args = ap.parse_args(argv)

    universe = load_universe()
    covered: set[str] = set()
    for entry in pool_entries():
        covered.update(word_items(shaping_form(entry)))

    gaps = {
        item: weight
        for item, weight in universe["items"].items()
        if item not in covered and (">" in item or not args.joins_only)
    }
    if not gaps:
        print("no gaps — every Übergangsraum item is reachable by the pool")
        return 0

    carriers: dict[str, list[tuple[int, str]]] = defaultdict(list)
    lexicon = [(w, c, "de") for w, c in read_list(CORPORA_DIR / "de_50k.txt", DE_WORD)] + [
        (w, c, "en") for w, c in read_list(CORPORA_DIR / "en_50k.txt", EN_WORD)
    ]
    for word, count, lang in lexicon:
        for item in set(word_items(word)):
            if item in gaps:
                carriers[item].append((count, f"{word} ({lang})"))

    print(f"{len(gaps)} unreachable items (of {len(universe['items'])}):")
    for item, weight in sorted(gaps.items(), key=lambda kv: (-kv[1], kv[0])):
        top = sorted(carriers.get(item, []), reverse=True)[: args.top]
        names = ", ".join(name for _, name in top) or "—"
        print(f"  {item:<16} w={weight:>12.1f}  candidates: {names}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
