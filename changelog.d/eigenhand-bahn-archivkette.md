### Added

- **The archive chain for hand-drawn Bahnen.** `tools.eigenhand.pull --pfade`
  brings a hand's `authored` Streifen-Pfade down out of the shared database
  into the local Kartei, `snapshot` carries them into the private archive
  unchanged, and `tools.eigenhand.sync --from` puts them back. A traced Bahn
  is the one own-hand datum born in the browser: nothing can follow it again,
  and until now neither the own-hand archive nor the DB snapshot held a second
  copy of it. The pulled record lands in the central `kartei.json` and nowhere
  else, because an archive run copies the Kartei in full while it skips an
  already filed Fassung directory as an immutable unit — a file written into
  one would never reach the archive and the run would still report success.
  It carries two versions: its own, so a later reader can tell what it is
  holding, and the `PFAD_FORMAT` the API answered under, so a restore declares
  the entries correctly.

### Changed

- **A restore that leaves a hand-drawn Bahn behind now ends loudly.**
  `sync --from` closes with how many were restored, how many were already
  there and how many are NOT, counted off the server's own answer, and fails
  on the last count — typically a run without `--mit-streifen`, where no strip
  row exists up there for a path to hang off. A silent partial restore is the
  failure this chain exists to prevent. An archive that holds no drawing at
  all says so too, since that looks identical to a hand that never had one.
  The restore fills only the boxes the server has no path for; one that
  already carries another path is left as it is and named, so a drawing
  corrected in the workbench or a box deliberately handed to a follower is
  never silently reverted.
- **`sync --from` reads the Kartei from the newest snapshot of the hand.**
  The files around it were already layered newest-first, but the Kartei came
  from the directory that was named — and since a hand-drawn Bahn rides in the
  Kartei and nowhere else, naming a stamp one too far back would have restored
  an older set of drawings and reported a clean run. The run says which
  snapshot the Kartei came from.
- **`--replace-authored` refuses while the drawing is not archived.**
  `tools.eigenhand.pfad` used to only warn before handing a hand-drawn path
  over to a follower run, and afterwards the drawing existed nowhere. It now
  checks that this exact Bahn is in the Kartei — a copy pulled before the
  author corrected his own trace does not count — and the refusal names the
  one command that resolves it. No second override flag beside it.
- **The DB snapshot's manifest names the `eigenhand_strips.pfade` gap.** It
  was silent about the one column it does not carry, so a reader took the
  snapshot for more complete than it is. The new `known_gaps` entry says that
  a followed path is re-made by re-running `tools.eigenhand.pfad` and that a
  hand-drawn one's master is the own-hand archive tree's `kartei.json`.
