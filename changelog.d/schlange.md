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
  Measured on the twelve loop words: paper reversals 18 → 0, ink reversals
  162 → 78, Papier-Strecke 29.87 → 4.47 xh against iteration 17 — the best
  physics result of the round — but the dev-19 ruler moved the other way
  (0,045881 → 0,051445, 6 : 13) on three named classes. An honest
  partial negative, kept for the mechanism rather than the artefact: the new
  `tools/pairlab/schlange.py` is a second, stand-alone follower beside
  `tools.pairlab.chain` — it borrows ten of the chain's and follower's
  private helpers by name (pinned by a test) but adds no switch to either,
  so the chain solve stays byte-identical by construction. No DB, no
  `core/` change, no fixture change.
