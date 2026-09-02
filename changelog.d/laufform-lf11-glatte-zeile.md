### Added

- **A sensor for the wobble no ruler was looking at.** `zigzag_rate` in
  `core/laufform.py` counts how often a rendered Laufform row reverses its
  curvature per x-height, and the Laufform inventory prints it beside every
  row's own chart form. The stored running forms reverse 6.9 times per
  x-height against the chart's 0.2, which is visible in every bound word —
  and it stayed invisible to every green number because the word bench and
  the ink follower both resample it away before they score. A defect no
  instrument can see is a defect nobody can fix, so the instrument came
  first (#NNN).
- **A median that cannot carry that wobble.** `spline_basis_median` in
  `core/aggregate.py` projects each occurrence onto a clamped cubic B-spline
  over the chart row's own arc length — the chart's corners entering as
  knots so a corner stays a corner — takes the median over the control
  points, and evaluates back onto the original anchors. The per-anchor
  median it stands beside medians all 120 anchors independently, so nothing
  couples a neighbour and the estimator's own noise reaches the page.
  `tools/laufform/smoothrow.py` builds candidate maps from it without
  touching the database (#NNN).

### Changed

- **The LF11 arm is pre-registered, measured and left unwritten.**
  `docs/reference/qualitaetsmetrik.md` §14 carries the pre-registration
  written before the first number and the result of the ladder that
  followed: at a knot spacing of 0.16 x-heights the candidate closes 96.7 %
  of the smoothness gap to the chart, moves the frozen word and pair rulers
  by −0.000037 and −0.000235, loses no crossing in any of the 63 words, and
  repairs all five row gates the fresh per-anchor median breaks. It is a
  candidate and nothing more: adoption waits on the humanbench word round
  and the author's go, because a ruler that cannot see the defect cannot
  approve its removal either (#NNN).
