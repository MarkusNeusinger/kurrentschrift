### Fixed

- **The replay button no longer sits on the writing.** A line that hits its
  width cap collapses the box to the aspect of the ink — at 390 px a
  29-character sentence is 25 px tall — and the ↺ hanging bottom-right inside
  that box landed on the last letters, on the Federprobe and on the Lesart
  check alike. The box now reserves the height its caller asked for wherever
  the button exists, so the writing keeps its ground and the button gets its
  own; measured on the live page, the button sits 39 px (Federprobe) and 28 px
  (Lesart) below the ink instead of inside it. Nothing else moves: a surface
  without the button still hugs the writing exactly as before.

### Changed

- **The `/tafel` layout shift is measured, and it is not the font.** The
  website audit read the jump as the late GLKurrent section initial and left a
  `font-display` question open behind it. Six production runs (real Chrome over
  CDP, Slow 4G + 4× CPU) put it at 0.095 mobile and 0.112 desktop — and in
  every one of them the show font is already loaded when the shift happens.
  The whole value is the page growing from 844 px to 3132 px in one step when
  `/sources` answers, which pushes the footer out of the viewport; the three
  chart scans contribute nothing, having carried their `chart_size` aspect
  ratio since #476. `frontend-stack.md` records the numbers, the method and
  what follows: reserving the sections' height would move this number, the
  font setting would not.
