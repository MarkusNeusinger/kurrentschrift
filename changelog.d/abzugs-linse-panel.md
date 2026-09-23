### Added

- **The Abzugs-Linse in the letter view: where the score takes its points
  off, drawn over the Tafel-Ausschnitt.** A second switch „Abzüge“ under
  „Landmarken“ in `/admin/buchstaben?g=…` opens a lens that loads only when
  opened (the re-score costs 0.3–2.5 s) and draws every located deduction of
  the chart row over the dimmed crop the ruler measured, not over the written
  form — the renderer widens round bodies, so a mark there would sit beside
  the scored ink. One mark hue for all six categories, the category carried
  by the mark's shape (square, ring, bracket, band, hatch, stipple, dots,
  feelers) and the size by its width on one scale per letter, so no reader
  has to tell colours apart. The legend chips are the „Abzüge (neu
  gemessen)“ line and the filter at once, read „nicht anwendbar“ instead of
  a 0, and name the part without a place; a „gespeichert“ line appears only
  where the stamped list value moved by more than 0.005. The five costliest
  sites stand as discs ①–⑤ on the image and as a list beside it, placed so
  no disc covers another; the list and the image select each other, the
  marks are pointer sugar with 44 px targets, and the keyboard path is the
  list (one tab stop). A Senkrechte run is drawn exaggerated ×20, or less
  where ×20 would swing past 0.15 x-heights, and the detail names the factor.
  ⚑ files a plain letter item whose note opens with the site, its part of
  the category number and its raw numbers — no new Korb kind or stage, and
  no pre-sort question, since the lens already shows the letter on its own.
  Kurrent and Offenbacher get the list's own sentence „diese Schrift misst
  anders“.
- **Abzugs-Token in `styles/paper.ts`.** `penalty` (mark · centerline ·
  selected · pin) and `penaltyCropAlpha`, measured in `paper.test.ts` against
  white and against the plate ink dimmed to the crop's 0.35 — not layer
  tokens, because a fourth hue clearing 3:1 on white and on undimmed ink does
  not exist.

### Changed

- **The collinearity deduction reads „Kreuzungsflucht“ everywhere it is
  labelled.** List, cards, Diagnose and wizard said „Kreuzung“ — the word the
  Landmarken-Linse uses for a detected crossing on the same page. Only the
  deduction was renamed; the landmark keeps its word. The score breakdown's
  label column grows with the longer name, measured from the strings as
  before.
