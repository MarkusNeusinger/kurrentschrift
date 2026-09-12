### Added

- **The Wellen-Basis moves from a private branch into the repo as a kept
  building block, off by default.** `build_chain_problem(wave_spacing=…)`
  re-parametrises the chain solver's free per-anchor deltas as
  `deltas = B @ c`, a clamped cubic B-spline design matrix over the seed's
  arc length, one block per pen stroke (continuous across letter seams, cut
  only at letter-internal stroke starts). Only `unpack`/`_pack` change, so
  every energy term, the retrace guard, the reports and the analytic
  gradient (the exact chain rule `Bᵀg`) keep reading per anchor; a
  one-anchor zigzag simply has no representation in the basis, so no term
  has to price it. The follower carries it as `--wave-spacing` (plus
  `--wave-arc seed|current` for the abscissa and `--wave-report` for the
  field-coherence numbers alone); at `wave_spacing = 0` geometry, bounds,
  gradient and the solve itself stay byte-identical to the follower before
  this PR — only the serialised `weights` blob every artefact carries gains
  the three new fields (`wave_spacing`, `wave_arc`, `wave_report`).
  Measured (§14 "Welle `sep11`", `docs/proposals/tintenfolger.md` §7.9):
  13 rows, zigzags 49 → 11 (−78 %), paper distance −54 %, dev-19 0.041403,
  15 : 4 against the base arm — but ink reversals rise 162 → 200 (+23 %)
  and the mandatory anchor `das` worsens by +0.0782: a coherent field
  cannot repair a misplaced affine seed pointwise. The author's own words
  are the reason it stays in the tree rather than in a branch: "die anderen
  versuche verfahren aber richtig behalten vielleicht brauchen wir die mal
  noch oder nehmen uns davon noch bausteine zum optimieren des tintenpfad"
  (2026-09-12) — kept as a building block for the Tintenpfad work, not
  adopted as a default. Glossary: Wellen-Basis (extended with the switches
  and the repo date).
