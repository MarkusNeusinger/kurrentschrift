### Added

- **Every measuring tool now says which fixture root it measured, and can be
  pinned to it.** Since #478 the word bench opened each run with
  `root: <name> exported_at=…` / `digest=<12 hex>` and refused to measure a
  base `--expect-root` did not name. The trace tools — the ones a campaign
  entry actually quotes — kept scoring silently against whatever root sat on
  disk. They carry the same sensor now: `tools.tracebench.run`, `.k0eval`,
  `.view` and `.excursions`, plus `tools.pairlab.follow`, `.spanmeas`,
  `.chainbench` and `tools.pairlab` itself, all through ONE implementation in
  the new `tools/wordbench/roots.py` rather than a copy each. The check runs
  before the first measurement, so a mismatch aborts naming both digests
  instead of producing a number against the wrong base; `tracebench.run --json`
  and `pairlab.follow --json` carry the full digest under `roots`, and a round
  passes the same prefix to every call it makes. The roots are gitignored, so
  an undeclared re-export left no other trace — the gap the audit of
  2026-09-02 could no longer reconstruct.
