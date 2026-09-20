### Added

- **A Streifen-Pfad box can be written on its own, and only onto the list it
  was drawn on.** `PATCH /eigenhand/strips/{hand}/{strip}/{fassung}/pfade/{box}`
  stores ONE word box's Bahn and merges it into the stored list; the read and
  the full push now answer with an `ETag` over that list, and the per-box write
  demands it back in `If-Match` (428 without one, 412 when the stored list has
  moved on). A PATCH because the editor knows one box: a full replacement would
  restate the rest of the row from a list the browser read minutes ago and
  overwrite whatever landed in between. This is the first door a Bahn can come
  through from the workbench, which is why the archive chain, the stored format
  marker and the field-level authored guard had to exist first — the route is
  what they were built for.
- **`verfahren` is stamped by the server on that route, never read from the
  body.** The per-box door exists for the author's own hand; a body claiming
  another provenance is refused rather than re-labelled, because a followed path
  stored as a drawing would be ground truth nothing could ever tell apart from
  one. A derivation keeps going through the full push, where the rules for one
  live. `displaced_authored` is deliberately not applied here and the code says
  why: it guards the author's work against a FOLLOWER run, and there is no
  follower on this path — every entry it can store is authored, so the rule
  would refuse nothing while reading like a guard. The refusal of an authored
  skip in `check_paths` is what actually keeps an empty entry from taking a
  drawing's place.

### Changed

- **The full `PUT …/pfade` honours `If-Match` when a push carries one.**
  Honoured, not demanded: the writers on that side are terminal tools that do
  not send the header yet, so requiring it in the same release that introduces
  it would break the push chain rather than guard it — the same lockstep the
  format follows. Its answer carries the new `ETag` either way, so
  `tools.eigenhand.pfad` and `tools.eigenhand.sync` can start echoing it without
  the API moving again, and the read-then-replace window the archive hand-off
  named closes when they do.
- **CORS exposes `ETag`.** The admin is same-origin today — the apex behind
  Cloudflare Access, the Vite proxy in dev — so nothing changes there; without
  it the token would go missing the day the workbench is served from anywhere
  else, and that reads as „saving is broken", nowhere like a CORS setting.
