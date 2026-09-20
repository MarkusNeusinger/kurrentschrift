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

- **The full `PUT …/pfade` demands the same `If-Match`, and both terminal tools
  send it.** An `ETag` on the answer alone protects nothing; only the condition
  on the write path does. The window this closes is the older of the two: a
  restore (`tools.eigenhand.sync --from <snapshot>`) reads a Fassung, merges its
  archived boxes into what is up there and pushes the whole list back, so a box
  drawn in the workbench in between was overwritten by a run that then reported
  success. `tools.eigenhand.pfad --apply` merges the same way. Both now echo the
  token of their own read (`tools/eigenhand/apiclient.py` carries `If-Match` and
  hands the answer's `ETag` back), and a stale push is refused with 412.
- **A write that lands on a Streifen-Pfad list takes the row under a lock.**
  The token covers the long window between a caller's read and its write; the
  row lock covers the short one inside a single request, where two writes
  carrying the same still-valid token would otherwise both pass and the second
  would drop the first. No-op on SQLite.
- **A weakened validator of the same digest is accepted (`W/"…"`).** Cloudflare
  weakens a strong entity tag whenever it re-encodes a response, and these
  answers are gzipped at the origin and leave through that zone — a strict
  comparison would refuse every save on the one deployment path the workbench
  has. The value is a content digest and this is an application lock, not a
  cache validator, so the weakened form says exactly as much.
- **CORS exposes `ETag`.** The admin is same-origin today — the apex behind
  Cloudflare Access, the Vite proxy in dev — so nothing changes there; without
  it the token would go missing the day the workbench is served from anywhere
  else, and that reads as „saving is broken", nowhere like a CORS setting.
