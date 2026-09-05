### Added

- **Every measuring tool now says which fixture root it measured, and can be
  pinned to it.** Since #478 the word bench opened each run with
  `root: <name> exported_at=…` / `digest=<12 hex>` and refused to measure a
  base `--expect-root` did not name. The trace tools — the ones a campaign
  entry actually quotes — kept scoring silently against whatever root sat on
  disk. All thirteen entry points that read a fixture root carry the same sensor
  now: `tracebench.run`, `.k0eval`, `.view` and `.excursions`, plus `pairlab`
  itself and `follow`, `spanmeas`, `chainbench`, `bindab`, `gradlab`, `peaklab`,
  `landmarklab` and `harvest` — all through ONE implementation in the new
  `tools/wordbench/roots.py` rather than a copy each. The check runs before the
  first measurement, so a mismatch aborts naming both digests instead of
  producing a number against the wrong base; `tracebench.run --json` and
  `pairlab.follow --json` carry the full digest under `roots`, and a round
  passes the same prefix to every call it makes. The roots are gitignored, so
  an undeclared re-export left no other trace — the gap the audit of
  2026-09-02 could no longer reconstruct.

- **A stored baseline has to come from the same root, too.** Announcing the root
  pins the run, not what the run is compared against, and a `--compare` report
  from another export pairs happily and prints a cross-root delta that reads
  like a result. `wordbench.run --compare`, `tracebench.run --compare`,
  `tracebench.view --rows` and `pairlab.spanmeas --base` now read the stored
  file's own `roots` block and refuse a foreign base BEFORE scoring, so a run
  that cannot be paired never spends the minutes either. `spanmeas --json`
  therefore writes an object (`roots` beside `rows`) instead of a bare row list;
  the old shape is still read, with a warning that its base cannot be checked —
  the same degradation an archived report without `roots` gets everywhere else.
