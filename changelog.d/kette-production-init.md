### Added

- **The chain solver can start on the connector production actually draws —
  and measuring it exposed a noise floor under the whole bench.**
  `tools/pairlab/chain.py` initialised every join from a hand-written mirror of
  the join block frozen on 2026-07-11, the one consumer the production-connector
  switch deliberately left alone because moving it shifts the starting basin of
  every chain fit. `--connector-init production` now replays the recorded
  `core.compose._connector_centerline` call instead
  (`tools/pairlab/prodconn.py`); `mirror` stays the default and the archaeology
  path. Arm K-F ran both over all 63 word specimens and was rejected — but the
  finding that outlived it is that on 23 of those specimens the two inits differ
  by at most 1.8e-15, pure last-bit arithmetic ordering, and nine of them still
  flip the structure guard's accept/reject verdict, with per-word ink swings from
  −0.030 to +0.080. The chain arms' ±0.003 gate therefore cannot decide a
  start-point change at all, which is why the next round measures that floor
  before any further init arm.

### Changed

- **The Kette's dev-19 numbers are re-baselined on today's fixture root.** The
  standing figures dated from 2026-08-26, three re-exports and the September
  rectangle repair ago, which the Lotse round had already shown makes numbers
  across that boundary incomparable. A fresh run of the unchanged v5 follower
  puts the Kette at dtw 0.045830 median · p90 0.094197 · aiou 0.7694 · soll
  distance 76, so both duel routes are finally measured on one root — the
  Kette still leads the Lotse (0.056080). The formulation did not move; the
  root did.
