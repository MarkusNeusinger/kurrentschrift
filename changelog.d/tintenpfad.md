### Added

- **`tools.pairlab.tintenpfad`, the Tintenpfad — a strand-decode follower
  that follows the ink first and assigns the letters afterwards.** Stage 1
  builds STRANDS from the frozen skeleton after the ink evidence (spur
  pruning, smoothest-continuation pairing at every junction, a sub-pixel
  rail read off the distance transform along the normal); stage 2 decodes
  the affine-registered seed through them by a Viterbi — monotone rides,
  priced hairpins, jumps and paper boardings, a hysteresis against
  out-and-back jumps — and emits the strand pixels themselves as the pen
  path, Hermite-bridged at jumps and arc-length-uniform. Every constant is
  frozen in `TintenpfadWeights` and travels into the candidate;
  `--legacy-p5` reproduces the prototype's measured row; every sensor the
  judges asked for (unvisited ink, excursions by kind, truncation, kink and
  turn distributions, label agreement, displacement coherence) is written
  per word. Measurement layer only: `core/` untouched, the chain follower's
  default byte-identical (the It.17 recipe re-run matches
  `temp/coarse-sep10/affine/a1/cand.json` on every stroke of all 13 rows).
  No adoption and no §14 entry — the artefact under `temp/wellen-sep11/`
  is the author's to judge. Glossary: Strang · Strang-Dekodierung.
