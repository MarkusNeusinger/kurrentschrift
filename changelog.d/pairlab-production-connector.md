### Changed

- **pairlab measures the production Übergang again, not a copy of it.** The
  join dissection used to regenerate connectors with a hand-written mirror of
  `core.compose`'s join block that had been frozen since 2026-07-11, while the
  real `_connector_centerline` was rebuilt three times and grew garland, fork
  and Absatz branches. It now records `core.compose`'s own call during the
  composition and replays it at the independently fitted placement
  (`tools/pairlab/prodconn.py`), so no join grammar lives under `tools/` at
  all and the next rebuild in `core/` reaches the measurement on its next run.
  On the frozen Sütterlin sets the two curves differed on 89 of 248 joins
  (median 0.056 xh, capital-restart joins 1.04 xh), and the production
  connector sits closer to the plate — `gen_chamfer` median 0.0434 → 0.0392.
  Report-only: no headline, no ruler and no composed geometry moves, and the
  chain solver keeps its frozen initialisation on purpose.

### Added

- **`dspan`, an extension-normalized shape distance for letter joins.**
  `dconn` start-aligns the composed and the measured connector, so a rule that
  moves the boundary between letter and connector — the exit trim measured and
  rejected in the J4 arm — makes the composed curve longer at the head and
  reads as a shape change; two thirds of that arm's failing number were this
  artifact. `tools/pairlab/spanmeas.py` compares only the stretch both curves
  share, clipped back from their common arrival, which removes the artifact by
  construction instead of by a threshold nobody could place: the arm's move
  drops from +0.0665 to +0.0040 xh and its fall share rises from 20 % to 46 %.
  A new sensor beside the frozen ruler, never an edit of it.
