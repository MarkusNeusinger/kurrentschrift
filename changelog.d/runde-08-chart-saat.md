### Added

- **The blind word round on the chart-seeded Laufform card is judged, filed and
  booked as an honest negative.** Round 8 — 75 screens, the stored rows against
  the 15 rows a write would install, placement pinned — goes 20 : 13 to the
  base among the 33 decided screens (39.4 % against a ≥ 60 % threshold) at
  47.6 % ties (against ≤ 25 %). Both thresholds fail, so this is not the J4
  shape where only the tie bar broke: the direction points at the base too. The
  round itself carries the claim — ten of twelve mirrored repeats name the same
  ARM at six of twelve naming the same side — and its instrument is clean,
  with all six null controls called "no difference". Per class the
  pre-registered visibility claim does not hold: `zeile-stark` ties 54.2 % and
  `lineal-verlierer` 50.0 %, both of them the classes that were claimed to be
  visible, while the unclaimed `zeile-schwach` comes closest to a verdict at
  26.1 % ties and 52.9 % candidate. The write of the card does not happen; the
  chart seed stays the harvest default, which is what decision A38 actually
  settled.
- **The pre-registered fallback was run before anything was discarded, and it
  is exact rather than approximate.** Dropping `Z` touches only the three words
  that draw a `Z`, so the remaining 60 screens ARE the 14-row card byte for
  byte — and they move the verdict from 39.4 % / 47.6 % to 38.7 % / 48.3 %.
  `Z` carries a third of the RULER loss and is the least conspicuous row of the
  card to the eye (1 : 1 at one tie), which is the finding: the ruler's loss
  and the eye's verdict are not the same axis.
- **A per-row decomposition carries the asymmetry rule one step further**
  (`data/humanbench/runde-08-zeilen.json`). Attributing each judged word to the
  rows its composition actually uses — the same gate `compose_word` applies to
  an overlay — reproduces the round's own null-control set exactly, and then
  separates the card: `d` takes 10 of its 12 decided words (83.3 %) at 14.3 %
  ties, the only row above the class floor to clear both thresholds and the one
  the judge named unprompted; split by its `u` neighbour it is 10 : 0 without a
  single tie. Against it, `h` takes 0 of 8 and `n` 3 of 15. The two rows the
  word ruler rewards most — `p` at 3 : 0 better and `w` at 4 : 2 — are two the
  eye rejects outright, which prices `menschliche-bewertung.md` §9a row by row
  instead of leaving it a maxim. The rows overlap, so the table ranks them and
  adopts none; the `d` row is proposed as its own pre-registered arm on today's
  root, which needs the author's yes and its own dated entry.
- **The round's own artefacts are in the repo** (`data/humanbench/runde-08-*`):
  the result text, the narrow key with its suspicion class per screen, the
  analysis JSON, the per-row decomposition and a provenance stamp carrying both
  arm checksums, the frozen root the round was built against and the
  dirty-worktree flag of its build commit. The full key, the payload, the two
  arm files, the candidate card and the strata file stay out — the judgement is
  the one part of the chain that cannot be recomputed, so it is the part that
  is kept.
