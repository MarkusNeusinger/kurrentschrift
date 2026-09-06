### Added

- **The blind word round on the J4 exit trim is judged, filed and read class by
  class.** Round 5 — 75 screens, base against `exit_trim` with the placement
  pinned — goes 34 : 2 to the candidate among the 36 decided screens (94.4 %
  against a ≥ 60 % threshold), while the pre-registered tie threshold of ≤ 25 %
  fails at 42.9 %. Per class the contradiction dissolves: `naht-stark` meets
  BOTH thresholds (26 : 2, 9.7 % ties), `naht-schwach` runs 8 : 0 for the
  candidate at 72.4 % ties — the class the pre-registration itself had
  described as one where a difference is unlikely to be visible. The instrument
  is clean where it can be checked: the three untouched control words are
  called "no difference" three times out of three, and ten of twelve mirrored
  repeats name the same ARM at only four of twelve naming the same side.
  `adopt: false` stands as the tool reported it; flipping the switch is a
  rendering-affecting change and therefore the author's call, exactly as the
  LF11 round was.
- **The round's own artefacts are in the repo** (`data/humanbench/runde-05-*`):
  the result text, the narrow key with its suspicion class per screen, the
  analysis JSON and a provenance stamp carrying both arm checksums, the root
  export it was built against and the dirty-worktree flag of its build commit.
  The full key, the payload, the two arm files and the strata file with its
  per-word displacements stay out — the judgement is the one part of the chain
  that cannot be recomputed, so it is the part that is kept.

### Changed

- **The word ruler and the eye are measurably opposed on this arm, and the
  entry says so with the decomposition.** Re-measured on today's frozen sep05
  root, the trim costs +0.000581 on words, leaves the pairs byte-identical and
  drops the seam departure from +7.59° to −0.70° (absolute median 12.67 →
  2.30). The whole ruler loss sits in `naht-stark` (+0.036888 against −0.000262
  in the weak class) — the class where the eye votes 26 : 2 for the trim; of
  the 30 words the ruler punishes, 18 go to the candidate and none to the base.
  The obvious narrowing was measured rather than argued: the existing
  `exit_trim_min_kink_deg` knob separates neither class at any rung (both carry
  the same kink, +7.90 against +7.44), costs MORE than the full trim between 5°
  and 25°, and gives the seam repair back. The global flip is therefore the
  smaller honest mechanism, and the entry recommends it as such.
- **The tie threshold now carries the observation that it also measures the
  class mix.** `menschliche-bewertung.md` §8a records, as an explicit proposal
  and not as a silent rule change, that a round which deliberately cuts a
  predictably invisible class will break a threshold defined over all screens —
  along with the reason the proposal is not adopted yet: a threshold that
  follows the round's own class declaration can be softened by cutting the
  classes differently.
