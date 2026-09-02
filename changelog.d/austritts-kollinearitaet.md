### Added

- **The exit-side collinearity rule, opt-in and measured — and rejected.**
  `compose_word(exit_trim=True)` cuts a sawtooth exit's chart stub back to the
  point where the straight to the unchanged coupling point continues the
  letter's own direction, centerline and silhouette both, and draws the join as
  that straight — the A-side mirror of `entry_trim`, the class rule the audit
  of 2026-09-02 asked for. The autopsy behind it is sharper than the finding
  was: the chart stub ends in a finishing flick (`e` turns from 45° to 9° over
  its last 0.05 xh, `i` turns downward), while the composer reads its departure
  over 0.12 xh and aims the connector there. The cut walks back no further than
  the foot turn, so the letter body is never touched, and it happens after the
  next glyph has been placed, so the placement stays byte-identical — the
  experimental control the pre-registration demanded. It does what it promised:
  the class seam angle goes from +12.52° to −1.39°, joins kinking past 10° from
  103 to 15, `bench_loss` 0.109255 → 0.108720, pairs untouched. It is still not
  adopted: `dconn` against the hand's dissected joins falls in only 20% of them
  (51% once the length artifact is taken out, still short of the 60% gate), so
  the switch defaults to off, the golden fixture is untouched, and the numbers,
  the post-hoc narrow-class arm and four named rescue paths are recorded in
  `qualitaetsmetrik.md` §14 „Übergänge J4/J4b" (#NNN).
- **`--exit-trim` on the word bench**, with `--exit-trim-min-kink` to narrow the
  rule to the joins that actually kink. A candidate arm's own measurement, never
  the headline — the same discipline `--overrides` and `--laufform` carry, and
  the run says so in its header (#NNN).
