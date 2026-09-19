### Changed

- **One noun for the line: „Bahn", on the plate and on the strip.** The same
  followed or traced line was called „Pfad" on the Eigenhand page, „Spur" in
  the Wörter intro, „Nachfahrung" and „Pfad" on the two layer buttons and
  „Bahn" in the chips — four names for one thing, each of them defensible
  where it stood and none of them readable together. Every German admin string
  now says „Bahn" (author decision 2026-09-18, Q8 b). Because the two layer
  buttons show the SAME line, the second one is named after what it adds:
  „Bahn" + „Bewegung", which is what its hint has said all along. The locale
  KEYS, the module names and the `belege/` directory keep pointing at the data
  field `eigenhand_strips.pfade`, whose glossary name „Streifen-Pfad" stays a
  field name and never a UI word — a new vitest over the six namespaces that
  talk about a drawn line (`werkbank`, `words`, `belege`, `joins`, `eigenhand`,
  `compare`) keeps the split from rotting back, with terminal commands and the
  follower's own name „Tintenpfad" exempt.
- **Where a line came from, as a chip that says it plainly.** A strip's path
  row carries its own `verfahren`, so the origin leaves the caption and stands
  beside the „Saat"-Chip as one of its own, reading „automatisch (Tintenpfad)"
  or „von Hand" instead of the raw column value — only where the Verfahren
  themselves disagree does the chip stay away, because then no single one is
  true of the Fassung; a word followed again on another day changes the
  caption, never the origin.
  A Verfahren the UI does not know is handed back unchanged rather than
  relabelled, because the column is free text and a silent swap would turn a
  foreign follower into a Tintenpfad. A plate line says only „automatisch":
  `word_instances` records no follower, and rows harvested before the
  Tintenpfad became the standard one may have been laid by the Kette — naming
  a method there would be a claim the row cannot back.
- **The three roles get their labels, and „Beleg" gets its one meaning back.**
  Tafel · Platte · Eigenhand now live as shared `shell.role*` strings with
  their first-appearance glosses („Platte (historische Hand)", „Eigenhand
  (meine Hand)"), ready for the Scope-Leiste to name a scope without inventing
  its own wording; the Eigenhand page carries its gloss once at the top. The
  last „Beleg" on a plate surface — the Übergänge detail's „Platten-Beleg" —
  becomes „Bahn der Platte (nachgefahren)", so the word counts accepted
  Fassungen in the own-hand Bestand and nothing else. The ten leftover strings
  of the retired `/admin/belege` page went with it; nothing rendered them.
