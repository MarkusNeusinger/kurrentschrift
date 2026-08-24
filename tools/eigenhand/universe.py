"""Build the Übergangsraum — the weighted Soll universe of real-word items.

Reads the consult-only frequency lists under ``data/corpora/
frequencywords-2018/`` (fetched by its ``fetch_frequencywords.py``; bytes
gitignored) and accumulates, per shaped coverage item (join or glyph
position, see ``coverage.py``), the summed corpus frequency of every
OCCURRENCE of that item in real words — a word carrying an item twice
contributes its frequency twice. That is deliberate: the weight feeds the
Aufbauziel ("how often should this be written"), and an item appearing
twice per word does appear twice as often in text. Measured on the German
list, the two readings barely differ (largest gap 0.004 on the normalised
scale), so this is a definition, not a tuning knob. The result is the LOCAL weight table
``data/samples/own-hand/universe/uebergangsraum.json`` — a mechanical
derivative of a protectable frequency database, therefore never committed
(quiz-wortbank.md §4); the committed ``streifen.json`` is the frozen output.

Two deliberate properties:

* The OpenSubtitles frequency lists are all-lowercase, so capital-initial joins cannot come
  from the corpus: they enter the Übergangsraum through the curated pool
  words (real case) via ``pool.py``'s membership union. The corpus supplies
  weights, the pool supplies existence.
* English counts are damped by ``EN_WEIGHT`` before summing (mainly German,
  English as a tagged share — owner decision 2026-08-22).

    uv run python -m tools.eigenhand.universe
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from core.eigenhand.coverage import word_items
from tools.eigenhand.store import CORPORA_DIR, universe_path


UNIVERSE_FORMAT = 1
EN_WEIGHT = 0.25
MIN_WORD_LEN = 2
# Noise gate against the subtitle-corpus junk tail (abbreviations, names —
# "qt", "oxnard"): tokens under this count never define Soll items. Legit
# rare vocabulary re-enters the Soll through the pool's own words anyway
# (pool.py unions pool-word items into the universe at weight 0).
MIN_COUNT = 100

DE_WORD = re.compile(r"^[a-zäöüß]+$")
EN_WORD = re.compile(r"^[a-z]+$")


def read_list(path: Path, pattern: re.Pattern[str]) -> list[tuple[str, int]]:
    if not path.exists():
        raise SystemExit(f"{path} missing — run: uv run python {path.parent / 'fetch_frequencywords.py'}")
    out: list[tuple[str, int]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        word, count = parts[0], parts[1]
        if len(word) >= MIN_WORD_LEN and pattern.match(word) and count.isdigit() and int(count) >= MIN_COUNT:
            out.append((word, int(count)))
    return out


def accumulate(rows: list[tuple[str, int]], factor: float, into: dict[str, float]) -> int:
    used = 0
    for word, count in rows:
        items = word_items(word)
        if not items:
            continue
        used += 1
        weight = count * factor
        for item in items:
            into[item] = into.get(item, 0.0) + weight
    return used


def build(corpora: Path, en_weight: float) -> dict:
    de_rows = read_list(corpora / "de_50k.txt", DE_WORD)
    en_rows = read_list(corpora / "en_50k.txt", EN_WORD)
    weights: dict[str, float] = {}
    de_used = accumulate(de_rows, 1.0, weights)
    en_used = accumulate(en_rows, en_weight, weights)
    checksums = {
        name: hashlib.sha256((corpora / name).read_bytes()).hexdigest() for name in ("de_50k.txt", "en_50k.txt")
    }
    return {
        "format": UNIVERSE_FORMAT,
        "en_weight": en_weight,
        "corpora": checksums,
        "words_used": {"de": de_used, "en": en_used},
        "items": {item: round(weight, 3) for item, weight in sorted(weights.items())},
    }


def load_universe(path: Path | None = None) -> dict:
    target = path or universe_path()
    if not target.exists():
        raise SystemExit(f"{target} missing — run: uv run python -m tools.eigenhand.universe")
    table = json.loads(target.read_text(encoding="utf-8"))
    if table.get("format") != UNIVERSE_FORMAT:
        raise SystemExit(f"{target}: unsupported format {table.get('format')!r}")
    return table


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--corpora", type=Path, default=CORPORA_DIR, help="corpus directory (default: %(default)s)")
    ap.add_argument("--out", type=Path, default=None, help="output path (default: the local universe path)")
    ap.add_argument("--en-weight", type=float, default=EN_WEIGHT, help="damping factor for English counts")
    args = ap.parse_args(argv)

    table = build(args.corpora, args.en_weight)
    out = args.out or universe_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(table, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    joins = sum(1 for item in table["items"] if ">" in item)
    print(
        f"wrote {out}: {len(table['items'])} items ({joins} joins) from "
        f"{table['words_used']['de']} de + {table['words_used']['en']} en words"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
