### Changed

- **The running forms of the 1922 hand are smooth now.** All 22 Laufform rows
  of `suetterlin-1922` were rewritten as spline-basis medians (LF11, knot
  spacing 0.16 x-heights) after the first humanbench word round decided what no
  ruler could: on the 48 screens of the repaired page the author chose the
  candidate 36 times against 1. The rows had been wandering left-right-left 2 to
  11 times per x-height where the chart rows they came from wander zero times,
  and every bound word rendered one — the single largest difference between
  "written" and "computed" in the product. The frozen word bench moves from
  0.109255 to 0.109218 and the pairs from 0.148433 to 0.148198, which is exactly
  what the dry measurement predicted, down to every component and diagnostic
  line. Public `/write/word` responses carry up to 24 h of edge cache, so the
  change appears there as that expires; no purge (#497).
- **The measurement journal records the round it could not have decided
  alone.** `docs/reference/qualitaetsmetrik.md` §14 carries the adoption entry —
  the round, the instrument defect that split it, both readings of the verdict
  side by side, the author's post-hoc exclusion decision, and the write with its
  snapshot timestamp and read-back — plus the re-baseline row in the headline
  ledger with the new root digests. `tintenfolger.md` moves LF11 from open to
  adopted (#497).

### Fixed

- **A judging page that filled its own loops was quietly pulling every verdict
  toward "no difference".** The silhouette of a pen stroke is an outer ring plus
  the rings of its interior, and the page filled each ring separately, so every
  loop ran solid — which erases exactly the features a reader is asked to judge.
  The tie share was 48 % on the affected screens against 22.9 % on the repaired
  ones. `menschliche-bewertung.md` gains it as construction rule 3.6b next to
  the failure it came from, with the rule that a display fixed mid-round splits
  the round at the timestamp and both readings get reported (#497).
