### Added

- **The loop-faithful running form, measured and left switched off.** An
  elementwise median over occurrences whose loops disagree — about where they
  sit and how big they are — returns a loop tighter than any of them, and a
  counter that closes is read as a different letter. `core/aggregate.py` gains
  `loop_ranges` (where the chart row closes a loop, read off the drawn spline
  and mapped back by arc length, because at a crossing the two strands are
  spatially adjacent) and `align_loops` / `loop_faithful_median`, which register
  every occurrence's loops onto the stack's own median place and size before the
  median is taken. Neither part can invent aperture: the median shift is zero and
  the median factor one by construction, so the result can never be wider than the
  evidence under it. Behind `LAUFFORM_LOOP_WINDOW`, default 0 — off, and off means
  byte-identical rows. Measured as arm LF13 and NOT adopted: two of five gates are
  red (aperture, ruler); the switch ships off. `tools/laufform/smoothrow.py` gains
  `--loop-window` to build the candidate cards.

- **The merge indicator, built and calibrated as a report column.** Where two pen
  strokes fuse around a tight counter, `skeletonize` hands the follower the axis
  of the fused blob instead of the pen's path. `(D0_skeleton − plate) / (2·w_pen)`
  reads 1.0 where the medial axis IS the pen path and falls where it is not; over
  the 202 measured counters it rises monotonically with counter width across six
  bands (0.609 → 0.878, the `S` alone at 0.970), which is the calibration its
  pre-registration demanded. It stays report-only — no aperture term reaches a fit
  loss before the sensor is frozen.

### Changed

- **The Laufform round now knows where its counters are actually lost.** Measured
  against the exact occurrence stack a row was derived from (the LF12 harvest
  re-derives all 18 stored rows byte-identically), the estimator costs 0.005–0.029
  xh of loop aperture, while the harvest ahead of it — dissecting a chain word fit
  into a centered 120-anchor occurrence — costs 0.016–0.057 xh. The diagnosis of
  2026-09-06 could only bound that step from outside; it is now attributed, and it
  redirects the next arm from the median to the dissection.
