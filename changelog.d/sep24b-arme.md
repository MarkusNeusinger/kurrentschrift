### Added

- **The sep24b ladder, stage (a): the seed's width carries the own-hand
  gain, its height does not.** A new journal entry (`messjournal.md` §14,
  „Stufe 3 gezielt `sep24b`, Stufe (a)") measures the pre-registered ladder
  on the seven boxes of the author's first sheet. The base is label masking
  plus plate scale. Scaling only the seed's x lifts coverage in 7 of 7 boxes
  (median 0.736 → 0.960). Adding the vertical scale and baseline on top
  gains nothing more (2 of 7, median change 0). Run ungated on the plate as
  a report, the x scale alone keeps the dev-19 AIoU median at 0.7929, while
  the vertical part costs it (0.7895). The plate guard holds by
  construction: the standard plate path is byte-identical before and after
  the arm commit, and the gate hands every plate case back unchanged. The
  round only nominates plate scale plus the x scale for the confirmation on
  unseen boxes, which waits for the next sheet; adoption stays the author's
  decision. A reboot had wiped the previous round's scratch record; the
  entry records how it was rebuilt and checked before any rung ran.
  `tintenfolger.md` §7.9 gains the rescue paths for the vertical part.

### Changed

- **The strip follower's seed registration comes in two sizes and only on
  printed-sheet input.** `tools.eigenhand.pfad --register-seed` was a
  switch; it now takes `k` or `ky`. `k` scales the seed's width alone,
  against the case's own x-height, and leaves the printed baseline and
  x-height where they are (`core.eigenhand.follower_input.register_seed_width`).
  `ky` is the full anisotropic registration the `sep24` ladder measured. The
  split lets a round tell which of the two scales carries a gain. Either
  way the stage runs only on a case cut from a Bogen strip (its `origin`
  starts with `eigenhand:`). Any other case, a plate word above all, comes
  back unchanged, and the reason is stored in `meta.input`. So the plate
  path stays byte-identical by construction rather than by a measurement
  the registration had failed. A default run stores the same row as before:
  with the stage off, `konfiguration.input.register_seed` still reads
  `false`.
