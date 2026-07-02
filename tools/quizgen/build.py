"""Build the quiz word seed from the curated corpus.

Reads ``corpus.py``, pins the best-scoring bank word for any entry that left
``distractors`` as ``None``, validates the rows, and writes ``quiz_words.json``
— the single source the Alembic seed migrations load into the ``quiz_words``
table.

The stored ``distractors`` are PINNED anchors, usually exactly one per word:
the hand-curated best misread, always offered by the quiz. The remaining
options are drawn at runtime from the whole bank by the similarity rules with
weighted randomness (see ``buildWordChoices`` in ``useQuizEngine.ts``), so the
choices change from round to round.

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

from tools.quizgen.corpus import ENTRIES
from tools.quizgen.similarity import best_distractors, is_plausible_distractor


OUT = Path(__file__).parent / "quiz_words.json"
# Pinned anchors per word: at least one, and only a few even for thematic sets —
# variety comes from the runtime draw, not from long stored lists.
MIN_DISTRACTORS = 1
MAX_DISTRACTORS = 3


def build() -> list[dict]:
    bank = [e["word"] for e in ENTRIES]
    out: list[dict] = []
    weak: list[str] = []
    for e in ENTRIES:
        word = e["word"]
        curated = e.get("distractors")
        # Curated pins are trusted verbatim — a thematic anchor (Sonntag for
        # Donnerstag) may bend the similarity rules on purpose. Only entries
        # that leave distractors None get the best-scoring bank word pinned.
        distractors = list(curated) if curated is not None else best_distractors(word, bank, MIN_DISTRACTORS)
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
        assert r["distractors"], f"{r['word']}: no pinned distractor"
        assert r["word"] not in r["distractors"], f"{r['word']}: answer in distractors"
        assert len(set(r["distractors"])) == len(r["distractors"]), f"{r['word']}: duplicate distractors"
        # Every dated word must explain itself in the answer reveal.
        assert r["era"] != "historic" or r.get("note"), f"{r['word']}: historic entry without a note"
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
    # Report how many words the runtime similarity draw can serve from the bank
    # itself (≥2 plausible in-bank candidates beyond the pinned anchor).
    bank = [r["word"] for r in rows]
    rich = sum(
        1
        for r in rows
        if sum(1 for w in bank if w not in (r["word"], *r["distractors"]) and is_plausible_distractor(r["word"], w))
        >= 2
    )
    print(f"wrote {OUT.name}: {len(rows)} words ({modern} modern, {historic} historic)")
    print(f"words with >=2 in-bank runtime candidates beyond the pin: {rich}/{len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
