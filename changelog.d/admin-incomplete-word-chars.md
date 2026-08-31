### Added

- **A tracing-status filter over the admin word specimens.** The Wörter
  overview gets a status select beside the search field — Alle · Offen ·
  Nachgefahren · Unvollständig — so "what is still to trace?" is a choice
  rather than a scroll through the whole list hunting for a missing chip.
  A specimen counts as done only on a stored hand-drawn trace: an automatic
  fit is what the manual pass exists to replace, so it stays open.
- **`incomplete` specimens in the words.json sidecar.** Some word specimens
  can never be traced by hand because their own ink is clipped — a cut-off
  i-dot, a last letter running off the plate rect. Flagging the entry
  (`"incomplete": true`, the reason in its `note`) takes it out of the open
  work list and out of the tracing tally's denominator, where it would
  otherwise sit forever as an unreachable "still open", and shows it as a
  chip on the card and in the word detail. It stays a specimen: the intact
  part is still measurable. The flag is data rather than a click because
  the rect corners are frozen bench fixtures — re-cutting a clipped
  specimen larger would re-baseline the word bench. `/word-samples` now
  carries `incomplete` and `note` (#NNN).
