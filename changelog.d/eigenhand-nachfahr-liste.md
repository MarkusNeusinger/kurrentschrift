### Added

- **Die Nachfahr-Liste — the Eigenhand's work list, one row per written word
  BOX.** The plan called it „der Filter ‚Nachfahren'", and there was nothing to
  filter: Phase 1 put the work-list machinery into the three Vorlage overviews
  only, and the strip panel orders per FASSUNG by Streifen-Befund. This is that
  machinery with the Kasten as its subject — its own row model beside
  `letterRows`/`pairRows`/`wordRows`, wired to `shell/listState.ts` and
  `shell/WorkList.tsx`, with the list state in the URL under the established
  names. Each row says what the Tintentreue found and which sensor named it,
  where the Bahn comes from, how many Absetzer the script writes the word in,
  and the ONE next step: „übersprungen: unautoriert" links into the letter view
  for exactly the keys the Skip-Eintrag named — a Ground-Truth gap belongs on
  the Tafel, not in the basket — „Maske geändert" asks for `pfad --apply`
  first, and a Kasten off a Bogen printed before the cut geometry gets a
  sentence and no command at all, because that one is „nie machbar" and a
  re-follow would only write the same Skip-Eintrag again. On a box the author
  drew HIMSELF the list never offers a re-follow:
  that line is his own, and inviting the follower to replace it with one tap is
  how it would happen by accident. The order is Schwere → Streifen (author
  decision Q13, Phase 2), and the Schwere is a LADDER, not a number — rot ·
  Folger fand nichts · grau · gelb · von Hand · grün, the plan order inside a
  step. With nothing measured yet the surface says so instead of implying a
  ranking. It is fed by the one hand-wide meta-only read, so a list of every
  box costs one request and not one point of a Bahn.
- **A red Kasten can go into the Auftragskorb.** `specimen_kind` gains `strip`
  beside the two plate namespaces (Vorgabe V7) — a word item whose specimen is
  the box, addressed `S0041/F02#2`. No migration: the column is `String(16)`
  without a CHECK, and no new `kind` either, because a complaint about a
  written word is a word item wherever the word was written. The basket's link
  back resolves to the strip surface with the box in the address AND the word
  in the list's own filter, so it opens on the rows carrying that text rather
  than on every box of the hand; such a row is counted on its BOX rather than
  on the plate's Wortprobe of the same text.

### Changed

- **The Streifen surface hosts two surfaces over one hand.** `?ansicht=liste`
  is the Nachfahr-Liste, `?ansicht=galerie` the pictures with Befund chips,
  Fleckenpinsel and the Bahn layer, unchanged — the same Liste/Galerie switch
  every overview has, and no second Unteransicht for it (V2; V14 makes the
  compact list what an overview opens as). What the two can answer differs and
  is stated rather than hidden: the word search narrows both, the coverage item
  only the gallery, because a box row carries its word and never the items that
  word covers — so a jump from a coverage cell now asks for the gallery
  explicitly. A settled keystroke in the search no longer rebuilds the whole
  query either, which would have thrown the list's sort, page and filters away
  on every search.
- **„Maske geändert" is one statement again.** The free-standing warning chip
  in the Bahn caption of a Fassung was computed in the client from `flecken_n`,
  at a time when nothing else could say it. It is a grey state of the
  Tintentreue per box now, so the chip beside it had become a second statement
  of the same thing in a second vocabulary; the Nachfahr-Liste prints it next to
  the verdict, with the step it asks for. The gallery's Bahn caption keeps the
  Herkunft and the seed caveat and no longer carries the mask warning.
