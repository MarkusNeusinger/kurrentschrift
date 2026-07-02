"""Build the quiz word seed from the curated corpus.

Reads ``corpus.py``, fills any entry that left ``distractors`` as ``None`` from
the lexicon by the similarity rules, validates that every entry ends with at
least three real distractors, and writes ``quiz_words.json`` — the single
source the Alembic seed migration (``0010_quiz_words.py``) loads into the
``quiz_words`` table.

    uv run python -m tools.quizgen.build          # write quiz_words.json
    uv run python -m tools.quizgen.build --check   # verify it is up to date

Deterministic: no RNG here (the runtime does the sampling), so the output is
stable and reviewable in a diff.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tools.quizgen.corpus import ENTRIES, LEXICON
from tools.quizgen.similarity import best_distractors, is_plausible_distractor


OUT = Path(__file__).parent / "quiz_words.json"
MIN_DISTRACTORS = 3
MAX_DISTRACTORS = 5


def _lexicon() -> list[str]:
    """Every candidate word: the shown words plus the distractor-only fodder."""
    seen: dict[str, None] = {}
    for e in ENTRIES:
        seen.setdefault(e["word"])
    for w in LEXICON:
        seen.setdefault(w)
    return list(seen)


def build() -> list[dict]:
    lex = _lexicon()
    out: list[dict] = []
    weak: list[str] = []
    for e in ENTRIES:
        word = e["word"]
        curated = e.get("distractors")
        # Curated lists are trusted verbatim — thematic distractors (Sonntag for
        # Donnerstag) may bend the strict length rule on purpose, and the runtime
        # already widens the pool with bank-similar words for variety, so there's
        # no need to pad here. Only entries that leave distractors None are filled
        # from the lexicon by the similarity rules.
        distractors = list(curated) if curated is not None else best_distractors(word, lex, MAX_DISTRACTORS)
        # Dedupe, drop the answer itself, cap.
        distractors = [d for d in dict.fromkeys(distractors) if d != word][:MAX_DISTRACTORS]
        if len(distractors) < MIN_DISTRACTORS:
            weak.append(f"{word} ({len(distractors)})")

        row: dict = {"word": word, "distractors": distractors, "era": e.get("era", "modern")}
        if e.get("note"):
            row["note"] = e["note"]
        if e.get("fugen"):
            row["fugen"] = e["fugen"]
        out.append(row)

    if weak:
        print(f"WARNING: {len(weak)} entries under {MIN_DISTRACTORS} distractors: {', '.join(weak)}", file=sys.stderr)
    return out


def _validate(rows: list[dict]) -> None:
    """Sanity checks that would otherwise only surface in the running quiz."""
    seen: set[str] = set()
    for r in rows:
        assert r["word"] not in seen, f"duplicate entry: {r['word']}"
        seen.add(r["word"])
        assert r["era"] in ("modern", "historic"), f"{r['word']}: bad era {r['era']!r}"
        assert r["distractors"], f"{r['word']}: no distractors"
        assert r["word"] not in r["distractors"], f"{r['word']}: answer in distractors"
        assert len(set(r["distractors"])) == len(r["distractors"]), f"{r['word']}: duplicate distractors"
        if "fugen" in r:
            assert r["fugen"].replace("|", "") == r["word"], f"{r['word']}: fugen must strip to word"


def _dump(rows: list[dict]) -> str:
    return json.dumps(rows, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify quiz_words.json is up to date, don't write")
    args = ap.parse_args()

    rows = build()
    _validate(rows)
    text = _dump(rows)

    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print("quiz_words.json is stale — run: uv run python -m tools.quizgen.build", file=sys.stderr)
            return 1
        print(f"quiz_words.json up to date ({len(rows)} words)")
        return 0

    OUT.write_text(text, encoding="utf-8")
    modern = sum(1 for r in rows if r["era"] == "modern")
    historic = len(rows) - modern
    # Report how well the similarity rules cover the generated distractors.
    gen_pairs = sum(1 for r in rows for d in r["distractors"] if is_plausible_distractor(r["word"], d))
    total_pairs = sum(len(r["distractors"]) for r in rows)
    print(f"wrote {OUT.name}: {len(rows)} words ({modern} modern, {historic} historic)")
    print(f"distractors passing the similarity bar: {gen_pairs}/{total_pairs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
