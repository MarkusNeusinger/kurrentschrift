### Added

- **A class rule for the chart forms the plate contradicts, measured and
  booked.** Author decision A4 answers audit finding 33 with a rule instead of
  five wizard re-traces, and `core/compose.py` now carries both halves behind
  their own switches, default off: `apex_handover` hands a bound join over at
  the apex of a long unlooped lead-in (the geometric class that selects t, ſ, k
  and — a finding of the dissection — ß), and `stem_depart` generates the d's
  Auslauf the way every other join is generated, riding the letter's own stem
  down to the departure height the plate was measured at. Two switches rather
  than one because the doctrine measures a single knob at a time; the ladder
  and every gate are in `messjournal.md` §14 „Übergänge J5", pre-registered
  before the first number.
- **A blind word round on the authenticity question, built and unjudged.** The
  humanbench word mode can now compose an arm with either join rule
  (`tools/humanbench/wordarm --apex-handover/--stem-depart`, stated in the arm
  file so no round inherits a default silently), and round 6 pairs the base
  against the class rule over the 22 words it moves plus twelve null controls —
  identical panels where "no difference" is the only right answer, which is
  what makes the tie option itself measurable.

### Changed

- **The word bench can run either arm of the class rule** —
  `--apex-handover` / `--stem-depart`, on `--exit-trim`'s opt-in pattern, each
  naming itself in the header and the JSON so a rung can never file itself
  under the baseline's name.
