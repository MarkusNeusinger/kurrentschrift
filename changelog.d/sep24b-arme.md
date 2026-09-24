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
