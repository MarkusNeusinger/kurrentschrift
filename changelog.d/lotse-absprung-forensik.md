### Added

- **A departure sensor for the Lotse route (`tools/inkpilot/forensics.py`).**
  It measures every emitted point of the follower's path against the inked
  BODY — the skeleton widened by its own `width_map`, so the question is
  "outside the ink", not "off the centreline" — and labels each departure
  with the mechanism that placed it there. Alongside it records
  `map_slack_xh`, the composed map's own distance from the ink at the same
  spot, which is what separates a departure the follower INHERITED from the
  composition from one it manufactured itself. The module mirrors
  `pilot_word` rather than putting a hook into it, so the follower stays
  untouched during a measurement round, and `assert_matches_pilot` holds the
  mirrored strokes against the real ones bit for bit on every run.

### Fixed

- **The Lotse route's "unexplained jump" was a transcription, not a
  measurement.** The route page carried `0.0585 → 0.0545` as an open
  question since `aug26`. The `aug20` artifacts still exist: no Lotse report
  of that round measures 0.0545, and the value is the dev-19 rank-9 word
  (`laden`) where the median is rank 10 (`will`, 0.058522). The only word
  that could have moved the median is provably unchanged between the two
  dates, so the jump never happened. Resolved on the route page and in the
  journal; the dated entry itself stays as written, only its reading
  changes.

- **The standing dev-19 numbers are marked as pre-`sep01`.** Scoring the
  untouched `aug20` candidate bytes against today's fixture root reproduces
  15 of 19 words to the last digit and moves four — the `sep01` word-rectangle
  repair showing through, because an old candidate carries its own
  registration and no longer shares a frame with a repaired reference. The
  route page now says so, and quotes the freshly measured Lotse figures for
  the current root.
