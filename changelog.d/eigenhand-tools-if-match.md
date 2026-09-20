### Changed

- **A refused Streifen-Pfad push now names the command that puts it right.**
  The two terminal writers already echo the `If-Match` token of their own read,
  so the server refuses a merge made on a list that has moved (412). What the
  operator got back was the server's words alone — correct, and addressed to a
  client rather than to the person at the keyboard. `tools.eigenhand.pfad
  --apply` now stops with the exact follow-up run (deliberately without
  `--replace-authored`: whatever landed in between is precisely what a blanket
  override would give up again), and `sync --from` counts that Fassung as NOT
  restored, names it beside the ones whose strip row is missing and carries on
  through the rest of the Kartei — one moved list says nothing about the other
  forty, and the closing refusal still ends the restore loudly and non-zero.
  The 412 arrives as its own refusal type (`StaleRead`), so a caller can add
  that sentence without matching on the server's prose, and nothing anywhere
  retries: re-sending the same merge against the list that is there now would
  be the lost update the token just refused, with one extra step.

### Added

- **The tools' HTTP layer is under test.** `tools/eigenhand/apiclient.py`
  carries the admin token, the `If-Match` condition and every refusal the
  chain can meet, and every existing test stubbed it out at the module seam —
  so nothing pinned the parts a stub imitates: the condition reaching the
  request verbatim (weak validators included), the `ETag` being read off the
  answer rather than reconstructed from the payload, `allow_404` swallowing a
  404 and never a 412, and a refusal arriving as a refusal instead of as a
  value some caller then merges.
