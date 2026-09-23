### Added

- **The Abzugs-Linse in the letter view: where the score takes its points
  off, drawn over the Tafel-Ausschnitt.** A second switch „Abzüge“ under
  „Landmarken“ in `/admin/buchstaben?g=…` opens a lens that loads only when
  opened (the re-score costs 0.3–2.5 s) and draws every located deduction of
  the chart row over the dimmed crop the ruler measured, not over the written
  form — the renderer widens round bodies, so a mark there would sit beside
  the scored ink. One mark hue for all six categories, the category carried
  by the mark's shape (band, bracket, square, ring, crosshatch, hatch,
  stipple, ticks across the edge, feelers) and the size by its width on one
  scale per letter, so no reader has to tell colours apart. What frames a
  deduction without being one — the Doppelzug zone, the Glätte corner
  windows — is context, in a hue and a thin dashed form of its own (an
  outline; a span with end bars), so a zone edge can no longer pass for a
  Chamfer edge on the same pixels. The legend chips are the „Abzüge (neu
  gemessen)“ line and the image's filter at once, read „nicht anwendbar“
  instead of a 0, name the part without a place, and say „Karte verworfen“
  where the core dropped a category's map; a „gespeichert“ line appears only
  where the stamped list value moved by more than 0.005. The five costliest
  sites stand as discs ①–⑤ on the image and as a list beside it, placed so
  no disc covers another, and never on a site apportioned 0.0000; the list
  and the image select each other, the marks are pointer sugar with 44 px
  targets, and the keyboard path is the list (one tab stop), which keeps
  every category — also one switched off on the image — and speaks the
  rank. A row the ruler cannot score gets the sentence that helps
  (resample or re-trace), not „reload“. A Senkrechte run is drawn
  exaggerated ×20, or less where ×20 would swing past 0.15 x-heights, and
  the detail names the factor.
  ⚑ files a plain letter item whose note opens with the site, its part of
  the category number and its raw numbers — no new Korb kind or stage, and
  no pre-sort question, since the lens already shows the letter on its own.
  Kurrent and Offenbacher get the list's own sentence „diese Schrift misst
  anders“.
- **Abzugs-Token in `styles/paper.ts`.** `penalty` (mark · context ·
  centerline · selected · pin) and `penaltyCropAlpha`, measured in
  `paper.test.ts` against white and against the plate ink dimmed to the
  crop's 0.35 — not layer tokens, because a fourth hue clearing 3:1 on white
  and on undimmed ink does not exist. `context` also keeps a deuteranope's
  ΔE ≥ 35 to every other token.

### Changed

- **The collinearity deduction reads „Kreuzungsflucht“ everywhere it is
  labelled.** List, cards, Diagnose and wizard said „Kreuzung“ — the word the
  Landmarken-Linse uses for a detected crossing on the same page. Only the
  deduction was renamed; the landmark keeps its word. The score breakdown's
  label column grows with the longer name, measured from the strings as
  before.
- **The Diagnose quality view says what helps on a row without pixel
  anchors.** Its 409 used to read the generic „erst neu laden“, which cannot
  help; it now says to resample or re-trace in the wizard, with the raw line
  still folded underneath.
