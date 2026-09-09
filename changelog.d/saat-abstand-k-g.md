### Added

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
