"""Load the Lesart vocabulary into the shared database through the admin API.

The words: the igerman98 dictionary's forms (tools.lesarten.expand) ∪ the
project's own quiz bank (tools/quizgen/quiz_words.json — the historic layer
hunspell lacks: Muhme, Wittib, gehorsamst …), deduplicated; bank words are
flagged so the read ranks them first on a tie. The server computes every
bucket key itself (core.lesarten.lesart_key).

Generation-switched, like the Übergangsraum push: open a generation, post the
words in batches, commit — the live vocabulary changes in one step, the old
one is dropped. Idempotent: the content hash of the fold plus the sorted word
list is sent first, and a build that is already live is refused by the server
(409), which this tool reports as „nothing to do" — so a changed look-alike
table (`core.lesarten.LESART_KEY_VERSION`) forces a fresh load even when not a
single word moved.

    ADMIN_TOKEN=… uv run python -m tools.lesarten.sync            # build + push
    ADMIN_TOKEN=… uv run python -m tools.lesarten.sync --dry-run  # counts only
    ADMIN_TOKEN=… uv run python -m tools.lesarten.sync --api http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
from collections.abc import Iterable
from pathlib import Path

from core.lesarten import WORD_MAX, key_marker, key_signature
from tools.eigenhand.apiclient import admin_token, api_base, request_json
from tools.lesarten.expand import REPO_ROOT, load_forms


QUIZ_WORDS = REPO_ROOT / "tools" / "quizgen" / "quiz_words.json"
# The marker names the fold the words were bucketed with, so the live build says
# on its face which look-alike table it can still be searched by.
SOURCE_LABEL = f"igerman98/de_DE_frami@32b006a + quiz bank ({key_marker()})"
BATCH = 20_000


def bank_words(path: Path = QUIZ_WORDS) -> set[str]:
    """The quiz bank's clean words (the Fugen marker stripped)."""
    rows = json.loads(path.read_text(encoding="utf-8"))
    return {str(r["word"]).replace("|", "") for r in rows if r.get("word")}


def drop_overlong(words: Iterable[str]) -> tuple[list[str], list[str]]:
    """Split a word list at `WORD_MAX` into (kept, dropped), order preserved.

    The column is `String(64)`, so a longer word cannot be stored and the API
    refuses the whole batch that carries one — the first production load died
    on exactly that, at word 80 000-odd. Nothing of value is lost: the two
    forms the igerman98 expansion produces above the bound are administrative
    compounds of 67 characters
    (`Grundstücksverkehrsgenehmigungszuständigkeitsübertragungsverordnung`
    and its `-en` plural), and a reading is only ever asked for a guess of at
    most `MAX_TEXT_LEN` = 32 characters.
    """
    kept: list[str] = []
    dropped: list[str] = []
    for word in words:
        (dropped if len(word) > WORD_MAX else kept).append(word)
    return kept, dropped


def build() -> tuple[list[tuple[str, bool]], str]:
    """(sorted [word, bank] pairs, sha256 of the fold plus the sorted words).

    The hash covers what is actually pushed, so it changes with the cap — a
    build filtered differently is a different build. It covers the FOLD too
    (`core.lesarten.key_signature`), because the server refuses a build whose
    hash is already live: the same word list under a changed look-alike table
    would otherwise be rejected as „nothing to do" while every word the new
    pair re-buckets sat unfindable in the stored generation."""
    forms = load_forms()
    bank = bank_words()
    words, dropped = drop_overlong(sorted(forms | bank))
    if dropped:
        print(f"dropped {len(dropped):,} words longer than {WORD_MAX} characters (e.g. {dropped[0]!r})")
    pairs = [(w, w in bank) for w in words]
    digest = hashlib.sha256("\n".join([key_signature(), *words]).encode("utf-8")).hexdigest()
    return pairs, digest


def push(pairs: list[tuple[str, bool]], digest: str, api: str, token: str, batch: int = BATCH) -> None:
    body = {"source": SOURCE_LABEL, "sha256": digest}
    try:
        opened = request_json("POST", f"{api}/lesarten/dictionary/generations", token, body)
    except SystemExit as exc:
        # Match the server's words, not the status: a fold mismatch answers 409
        # too, and „nothing to do" would be exactly the wrong thing to print
        # when the API is still bucketing with the previous look-alike table.
        if "already live" in str(exc):
            print("this build is already live — nothing to do")
            return
        raise
    assert opened is not None
    gen = int(opened["generation"])
    print(f"generation {gen} opened; pushing {len(pairs):,} words in batches of {batch:,}")
    try:
        total = 0
        for i in range(0, len(pairs), batch):
            chunk = pairs[i : i + batch]
            started = time.monotonic()
            out = request_json("POST", f"{api}/lesarten/dictionary/generations/{gen}/forms", token, {"words": chunk})
            assert out is not None
            total = int(out["total"])
            # The per-batch second is what the first load lacked: it grew with
            # the rows already stored until the request outlived the edge.
            print(f"  {i + len(chunk):>9,} sent · {total:,} stored · {time.monotonic() - started:.2f} s")
        meta = request_json("POST", f"{api}/lesarten/dictionary/generations/{gen}/commit", token, body)
        assert meta is not None
        print(f"live: generation {gen}, {meta['forms']:,} forms, {meta['source']}")
    except (SystemExit, urllib.error.URLError, KeyboardInterrupt):
        # Leave nothing half-loaded behind; the next begin would drop it anyway.
        try:
            request_json("DELETE", f"{api}/lesarten/dictionary/generations/{gen}", token)
        finally:
            raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--api", help="API base (default: $EIGENHAND_API or production)")
    parser.add_argument("--token", help="admin token (default: $ADMIN_TOKEN)")
    parser.add_argument("--dry-run", action="store_true", help="build and print the counts, push nothing")
    parser.add_argument("--batch", type=int, default=BATCH)
    args = parser.parse_args(argv)

    pairs, digest = build()
    banked = sum(1 for _, b in pairs if b)
    print(f"{len(pairs):,} words ({banked:,} from the bank), sha256 {digest[:12]}…")
    if args.dry_run:
        return 0
    push(pairs, digest, api_base(args.api), admin_token(args.token), args.batch)
    return 0


if __name__ == "__main__":
    sys.exit(main())
