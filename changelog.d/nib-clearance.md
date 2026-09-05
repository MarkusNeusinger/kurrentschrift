### Added

- **The composer can read its ink clearances in nib radii — measured, and
  deliberately left switched off.** The placement clearances of
  `core/compose.py` are stated in x-heights but were every one of them
  calibrated at the chart-pooled Gleichzug pen (half-width 0.07251), so a
  heavier pen fills the same skeleton gap with more ink and the letters
  crowd. `compose_word(nib_clearance=True)` reads them in nib radii instead,
  floored at the calibrated value — and it stays off, because the measurement
  says it does not do what it was licensed for: at the plates' own pen
  (half 0.097) the frozen word set's Gleichzug doublings stay at 21, and
  coverage rises. The reason is geometric rather than numeric, which is the
  finding worth keeping: eight of the nine doublings a heavy pen opens are
  the covering join lying alongside the very body it lands on, and a
  placement distance moves the join and that body together — the ninth is an
  intended arm fusion, body against body, which sits below every clearance by
  design. The switch survives because the rule
  is the right shape for the day the delivered nib changes; below the
  calibration pen it is a strict no-op, so the golden fixture and both bench
  headlines are byte-identical. `tools/humanbench/wordarm.py` gains the
  matching `--nib-clearance`. Full pre-registration, gates and the residual —
  nine letterforms whose counters close outright under the heavier pen, which
  no placement rule can reach — in `docs/reference/messjournal.md` §14
  „Ink-Clearance an die Feder `sep05`".
