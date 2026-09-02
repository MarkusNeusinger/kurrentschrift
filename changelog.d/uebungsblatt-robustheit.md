### Fixed

- **A Vorschrift line the ruling is too narrow for no longer vanishes without a
  word.** An ordinary German sentence — „heute schreibe ich Dir aus
  Straßburg.“, 37 characters — produced a completely blank A4 sheet at the
  Sütterlin preset, and the only hint sat in a closed „Mehr dazu“ popover that
  named a different number (website audit 2026-09-02). Now the line keeps its
  row, the row is marked in the preview with its number, and the field says
  „Zeile 1 ist mit 37 Zeichen zu breit für 6 mm Mittellänge — höchstens 23
  passen.“ The Lineatur itself stays untouched: no scaling, no re-wrapping at a
  word boundary (author's decision 2026-09-02) — a Vorschrift that no longer
  sits exactly between its lines has stopped being a Vorschrift. The counts are
  measured, not guessed: how many characters fit comes from that line's own
  composition, and the help text's estimate from `AVG_ADVANCE_UNITS`, the
  composer's own average over a–z (#NNN).
- **The help text promises what the sheet can keep.** „Höchstens 12 Zeilen mit
  je 60 Zeichen“ quoted the text field's cap while 20 characters already ran off
  the row; it now computes from the chosen Mittellänge and page margin — 18
  characters at 6 mm, 44 at the Kurrent preset's 2,5 mm — and the prerendered
  crawler page states the same figure instead of a placeholder (#NNN).
- **An empty sheet says why, and cannot be downloaded.** 99 parts of Oberlänge
  fit no row on A4 and produced a blank but eagerly downloadable page. The three
  ratio fields now carry a `max` of 6 and clamp on blur (typing past a number
  input's `max` is accepted by every browser), and a page without a single row
  explains itself over the preview and holds the PDF button (#NNN).
- **A printed sheet explains its own mixed script.** With Kurrent or Offenbacher
  chosen, the Vorschrift is still set in Sütterlin — the only script written out
  so far. A line under the text field says so, and the sheet's footer prints
  „Kurrent · 2 : 1 : 2 · Vorschrift in Sütterlin“, so a printout on the table
  needs no popover to be understood (#NNN).
- **The ratio heading stops breaking after its first colon.** „Verhältnis ·
  Oberlänge : Mittellänge : Unterlänge“ wrapped mid-ratio in the 340 px panel
  and left a dangling colon at 360 px; it is now an overline plus its own
  caption line, the colons bound with non-breaking spaces (#NNN).
