### Changed

- **The Eigenhand Bogen prints a fainter lineature.** Every ruling of the
  capture theme moved down one step — baseline 0.22 → 0.12 mm (what the
  auxiliary lines used to be), waist 0.15 → 0.10, ascender/descender 0.12 →
  0.08, slant grid 0.10 → 0.06; the word-box and verdict-box frame stays at
  0.12 because the writer has to find and tick that box. The lineature only
  has to guide the hand for the seconds a row takes, and everything it does
  after that is damage: faint cyan still prints (0.06 mm is 1.4 dots at
  600 dpi), while every millimetre of it that is NOT on the paper is one the
  ingest cannot mistake for ink or smear into a measured stroke. Positions,
  Passmarken and the printed ruler check are byte-identical — only stroke
  widths moved.

### Added

- **Pinned words reach the first sheet of a frozen plan.** `python -m
  tools.eigenhand.pool pin` appends a strip of its own for every word in
  `corpus.PINNED_FIRST` and registers it in the plan's new `pins` block,
  which `plan.ordered_strips` puts at the head of plan order — so the print
  queue, the coverage progression and the Bestand all lead with it. The
  frozen strips are untouched (append-never still holds, guard included), and
  a pin leaves the front the ordinary way, by being written. First pinned
  word: `Kurrentschrift` on `S0181`, row 1 of the next Bogen.
