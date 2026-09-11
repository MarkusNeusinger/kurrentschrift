### Added

- **Three measured arms of the Tintenpfad, each a reading of the ink or a
  rule of the decoder, all off by default.** The author asked to optimise
  the strand-decode follower and test whether it becomes the best method,
  under his standing condition that no point may move without its
  neighbours. `tip_read` walks every free run end along the strand and then
  along the ridge of the distance transform until the frozen ink mask ends —
  no fixed amount, the mask is the stop — so the Anstrich and Auslauf the
  thinning cut short are written to the tip (the four `und` rows lose their
  bare exit stroke). `rail=tentfit` with `edt_upsample` reads the ridge with
  a least-squares tent over ±2 px on a four-times finer raster of the same
  distance transform, cut by the mask's own adaptive threshold inside the
  mask's edge band; the pixel moves along its normal only, capped as before,
  and the raw kink median falls from 9.7° to 8.0° without a low-pass on the
  path. `ink_bridge_xh` turns a decoder lift into a chord only where the
  crop's grey across the straight gap reads faint ink below the paper level;
  a blank gap stays a lift (two of nine tested gaps qualify, `haben` and
  `schießen`, both inside the mask). Two further arms were built and measured
  as honest negatives and stay off: a stub filter that absorbs junction
  strands under 0.25 xh changes no stroke, and a double-ink evidence for the
  ß stem never fires because the plate's stems read one to one-and-a-third
  pen widths. A companion switch `spur_at_ends` keeps the thinning's fork
  spurs at strand ends and is measured inert on this plate. Every default
  run stays stroke-identical to the delivered Tintenpfad (only the new
  weight fields at their off values appear in the artefact); the numbers of
  the round stay on the progress page until a §14 entry books them.
