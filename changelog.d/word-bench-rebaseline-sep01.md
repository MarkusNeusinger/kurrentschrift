### Changed

- **Word bench re-baselined after the repaired specimen rects: 0.106400 →
  0.109255.** Seven of the 63 word references now show ink their crop used
  to cut off, so the composition has more to hit and the headline rises —
  the predicted direction, and the point of the repair: until now those
  words were measured against a letter that was not fully on the reference.
  Numbers do not compare across this line (`qualitaetsmetrik.md` §2). Pairs
  are unmoved at 0.148433, as expected — no rect on the pairs plate was
  touched. The dated entry with the per-word losses and the order the three
  steps had to run in is `qualitaetsmetrik.md` §15.

### Fixed

- **`shift_registrations` could not reach the deployed API.** It built its
  own HTTP client, and the edge answers a bare `Python-urllib` User-Agent
  with a 403. Reads now go through `fetch_fixtures.ApiClient` — the
  read-only client the archive tool already shares for exactly this reason
  — and the one write borrows its redirect and TLS handling rather than
  restating it. `ApiClient` keeps having no write verb: that is what makes
  it safe to share.
- **The batch write would have renamed the writer.** Its `hand` is a
  get-or-create that overwrites `label`/`era`/`note` with whatever the body
  carries, and `label` is required — so the tool now reads the stored hand
  back and echoes it instead of inventing one (#NNN).
