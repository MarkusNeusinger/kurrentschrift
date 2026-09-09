### Added

- **The seed is measured as a chain arm for the first time, and it is an honest
  negative worth keeping.** Author decision A39 runs rescue path (1) of round 9:
  `--chain-seed grid` starts each letter's translation block where the bounded
  grid search finds that letter on the ink instead of at the composed placement
  — a start point, not a claim and not an objective, so the weights, the guard,
  the evidence and the ruler are byte for byte the ones the production chain
  runs. It fails: the standing aiou gate tears at `Wer` (−0.0187) and `das`
  (−0.0074), `cross_missing` goes 11 → 13, and the dtw p90 rises. It also heals
  exactly the word the judge called „richtig schlimm" — `unter` gains **+0.1072
  aiou** and loses all five of its paper reversals, because the base run is
  reverted to init there and the arm's is not — while damaging exactly the one
  he called good. Reference-free the Soll distance falls 85 → 74 and the paper
  reversals 49 → 42 (45 → 32 without `regieren`, the one word whose grid search
  ends AT the block bound, so seven of its slots start registered and one does
  not). The whole aiou spread turns out to be the structure guard rather than
  the ink: 28 of 63 words change their verdict, the ones moving to `revert-init`
  lose 0.0770 median and the ones leaving it gain 0.1034, while the 35 unchanged
  move ±0.0005. No default flips, no proposal goes to the author; the two
  conversions and the composer's e-width task are registered in
  `tintenfolger.md` §7.9. Pre-registration, measurement and the round-11 build
  are in `docs/reference/messjournal.md` §14 „Kette K-G Saat-Registrierung
  `sep09`".
- **`tools/pairlab/seedgap.py` — the seed-gap inventory, and it splits the
  defect the judge named into two halves with different cures.** Round 9 ended
  with the author asking why the same `e`→`r` pair reads well in `Wer` and
  „richtig schlimm" in `unter`/`regieren`, and the answer pointed at the SEED:
  the Kette starts from the composed word, and where that start sits on the
  wrong ink the solver settles there. The sensor measures, per letter slot, how
  far the chain's own seed anchors lie from the plate ink — once as the
  whole-letter translation the bounded grid search wants (**Saat-Versatz**, a
  placement error the solver's translation block can absorb) and once as the
  per-anchor distance that survives that translation (**Saat-Rest**, the
  composed letter's shape not being the hand's). Splitting them is the point:
  only the first half is reachable from the follower at all, and the second is
  the standing composer task „e-Breite" (`tintenfolger.md` §7.2), which moves
  `core/compose.py` and is therefore an author decision, not an arm.
- **`tools/tracebench/reversals.py` — the paper-reversal sensor, landmark-aware
  by construction.** The first count of the same defect was withdrawn on the
  author's objection because it counted the DUCTUS: `Galoppieren` led its table
  with 23 reversals, every one of them a real turning point inside the ink. This
  one counts a reversal only where the vertex lies in the PAPER, which is where
  the eye reads a zig-zag — the same lesson the Kringel catalogue taught, that a
  sensor without landmark awareness measures the ductus instead of the defect. A
  report bound to no gate, and its numbers are stable across the thinning
  threshold and both paper definitions rather than balanced on one.
- **`--window-xh` for a humanbench word round: show the place, don't hide it in
  the word.** Round 9 asked the judge to compare two centerlines over a whole
  word at 2× magnification and got 44 „no difference" out of 44 — a 0.05 xh
  needle is a few screen pixels there. The flag cuts the screen to an excerpt
  around the point where the two arms part worst (`arm_gap_site`, the midpoint
  of the worst-separated pair, so a mirrored repeat gets the same frame as its
  original) and trades context for resolution. Both panels still share ONE
  window and both arms are still drawn in full, so §8's blindness is untouched;
  the stamp carries `window_xh` either way, because a windowed round's numbers
  must never be pooled with a whole-word round's. Construction rule §3.4a in
  `docs/reference/menschliche-bewertung.md`.
