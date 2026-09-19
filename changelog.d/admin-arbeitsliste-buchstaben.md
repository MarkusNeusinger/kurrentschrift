### Added

- **The Buchstaben overview is a work list, and its state lives in the URL.**
  `/admin/buchstaben` now opens as one row per authored letter — glyph, key,
  score chip, the score's deductions and the chips that say what is missing
  (gesperrt · Laufform · n Vorkommen · n im Korb) — with no image at all; a
  row expands in place to the same four faces the card wall showed, and
  `?ansicht=galerie` brings that wall back as the opt-in. Measured on a
  throwaway stack with 31 letters, the page fell from 10 451 px and 31 images
  to 3 480 px and none. Nothing on the surface turns a missing read into a
  number: a chip whose own read has not answered carries no count, and „kein
  Score" waits for the score read rather than describing one that is still in
  flight. Filter chips (combined with AND, each count saying how many rows that
  chip alone would select), the sort and pages of 24 with „alle zeigen" all
  write into the query string — `?ansicht=liste|galerie&filter=&sort=&seite=` — because the state
  of a list is what a link to it has to carry, and `localStorage` cannot
  travel to another device. A new pure module `shell/listState.ts` owns those
  four names and preserves every other parameter untouched, so the subject
  keys survive a filter click and a letter opened from the list comes back to
  the same page of the same filter.

### Fixed

- **Opening a letter no longer wipes the rest of the query string.** The
  Buchstaben view rewrote the whole query on every focus change, which is why
  the overview's sort was gone the moment a letter was opened and back again.
  It merges now, and „Alle Buchstaben" returns to the list as it was left.
- **„Ohne Laufform" is read from the stored template rows instead of from a
  failed render.** The card wall discovered a missing running form by drawing
  variant 100 and catching the „not available" answer, which a list without
  images cannot do; the admin context now derives the set of letters that have
  one from the template read it already made — and the Laufform apply re-reads
  it, because a set can go stale where a per-render probe could not.
