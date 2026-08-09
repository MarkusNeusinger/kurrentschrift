"""humanbench — human judgement passes over the fits, as self-contained pages.

The automated benches (``tools/glyphbench``, ``tools/wordbench``) score what a
metric can already see. This package produces the other half: a labelling pass
the author works through by eye, so a metric can be checked against human
judgement instead of against itself.

Two page modes, both emitted by ``tools/humanbench/page.py``:

* **single** — one fit per screen, judged into the six categories (plus the
  „Unsicher" modifier) with an optional spot marker.
* **paired** — two variants of the SAME occurrence side by side, judged as a
  two-way preference. Blind by construction: the page draws only geometry, so
  nothing in the emitted file says which side is the new one.

The page is a pure renderer: it never touches the database and never decides
which occurrences are shown. Building the payload — and keeping the key that
maps an item id back to its occurrence — is the builder's job, and that key
stays out of the page (and out of the repo, quellen-und-rechte.md §5).

``tools/humanbench/build.py`` is that builder, and the reason this is a package
rather than a scratchpad script: the first round produced the finding list the
current work plan rests on, and a second round assembled by hand would have
been a different instrument whose numbers could not be held against the first.
It therefore carries the safeguards a round costs a human to learn — the
proportional crop pad, the seeded shuffle WITHIN the severity bands, the
held-out reserve, the blind repeats, the pen lifts drawn as lifts — each next
to the failure it was added for, plus a provenance stamp naming the round, the
seed and the code commit the judged fits came from. Without that stamp a later
round has nothing to be compared against.

The paired mode is what the second round needs: "the problems are fewer now"
becomes a measurement rather than an impression only if the before and after
are judged blind, on one shared crop, in an order the seed decides and the key
alone records.

``tools/humanbench/analyse.py`` closes the loop: it parses the result text the
page emits and runs the evaluation in the order the analysis plan fixed BEFORE
the labels existed — reliability, occupancy, gate validation, coverage matrix,
place check, drift. It belongs next to the builder for the same reason the
builder exists: an evaluation written after seeing the labels can be reordered
until it says something, so the order has to be code. It reads numbers and
never derives them — the per-occurrence metrics come from a file the caller
supplies, which is also how the learned geometry stays out of this repo
(``docs/reference/quellen-und-rechte.md`` §5).
"""
