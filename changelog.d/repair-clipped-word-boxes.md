### Fixed

- **Six word specimens whose rect cut off their own ink.** The i-Strich of
  `einer` and the u-Bogen of `zum` were sliced by the top edge of their
  crop, `das` and `und` lost the d's entry stroke, `Wer` and `zwei` sat
  below the plate's own clearance. The rects now enclose that ink with air.
  The cause was the standard itself: `propose_boxes` cuts with a 3 px pad
  measured on the DESPECKLED mask, and a thin Sütterlin diacritic falls
  under the despeckle floor or lands on the border.

### Added

- **`tools/wordbench/repair_boxes.py`, the repair as a repeatable
  measurement.** It re-measures on the raw binarised plate and lifts only
  the edges whose clearance fell below the plate's standard — 169 of the
  202 specimens sit at exactly that 3 px and are left byte for byte alone,
  because every rect it touches is a fixture and a stored trace
  registration that has to move with it. What counts as the word's own ink
  is decided by the line's own lineature rather than a pixel count:
  components outside ±1.35 x-heights belong to the neighbouring line,
  punctuation hangs entirely below the Mittellinie and is never pulled in
  (every right-edge candidate of the first pass was a comma), pale
  bleed-through fails a darkness comparison against the word's own stroke.
  An edge that would grow by more than one x-height is reported instead of
  applied — then something foreign hangs on the ink, as with the comma
  fused to the last letter's exit stroke in `regieren`.
- **`tools/wordbench/shift_registrations.py` for the other half.** A stored
  trace registers in crop-local pixels, so a moved rect origin leaves it
  beside its own ink and stamped „Rahmen veraltet". The correction is
  exactly that origin shift — no re-tracing — and it is idempotent: a row
  already sitting in the repaired crop is left alone. It writes to the
  shared database, so it is dry-run by default (#NNN).

### Changed

- **A clipped specimen is repaired first and flagged `incomplete` second.**
  The flag stays for ink that ends on the plate itself, where no rect can
  enclose it. The frozen fixture is a reason for a declared re-baseline,
  not a reason to leave the defect standing — `qualitaetsmetrik.md` §15
  carries the dated entry and the re-export the repair falls due for.
- **`propose_boxes.py` imports its mask helpers from `core.word_metric`
  again.** They moved there and the tool had been failing on import ever
  since.
