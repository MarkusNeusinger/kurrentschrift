"""Lesarten — the readings a guessed word could have on the page.

A person with an old letter on the desk types what they believe a word says;
the site answers with the REAL words that would look the same in the German
cursive, ranked by how cheaply the two differ: swapping two documented
look-alikes (n ↔ u, e ↔ n, the long ſ ↔ f, …) is nearly free, anything else
is not a reading. Owner decision 2026-08-30: readings are existing words only
— a letter salad like „Mnhme" is not a Lesart.

The vocabulary lives in the shared database (`lesart_forms`, loaded from the
igerman98 dictionary ∪ the quiz bank by `tools.lesarten.sync`, see
data/corpora/igerman98/SOURCE.md); this module is the pure half both sides
share — the same `lesart_key` buckets the words at load time and finds the
bucket at query time, so a word can only ever be found by the key it was
stored under. That is why the fold carries a version (`LESART_KEY_VERSION`):
changing the look-alike table re-buckets the whole vocabulary, so the stored
generation has to be reloaded before the new pair can be found.

The look-alike table is the Python twin of `app/src/lib/lesarten.ts`
(LOOKALIKES); tests/test_lesarten_core.py pins the two together.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable


# Typed letter → the letters it can be read as. Lowercase pairs from the
# reading-trap catalogue (n/u, e/n, n/m, m/w, v/w, i/j, i/e, t/l, f/h, f/t,
# g/p, ſ/f as s ↔ f), umlaut ↔ base letter, the capital confusion clusters
# (L/K/R, N/M, B/V). Symmetric by construction (pinned by the tests).
LOOKALIKES: dict[str, tuple[str, ...]] = {
    "n": ("u", "e", "m"),
    "u": ("n", "ü"),
    "e": ("n", "i"),
    "m": ("n", "w"),
    "w": ("m", "v"),
    "v": ("w",),
    "i": ("e", "j"),
    "j": ("i",),
    "t": ("l", "f"),
    "l": ("t",),
    "f": ("s", "h", "t"),
    "h": ("f",),
    "s": ("f",),
    "g": ("p",),
    "p": ("g",),
    "a": ("ä",),
    "ä": ("a",),
    "o": ("ö",),
    "ö": ("o",),
    "ü": ("u",),
    "L": ("K", "R"),
    "K": ("L", "R"),
    "R": ("L", "K"),
    "N": ("M",),
    "M": ("N",),
    "B": ("V",),
    "V": ("B",),
}

# The fold's version. A word is only ever findable under the key it was stored
# with, so a changed table silently strands every word it re-buckets: after the
# g/p pair was added (v2, 2026-09-04) the stored p rows of a v1 generation sat
# in the g-less bucket the read no longer asks for. Bump it whenever LOOKALIKES
# changes — `key_signature` carries the bump into the build's content hash, and
# `key_marker` into its source label, so the vocabulary must be reloaded and a
# generation still bucketed by the old fold is visible in `GET /lesarten`.
LESART_KEY_VERSION = 2

# The longest reading the API answers for — the page caps its field there too.
MAX_TEXT_LEN = 32
DEFAULT_LIMIT = 8

# The longest word the vocabulary can hold: `LesartForm.word` is String(64),
# so anything longer cannot be stored at all. Nothing is lost by the cap — a
# reading is only ever offered for a guess of at most MAX_TEXT_LEN characters,
# and the handful of forms the igerman98 expansion produces above it are
# administrative compounds (67 characters and up). The loader
# (`tools.lesarten.sync`) drops them; the API refuses them.
WORD_MAX = 64


def _components() -> tuple[dict[str, str], dict[tuple[str, str], int]]:
    """Connected components of the look-alike graph → (letter → class
    representative, (a, b) → graph distance within a class)."""
    rep: dict[str, str] = {}
    dist: dict[tuple[str, str], int] = {}
    seen: set[str] = set()
    for start in LOOKALIKES:
        if start in seen:
            continue
        # BFS over the component, collecting every member.
        members: list[str] = []
        queue = deque([start])
        seen.add(start)
        while queue:
            cur = queue.popleft()
            members.append(cur)
            for nxt in LOOKALIKES.get(cur, ()):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        head = min(members)
        for m in members:
            rep[m] = head
        # Pairwise distances inside the component (tiny graphs).
        for src in members:
            d = {src: 0}
            q = deque([src])
            while q:
                cur = q.popleft()
                for nxt in LOOKALIKES.get(cur, ()):
                    if nxt not in d:
                        d[nxt] = d[cur] + 1
                        q.append(nxt)
            for dst, steps in d.items():
                dist[(src, dst)] = steps
    return rep, dist


_REP, _DIST = _components()


def lesart_key(text: str) -> str:
    """The bucket key: every letter replaced by its look-alike class. Two words
    share a key iff they have the same length and every position holds
    letters that can be read as one another (or the same letter)."""
    return "".join(_REP.get(ch, ch) for ch in text)


MARKER_PREFIX = "lesart-key/v"


def key_marker(version: int = LESART_KEY_VERSION) -> str:
    """The token `tools.lesarten.sync` stamps into a build's source label. The
    API compares it against the running code, so `GET /lesarten/dictionary`
    says whether the live vocabulary was bucketed by today's fold."""
    return f"{MARKER_PREFIX}{version}"


