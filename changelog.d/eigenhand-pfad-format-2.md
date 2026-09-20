### Added

- **Streifen-Pfad format 2 — the API reads and accepts it, and keeps storing
  what is pushed.** `core.eigenhand.pfad.SUPPORTED_FORMATS` is now `(1, 2)`
  while `PFAD_FORMAT` stays the format this image WRITES, and the 409 fires
  only on a number the API does not know. That gap is the lockstep: the server
  admits the newer shape one release before any writer produces it, and the
  stored marker (`eigenhand_strips.pfade_format`) makes the two shapes coexist
  per row rather than per deployment. What a push declares is checked as
  CONTENT, not just stamped — a format-2 field under format 1 is refused, and
  so is a copy of `letter_spans` hidden in the free `meta` under format 2,
  because a row whose cell does not obey its own number is the mislabelling the
  marker exists to prevent.
- **A Skip-Eintrag says why a word box carries no path.** An entry of the same
  list with `status: "skipped"`, a `grund` out of a closed vocabulary
  (`not_selected` · `no_geometry` · `unauthored` · `gave_up` · `other`), an
  optional `detail`, no strokes, and registration and x-height optional (author
  decision C, 2026-09-20). Until now those four situations were one
  indistinguishable state — „no entry" — and they are not the same work at all:
  „skipped: unauthored" is a jump to the plate rather than tracing, and only
  „gave up" is follower work. One list rather than two, because a box has
  exactly one state; a closed vocabulary rather than free text, because the
  four would merge again within a month.
- **Letter boundaries are a checked field with their own provenance.**
  `letter_spans` moves out of the unvalidated `meta` into the entry itself,
  each span carrying `herkunft` (`auto` | `authored`), and its indices are held
  against the strokes they point into: the follower assigns them on the decoded
  path while the entry stores the CAPPED strokes, so a word past 4096 points or
  128 strokes could desynchronise the two silently. The refusal names the span
  and the stroke that disagree — a desynchronised span is well-formed in every
  number it carries, so only the stroke it names can refuse it.

### Changed

- **The authored rule compares FIELDS instead of whole boxes.**
  `displaced_authored` weighed `verfahren` and `box_index` and waved everything
  inside the entry through; it now reports per box AND per field, so a push
  that keeps the `verfahren` and drops the hand-corrected boundaries is refused
  by name, while a box that only carries corrected boundaries is no longer
  locked against an ordinary re-follow — the boundaries just have to come back
  with it. `tools.eigenhand.pfad` carries them over by itself, keeps a
  hand-corrected stroke's boundaries whole, and where the fresh Bahn cannot
  hold them at all keeps the stored entry and says so, because re-indexing a
  hand-drawn boundary is the Span-Zuordner's work and not a silent repair
  inside a merge.
- **`format` is required on a Streifen-Pfad push.** The wire default was bound
  to the moving constant, which was safe only while exactly one format was
  admitted: now that the guard lets two through, a push naming no format would
  claim whichever number this image writes and the row would be stamped with
  it. Every writer in the repo already names it; the repo's own test helper now
  does too.
