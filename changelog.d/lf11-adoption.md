### Changed

- **The running forms of the 1922 hand are smooth now.** All 22 Laufform rows
  of `suetterlin-1922` were rewritten as spline-basis medians (LF11, knot
  spacing 0.16 x-heights) on the author's decision, informed by the first
  humanbench word round, which came out 40 judgements to 1 for the candidate and
  reliable on its repeat pairs. The round carries no formal verdict — the
  "no difference" share is 34.9 % against a pre-registered ceiling of 25 % — so
  the journal records an author decision rather than an instrument verdict.
  The rows had been reversing their curvature a
  median of 6.9 times per x-height against their chart rows' 0.2 — the worst of
  them, the `c`, 21.8 times — and every bound word rendered one, which made it
  the single largest difference between "written" and "computed" in the product.
  Across the 22 rows production serves, the mean rate falls from 8.570 to 0.627.
  The frozen word bench moves from
  0.109255 to 0.109218 and the pairs from 0.148433 to 0.148198, which is exactly
  what the dry measurement predicted, down to every component and diagnostic
  line. Public `/write/word` responses carry up to 24 h of edge cache, so the
  change appears there as that expires; no purge (#501).
- **The journal records a decision no number could have made, and says whose it
  was.** `docs/reference/qualitaetsmetrik.md` §14 carries the entry — the round,
  all three tallies side by side under the binding analysis plan, why none of
  them clears the tie bar, the unresolved question of whether a display fault
  reached any of the judgements, and the write with its snapshot timestamp and
  read-back — plus the re-baseline row in the headline ledger with the new root
  digests. `tintenfolger.md` marks LF11 adopted on the author's decision and
  opens the repeat round that would replace it with a real verdict (#501).

- **The judging method learned two rules from its first real round.**
  `menschliche-bewertung.md` gains construction rule 3.6b beside the loop-fill
  fault that #492 fixed: check a form with an interior before the first round,
  because filling a loop erases exactly the features the question asks about and
  pulls answers toward "no difference" rather than adding noise in both
  directions. And the part this PR's own first draft got wrong: a split round is
  a weaker round, its cleaned half is counted under the same plan (mirrored
  repeats never vote), and below six complete repeat pairs it is diagnostic
  rather than adoption-carrying (#501).
