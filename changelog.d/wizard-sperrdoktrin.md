### Changed

- **A locked glyph can be overwritten from the wizard, deliberately.** The lock
  used to send the author to the Tafel to unlock, back into the wizard to draw,
  and back again to re-lock — four steps for one decision, and the glyph was
  left unlocked in between. It now stays fully offered and visibly marked (chip
  in the title, hint on the Weg step, and the save button says „gesperrt"), and
  overwriting costs one confirmation that names what is replaced. The gate is
  unchanged where it matters: the server still refuses without `force` (423),
  and only that dialog ever sends it — no button sets the flag on its own
  (`docs/proposals/optimierungs-werkbank.md` §6) (#513).
- **The coverage deduction is called „Deckungslücke".** The diagnosis panel
  printed „Deckung (IoU): 0.105", „Deckungs-Gate: 0.01" and „Deckung 0.99"
  within three lines — the same quantity once as a result and once as a
  deduction, under one word, so the 0.99 read as excellent coverage while being
  the largest possible penalty. Only the deduction is renamed (`1 − gate`, the
  share of the ink the form misses); the two positive readings keep their word.
  The one-line breakdown on the letter cards also gained the „Abzüge:" prefix
  that the bar chart states under its bars, so a bare number can no longer be
  read as a score (#513).
