### Added

- **A written text wraps into lines instead of shrinking under the ink
  floor.** Where the measured frame would put a line under 14 px of x-height
  — the design system's own floor for the smallest type it allows —
  `WrittenWord` breaks the text at word boundaries and composes each line
  on its own, so a line runs as ONE continuous pen stroke from its Anstrich
  to its Auslauf and "Zug um Zug" holds per line rather than per text. On a
  360 px phone the audit's 29-character sentence goes from 7.1 px per
  template unit on one line to 16.2 px over three; on the desktop nothing
  moves. The floor is a promise about the RESULT: the split is planned from
  the text's average advance, and a line that comes back from the composer
  denser than that average is re-planned with its measured width, so a
  breakable line never stays under the floor. Owner decision 2026-09-04:
  the two alternatives — a scale floor
  with a horizontally scrolling surface, and a viewport-coupled character
  cap — are rejected. A single word too wide for the frame is not
  hyphenated; it stays one line below the floor.

### Fixed

- **The replay button no longer stands in the writing.** The ↺ hangs inside
  the ink box, so wherever that box hugged the writing it sat on the last
  letters: in the quiz it was inside a 62.5 px letter box and read like a
  part of the form, on the very page that asks the reader to tell forms
  apart. Both written surfaces now reserve ground for it — a gutter beside
  the ink where the white frame is wider than the writing (it is, on every
  surface that shows the button), a strip under the line where it is not.
- **The written box is measured, not assumed.** `WrittenWord` and
  `WrittenGlyph` sized their box from the caller's `maxWidth` constant while
  the browser squeezed the ink into the real frame, which left a 22 px line
  of writing inside a box three times as tall. The frame's width is now
  measured (`useAvailableWidth`) and caps the caller's constant, so the box
  is the writing's own size.
