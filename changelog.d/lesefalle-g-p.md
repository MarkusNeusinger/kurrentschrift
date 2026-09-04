### Added

- **g and p as a reading trap, in the quiz and in the readings.** The
  reading quiz now names what separates them after a wrong pick — the g
  closes a round loop below the line, the p goes down straight and carries
  its bow at the upper right — and the Lesart search folds the two into one
  look-alike class, so `Rappe` and `Ragge` finally reach each other. The
  pair is documented in `orthographie-regeln.md` §3, which is what the
  catalogue requires before it explains anything at all.

### Changed

- **The Lesart vocabulary's content hash covers the fold, not only the
  words.** A word is findable only under the key it was stored with, so a
  new look-alike pair silently strands every word it re-buckets. The fold
  now carries a version (`core.lesarten.LESART_KEY_VERSION`) that goes into
  the build hash — the same word list under a changed table is a new build
  and can no longer be refused as already live — and into the build's source
  label, so `GET /lesarten/dictionary` reports a generation bucketed by an
  older fold as `stale`. Bumping the table without reloading is now visible
  instead of silent: the API refuses a build from another fold outright (it
  computes the buckets itself, so a loader running ahead of the deploy would
  store the old ones under the new label), and the Lesart page says the
  vocabulary is being switched over rather than calling a reading unique.
