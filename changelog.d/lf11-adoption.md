### Changed

- **The running forms of the 1922 hand are smooth now.** All 22 Laufform rows
  of `suetterlin-1922` were rewritten as spline-basis medians (LF11, knot
  spacing 0.16 x-heights) on the author's decision, informed by the first
  humanbench word round: 28 judgements to 1 for the candidate on the repaired
  page, 40 to 1 across the whole round. The round does not carry a formal
  verdict — a display fault split it, and the cleaned half misses the tie
  threshold by 0.6 points — so the journal records an author decision rather
  than an instrument verdict. The rows had been reversing their curvature a
  median of 6.9 times per x-height against their chart rows' 0.2 — the worst of
  them, the `c`, 21.8 times — and every bound word rendered one, which made it
  the single largest difference between "written" and "computed" in the product.
  Production now serves a median of 0.6. The frozen word bench moves from
  0.109255 to 0.109218 and the pairs from 0.148433 to 0.148198, which is exactly
  what the dry measurement predicted, down to every component and diagnostic
  line. Public `/write/word` responses carry up to 24 h of edge cache, so the
  change appears there as that expires; no purge (#501).
- **The measurement journal records the round it could not have decided
  alone.** `docs/reference/qualitaetsmetrik.md` §14 carries the adoption entry —
  the round, the instrument defect that split it, both readings of the verdict
  side by side, the author's post-hoc exclusion decision, and the write with its
  snapshot timestamp and read-back — plus the re-baseline row in the headline
  ledger with the new root digests. `tintenfolger.md` moves LF11 from open to
  adopted (#501).

### Fixed

- **A judging page that filled its own loops was quietly pulling every verdict
  toward "no difference".** The silhouette of a pen stroke is an outer ring plus
  the rings of its interior, and the page filled each ring separately, so every
  loop ran solid — which erases exactly the features a reader is asked to judge.
  The tie share was 50.0 % on the affected screens against 25.6 % on the repaired
  ones. `menschliche-bewertung.md` gains it as construction rule 3.6b next to
  the failure it came from — including the part the first draft of this PR got
  wrong: a split round is a weaker round, its cleaned half is counted under the
  same plan (mirrored repeats never vote), and below six complete repeat pairs
  it is diagnostic rather than adoption-carrying (#501).
