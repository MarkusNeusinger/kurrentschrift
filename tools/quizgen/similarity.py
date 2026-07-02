"""Distractor scoring for the quiz word generator — Python twin of the rules in
``app/src/sections/quiz/wordBank.ts`` (``similarity`` / ``isPlausibleDistractor``).

A good distractor is a *plausible misread* of the answer in the German cursive
hand, not an arbitrary different word: near-equal length, a shared start OR end
letter, and the remaining differences limited to the letter pairs that look
alike in Kurrent/Sütterlin. Keep this in sync with the TS helper — both encode
the same rule set so the generated bank and the runtime top-up agree.
"""

from __future__ import annotations


# Unordered letter pairs that look alike in the cursive hand.
CONFUSABLE: list[frozenset[str]] = [
    frozenset(p)
    for p in (
        ("e", "n"),
        ("n", "u"),
        ("u", "a"),
        ("n", "m"),
        ("m", "w"),
        ("h", "k"),
        ("h", "b"),
        ("b", "l"),
        ("k", "l"),
        ("f", "s"),
        ("f", "ſ"),
        ("c", "e"),
        ("r", "x"),
        ("g", "z"),
        ("i", "e"),
        ("t", "l"),
    )
]


def _is_confusable(a: str, b: str) -> bool:
    return frozenset((a, b)) in CONFUSABLE


def _is_capitalized(w: str) -> bool:
    """Initial-capital (a noun) vs. lowercase — a different reading target."""
    if not w:
        return False
    first = w[0]
    return first == first.upper() and first != first.lower()


def similarity(answer: str, candidate: str) -> int:
    """Heuristic distractor quality; higher = more confusable. 0 = unusable.

    Mirrors the TS ``similarity``: equal case pattern, length within ±1, a
    shared first or last letter, and per-position differences rewarded when
    they are cursive confusions and penalised when arbitrary.
    """
    if not answer or not candidate or answer == candidate:
        return 0
    if _is_capitalized(answer) != _is_capitalized(candidate):
        return 0
    a, b = list(answer), list(candidate)
    if abs(len(a) - len(b)) > 1:
        return 0

    score = 0
    if a[0].lower() == b[0].lower():
        score += 2
    if a[-1].lower() == b[-1].lower():
        score += 2
    if score == 0:  # must share a start or end letter
        return 0

    if len(a) == len(b):
        for x, y in zip(a, b, strict=True):
            xl, yl = x.lower(), y.lower()
            if xl == yl:
                continue
            score += 1 if _is_confusable(xl, yl) else -2
    else:
        score -= 1
    return score


def is_plausible_distractor(answer: str, candidate: str) -> bool:
    return similarity(answer, candidate) > 0


def best_distractors(answer: str, lexicon: list[str], count: int = 4) -> list[str]:
    """The ``count`` best-scoring plausible distractors for ``answer`` from a lexicon.

    Sorted by descending similarity, ties broken alphabetically for a stable,
    reproducible generator output (no RNG — the runtime does the sampling).
    """
    scored = [(similarity(answer, w), w) for w in lexicon if w != answer and is_plausible_distractor(answer, w)]
    scored.sort(key=lambda sw: (-sw[0], sw[1]))
    return [w for _, w in scored[:count]]
