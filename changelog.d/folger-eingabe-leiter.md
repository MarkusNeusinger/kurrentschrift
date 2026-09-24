### Added

- **The own-hand follower input ladder, booked.** A new journal entry,
  `messjournal.md` §14 „Folger-Eingabe-Leiter `sep24`", records the
  exploratory round of 2026-09-24. It measured the strip follower's three
  input stages on seven boxes of the author's first sheet, each rung
  against its predecessor under a pre-registered rule. Label masking and
  plate-scale resampling did not beat their predecessors. The anisotropic
  seed registration lifted the own hand in every box (median coverage
  0.736 → 0.959) but failed the plate guard (dev-19 AIoU median
  0.7929 → 0.7895), so it is out. The entry also books three things
  beside the verdicts. A blind comparison ran, 7 : 0 for the seed
  registration, but it was not the registered pass. The diagnosis had
  misread the Absetzer sensor: the follower never counts a lift the seed
  sanctions, so the proposed Soll correction would have double-counted
  the dots, and it was dropped. And the pre-registration carried no
  pre-arm hash; the next one is therefore committed before any arm runs.
  The proposal `eigenhand-erfassung.md` records the author's decision
  that the strip follower may adapt its input while its decoder stays
  A45, that every stage has to leave the plate path standing, and that
  label masking is the default. `tintenfolger.md` §7.9 names two rescue
  paths: the seed registration on printed-sheet input only (R-gate), and
  its two scales as separate rungs (R-split). The glossary gains the
  Platten-Wächter, the plate guard every such stage answers to.
- **The next follower round, pre-registered before any arm exists.** The
  entry „Stufe 3 gezielt: R-gate + R-split `sep24b`" is committed on its
  own, and the last commit that changes it is the pre-arm hash the previous
  round lacked. Because the author squash-merges, the merge commit on
  `main` is the reference of record, named in a dated addendum after the
  merge, and the arm code comes in a PR of its own. It registers a
  three-rung ladder: label masking plus resampling as the base, then the
  seed's x-scale alone, then the vertical scale and baseline on top. A
  passing rung nominates resampling and itself as one package, since the
  seed registration was measured at the plate's scale. The seed
  registration runs only on a case cut from a printed sheet, so the plate
  path stays byte-identical by construction. Each stage-3 rung is still
  reported ungated on the plate, through the scratch runner rather than a
  repo switch, so the gate hides nothing. The arm commit turns today's
  boolean `--register-seed` into `--register-seed {k,ky}`. The metrics and
  the decision rule are unchanged. A jitter and short-chord sensor, built
  on the frozen continuity arithmetic, is reported and never decides. The
  confirmation runs on unseen boxes from S0182 on, and only on strips the
  hold-out draw puts into practice; the draw comes first. The author's
  seeded blind pass comes before any adoption, and adoption stays the
  author's decision.
