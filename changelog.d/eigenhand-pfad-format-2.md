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
  inside a merge. An answer BY HAND passes for both fields — boundaries lie on
  a Bahn and do not outlive it, and guarding them against the author's own
  re-draw left him no move at all. A Skip-Eintrag is never such an answer,
  whatever `verfahren` it claims: it says there is no path in this box, and
  letting it through would delete a drawing without the 409 and without the
  archive check that hangs off `--replace-authored`.
- **A push declares the format its BODY is in, not the one this image writes.**
  Both tools push entries they did not produce — `tools.eigenhand.pfad` merges
  around the boxes it did not follow and carries the author's boundaries onto
  its own result, `tools.eigenhand.sync` restores what an archive holds — so a
  declaration taken from `PFAD_FORMAT` would have been refused by the very
  content rule above, and the carry-over could never have reached the one kind
  of box it exists for. `core.eigenhand.pfad.format_of_entries` answers it from
  the content, and only ever upward.
- **`pull --pfade` carries hand-corrected letter boundaries into the archive
  too.** The one Ziehweg filtered on the Bahn's `verfahren` alone, so a
  followed path whose boundaries the author had corrected was never pulled,
  never snapshotted and never restored — the phase's own rule („the archive
  chain stands before anything can create hand work") would have held for one
  of the two pieces of hand work only.
- **The SPA wire types carry the format-2 entry.** `EigenhandPfad` gains
  `status`, `grund`, `detail` and `letter_spans`, and `strokes`,
  `registration_px` and `xh_px` become what the API really answers with. The
  surfaces that draw or count a path take skips out through one narrowing
  predicate (`bahnenOf`) rather than a hand-written filter each, because a skip
  reaching the overlay is not a wrong picture but a crash.
- **`format` is required on a Streifen-Pfad push.** The wire default was bound
  to the moving constant, which was safe only while exactly one format was
  admitted: now that the guard lets two through, a push naming no format would
  claim whichever number this image writes and the row would be stamped with
  it. Every writer in the repo already names it; the repo's own test helper now
  does too.
