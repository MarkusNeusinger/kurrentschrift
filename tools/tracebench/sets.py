"""The frozen development split of the trace bench.

On 2026-08-13 the author re-traced ten Abb.-19 words by hand in the word editor
(Werkbank W3) and stored them as `provenance: "authored"` — the reference set an
automatic tracer is graded against, because a candidate cannot be its own
measure (`docs/research/bildsynthese-und-stiftbahn.md` §6 Nachtrag).

Those ten ids are frozen here, and the rule is APPEND-NEVER: every word traced
after this list was written is CONFIRMATION material by definition (the
held-out reserve of the humanbench method) and never moves into the dev split,
no matter how useful it would be. Without that line a "the follower improved by
25 %" is unfalsifiable — a gain measured on the words a follower was tuned
against is fitting, not progress.

Why a committed constant, and not the obvious alternatives:

* not the fixture manifest — the artifact is regenerated on every re-export, so
  the split would silently follow whatever happens to be traced today;
* not "everything authored" — the same drift with an extra step, since the
  author keeps tracing (that is the point of the confirmation set);
* not a timestamp cutoff — `word_instances` rows carry no immutable authoring
  date the bench could trust, and a re-save would move a word between splits.

The split's blind spots are named rather than papered over: no umlaut word, no
long ſ, exactly one capital. Those are precisely what the confirmation set is
being traced for (§1).
"""

from __future__ import annotations


TRACEBENCH_DEV_IDS = frozenset({"die", "laden", "linken", "mit", "muß", "und", "unter", "Wer", "will", "zwei"})


__all__ = ["TRACEBENCH_DEV_IDS"]
