"""The frozen development split of the trace bench.

On 2026-08-13 the author re-traced ten Abb.-19 words by hand in the word editor
(Werkbank W3) and stored them as `provenance: "authored"` — the reference set an
automatic tracer is graded against, because a candidate cannot be its own
measure (`docs/research/bildsynthese-und-stiftbahn.md` §6 Nachtrag).

The ids below are the DEV side of the stratified split pre-registered in
`docs/proposals/tintenfolger.md` §2.5 (2026-08-16, performance-blind: drawn
from the frozen slot contents before any of the newly traced words was ever
benched): the ten burned words above plus `Galoppieren` and `das`, and — per
the §2.5 repetition rule (repeat occurrences split as a WORD, never across
the boundary) — every repeat occurrence of a dev word (`die-2`, `mit-2`,
`muß-2/-3`, `und-2/-3/-4`): 19 specimen rows in total. Activated 2026-08-17
as a declared ruler change with a dated re-baseline of all standing routes
(messjournal.md §14), on the owner's in-session go — the dev words were
fully authored at that point, the confirmation sets were not yet.

The rule remains APPEND-NEVER: every word outside this list is CONFIRMATION
material by definition (the held-out reserve of the humanbench method) and
never moves into the dev split, no matter how useful it would be. Without that
line a "the follower improved by 25 %" is unfalsifiable — a gain measured on
the words a follower was tuned against is fitting, not progress.

Why a committed constant, and not the obvious alternatives:

* not the fixture manifest — the artifact is regenerated on every re-export, so
  the split would silently follow whatever happens to be traced today;
* not "everything authored" — the same drift with an extra step, since the
  author keeps tracing (that is the point of the confirmation set);
* not a timestamp cutoff — `word_instances` rows carry no immutable authoring
  date the bench could trust, and a re-save would move a word between splits.

The split's remaining blind spots are named rather than papered over: no umlaut
word and no long ſ (the capital gap closed with `Galoppieren`). Those are
precisely what the confirmation sets hold (§2.5).
"""

from __future__ import annotations


TRACEBENCH_DEV_IDS = frozenset(
    {
        # the ten burned words of 2026-08-13 (§2.4)
        "die",
        "laden",
        "linken",
        "mit",
        "muß",
        "und",
        "unter",
        "Wer",
        "will",
        "zwei",
        # the §2.5 extension (owner decision 2026-08-16, activated 2026-08-17)
        "Galoppieren",
        "das",
        # repeat occurrences of dev words — same split side as their word (§2.5)
        "die-2",
        "mit-2",
        "muß-2",
        "muß-3",
        "und-2",
        "und-3",
        "und-4",
    }
)


__all__ = ["TRACEBENCH_DEV_IDS"]
