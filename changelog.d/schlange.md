### Added

- **Schlange — an elastic-curve (snake) follower kept as a building block,
  never wired in.** The author's own physics statement about the "Welle"
  round ("die anderen Versuche aber richtig behalten") applies here as much
  as to its sibling Hook: rather than the chain's per-anchor deltas, every
  welded pen run of a word evolves as a discrete snake in the
  coarse-to-fine EDT valley — a semi-implicit metric step
  `(I + ℓ⁴·D2ᵀD2)⁻¹` so neighbouring nodes move as one wave, arc-length
  reparametrisation with the ductus corners kept as breakpoints, a bending
  energy on the curve (free at the corner rows), the chain's own coverage
  pull capped and averaged per node, and the affine seed of iteration 17.
  Measured on the twelve loop words against TWO baselines, each arrow named
  with its own left side. Physics **against iteration 17** (18 · 162 · 29.87):
  paper reversals 18 → 0, ink reversals 162 → 78, Papier-Strecke
  29.87 → 4.47 xh — the best physics result of the round. Ruler **against the
  production base** (dev-19 0,045881): 0,045881 → 0,051445, 6 : 13 on three
  named classes — and against iteration 17 the same run reads
  0,044431 → 0,051445, 2 : 17, so the ruler is lost against either. An honest
  partial negative, kept for the mechanism rather than the artefact: the new
  `tools/pairlab/schlange.py` is a second, stand-alone follower beside
  `tools.pairlab.chain` — it borrows eleven private helpers by name from
  five modules (`tools.pairlab.chain` and `.follow` among them; a test
  pins every signature) but adds no switch to any of them, so the chain
  solve stays byte-identical by construction. No DB, no `core/` change, no
  fixture change. The numbers above were measured on the module as it stood
  before this PR's own review round fixed a real `seed_curve` corner-index
  off-by-one (a shared and a non-shared seam had their arc-length offsets
  swapped, moving a corner from its true arc length 80.0/90.0 to 100.0/70.0
  — wrong on almost every fixture word, not the untriggered edge case the
  fix's own commit message called it); the fixed module no longer
  reproduces them (`das` measures 600 vs. 625 stroke points pre- vs.
  post-fix) and re-measuring it is left to whoever next picks this building
  block up.