def fold_marker_in(source: str) -> str | None:
    """The fold marker a build's source label carries, or None when it names no
    fold at all (a label written before the version existed).

    Read token-wise, not as a substring: `lesart-key/v2` must not match the
    `lesart-key/v20` of a much later table. The loader writes the marker as its
    own parenthesised word, which is what makes that comparison exact."""
    for token in source.replace("(", " ").replace(")", " ").split():
        if token.startswith(MARKER_PREFIX):
            return token
    return None


def is_current_fold(source: str) -> bool:
    """Whether a build's source label was stamped by the fold this code uses."""
    return fold_marker_in(source) == key_marker()


def key_signature() -> str:
    """Everything `lesart_key` folds together, as one line: the version and the
    table behind it. The loader mixes this into the content hash of a build, so
    the same word list under a changed fold is a DIFFERENT build — the server
    cannot refuse it as already live, and a forgotten version bump changes the
    hash all the same."""
    table = ";".join(f"{a}>{''.join(sorted(tos))}" for a, tos in sorted(LOOKALIKES.items()))
    return f"{key_marker()} {table}"


def swap_cost(a: str, b: str) -> int | None:
    """Cost of reading letter `a` as `b`: 0 for the same letter, the graph
    distance for look-alikes (1 = a documented pair), None if unrelated."""
    if a == b:
        return 0
    return _DIST.get((a, b))


@dataclass(frozen=True)
class Swap:
    index: int
    from_: str  # the letter in the guess
    to: str  # the letter in the reading


@dataclass(frozen=True)
class Reading:
    word: str
    bank: bool  # from the project's own curated bank (quiz words), not the dictionary
    cost: int
    swaps: tuple[Swap, ...]


def rank_readings(guess: str, candidates: Iterable[tuple[str, bool]], limit: int = DEFAULT_LIMIT) -> list[Reading]:
    """Rank the bucket's words as readings of `guess`: cheapest first (the
    summed pair distance), the curated bank before the dictionary on a tie,
    then fewer differing letters, then alphabetical (every candidate already
    has the guess's length); the guess itself and anything that is not a pure
    look-alike variant are dropped."""
    out: list[Reading] = []
    for word, bank in candidates:
        if word == guess or len(word) != len(guess):
            continue
        swaps: list[Swap] = []
        cost = 0
        ok = True
        for i, (a, b) in enumerate(zip(guess, word, strict=True)):
            c = swap_cost(a, b)
            if c is None:
                ok = False
                break
            if c:
                cost += c
                swaps.append(Swap(i, a, b))
        if ok and swaps:
            out.append(Reading(word=word, bank=bank, cost=cost, swaps=tuple(swaps)))
    out.sort(key=lambda r: (r.cost, not r.bank, len(r.swaps), r.word))
    return out[:limit]
