### Changed

- **The Admin-Redesign plan books Phase 2 and its first round of author
  decisions.** Plan only — this change ships no code, and none of the three
  decisions below is implemented yet. `docs/proposals/admin-redesign.md`
  gains §4.7 for the three decisions of 2026-09-20 and §15.6 for the
  thirteen-PR slice of the phase. A hand-drawn path is **to be** pulled down
  as a ROW IN THE CENTRAL `kartei.json`, the way the Fleckenmaske already
  travels — the archive run copies the Kartei in full every time, so
  `snapshot.py`'s immutability assumption stays intact and needs no change,
  which is why that option was recommended. `--replace-authored` **is to
  refuse** while the box is not archived, with no second override flag (today
  it still only warns): the price is one `pull --pfade`, the gain is that
  truth cannot disappear on request. And "skipped" **is to become** its own
  entry type in the same list — `status` + `grund` mandatory, no strokes —
  because a box has exactly one state and two lists would eventually
  contradict each other; today all four skip paths still `continue` without
  an entry.

- **Phase 2's hard ordering is stated, with the reason for each step.** §15.6
  fixes four points that are not tidiness: the archive chain stands before
  anything can write a traced box, because such a path is the first own-hand
  datum that lives only in the shared DB and `/dbsnapshot` does not cover that
  column; the stored format marker stands before anything reads a format,
  because otherwise every existing row reads as format 2 and the traffic light
  claims colours for sensors that were never computed; the field-level guard
  for authored spans stands before a surface can correct one; and the per-box
  PATCH comes last of the four, because it is the first point at which a
  hand-drawn path exists at all. Each PR row carries its effort, its
  dependency and the author decision behind it, and the six still-open
  questions D–I are marked against the PR they gate, each with the path taken
  if no decision arrives.

- **Twenty-two claims of the proposal found wrong, twenty-one corrected in
  place here, each with its file:line proof** (the twenty-second, a stale
  Stand block, had already been pulled along by #632).
  The heaviest: `spans_of` gives a connector sample the
  label of the INDEX-NEAREST labelled sample, ties going to the PREVIOUS one
  (`tools/pairlab/tintenpfad.py:2018-2033`), so a connector is split down the
  middle and `connector_spans` cannot be cut out of `letter_spans` — they stay
  out of format 2. `PFAD_FORMAT` lives in `core/eigenhand/pfad.py:55`, not in
  the router, and the lockstep has five writers rather than three, the
  verify seed script among them. Two of the listed per-box states are
  properties of the whole Fassung ROW, and per box four causes are today the
  same state "no entry". Authored spans do NOT reuse the existing rule: that
  one is box-wide and hangs on `verfahren` alone, so a field comparison is new
  work in three places. `tools/tracebench/excursions.py` is already
  reference-free — it measures against the specimen's own cleaned ink — and
  only its fixture wiring is unsuitable, which turns sensor 4 into a rewiring
  rather than a new sensor. "Worst sensor wins" is not `_summarise`, which
  folds WORDS: the meant block is `severity = max` plus the `GRUND_ORDER`
  tiebreak. The archive chain as described silently loses data, and the
  analogy "archived like image, verdict and mask" reverses the direction —
  those are pushed up, a traced path has to be pulled down. The 409 was
  described too narrowly in three ways. `StripsPanel` grew to 1318 lines
  instead of shrinking, and the "Nachfahren filter" is a whole new list
  surface with one row per BOX.
