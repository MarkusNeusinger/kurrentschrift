### Changed

- **`/tafel` holds its three sections open while they load, instead of showing
  a spinner.** The route's whole measured layout shift was one moment: until
  `/sources` answered, the page was a centred „lade Vorlage …" exactly one
  viewport tall, so the footer stood inside the viewport — and when the three
  script sections mounted at once, the document went to 3132 px (mobile) /
  4494 px (desktop) and pushed the footer out. The page now draws its own
  header and its three sections at their finished height from the first paint:
  the real script names and Feder captions (both fixed copy, so they never
  move in), a box the size of the state chip, each plate at its own aspect
  ratio, and the provenance card. Measured the way the shift was measured for
  #517 — real Chrome over CDP, Slow 4G + 4× CPU, cache off, three runs per
  viewport — CLS falls from 0.0969 to 0.0007 on mobile and from 0.1125 to
  0.0004 on desktop, and what is left is the site header's own webfont swap,
  which the old page had too. The reserved page is 41 px (mobile) / 59 px
  (desktop) short of the finished one, all of it the Original/Geschrieben
  toggle on the one written script, which is below the fold on both. The
  shimmer honours `prefers-reduced-motion` by not running at all.
