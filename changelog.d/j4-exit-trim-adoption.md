### Changed

- **The exit trim is the production default, and the golden fixture is
  re-baked to say so.** Author decision A37 of 2026-09-06 adopts `exit_trim`
  after the blind word round went 34 : 2 for it; `compose_word` now applies it
  unless a caller says otherwise, so every `/write/word` answer moves (the edge
  cache holds the old one for up to 24 h, as after the LF11 write). Measured on
  the unchanged frozen root, so the two numbers are paired: words 0.108444 →
  0.109026, pairs byte-identical, seam departure +7.59° → −0.70° with the
  absolute median falling 12.67 → 2.30, and `gleichzug_doublings` unmoved at
  14. The word ruler rises knowingly — the round showed its whole cost sits in
  the class where the eye votes 26 : 2 for the trim. `EXIT_TRIM_MIN_KINK_DEG`
  stays 0.0: the same round measured the narrowing, and while it does enrich
  the strong-seam class from 10° on, it never separates the two — the only rung
  that buys ruler back gives the seam repair up to do it.
- **The measurement tools follow the shipped default instead of overriding
  it.** `wordbench.run`, `humanbench.wordarm` and `pairlab.spanmeas` trade
  `--exit-trim` for `--no-exit-trim`, which is now the pre-adoption base and a
  candidate arm like any other — a bench run with no flags measures what
  production writes, which is the whole point of the headline. `wordarm` reads
  the default off the composer's signature, so an arm file that says nothing
  records the boolean it actually drew with, and its `join_rules` block gained
  `exit_trim` beside the two J5 switches.

- **The continuity sensor, frozen the same day and knowing nothing about this
  arm, agrees with the eye.** S2 was built, frozen and accepted against the
  UNTRIMMED composition, and none of its constants comes from this round. On
  the same root against the same base, the trim takes `cont_kink_total` from
  402 to 337 — 65 discontinuity events fewer — with the survivors flatter
  (`cont_kink_deg_median` 19.75 → 18.52), less wobble (2.707 → 2.482) and the
  sagitta measured AROUND THE GENERATED JOINS more than halved
  (`cont_bow_join_median` 0.0091 → 0.0042). It is a report column and no gate,
  so it decided nothing here; it is simply the place where two instruments that
  know nothing of each other say the same thing. The corollary is booked with
  it: the S2 entry's own numbers now describe the composition BEFORE the trim,
  where they are correctly filed and stay untouched.

### Fixed

- **The join dissection replays the trim instead of quietly measuring the
  untrimmed curve.** `pairlab.prodconn` had named this exactly: the trim
  replaces the generator's return value inside `compose_word`, "harmless while
  the switch is off — should it ever become the default, this function has to
  grow the same post-processing or the dissection will quietly measure the
  wrong curve". It now does. The recorder additionally captures
  `_exit_trim_index` for every join the rule is eligible on — with or without
  a cut, because a join production did not trim can become trimmable once the
  letters move — plus `_cut_exit_stub`, which runs only when the curve was
  really replaced and so distinguishes "no cut" from "narrowed away". `replay`
  shifts that stub with its letter and calls the same core functions again, so
  the cut is RE-DECIDED at the fitted placement rather than frozen at the
  composer's. Two limits are named in the docstring: the eligibility guards
  stay production's, like every other recorded flag, and a composition
  recorded under the min-kink narrowing is not silently widened.
