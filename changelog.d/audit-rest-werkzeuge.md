### Fixed

- **The bench run directory is ignored where the benches actually write it.**
  Both bench READMEs are invoked from the repo root and write to `runs/dev/…`,
  which resolves to `<root>/runs/` — a path neither of the two package-scoped
  ignore rules (`tools/wordbench/runs/`, `tools/glyphbench/runs/`) ever
  covered, so a full run left its whole output tree sitting in `git status`.
- **The InkSight and route-G development split is reproducible again.**
  `dev_ids()` turned the frozen `TRACEBENCH_DEV_IDS` frozenset into a tuple
  without sorting on the InkSight side, so the key order of `frames.json` and
  the run log differed between two runs over identical inputs — a measurement
  artifact that was not byte-reproducible. Both routes now sort, and both are
  pinned to the same order by a test, because the two are compared word by
  word. The guarded import that silently fell back to a ten-id literal (the
  split has nineteen) is gone with it: it dated from before `tools/tracebench`
  existed and could only ever fire as a run that measured half the words
  without saying so.

### Changed

- **The sitemap `<lastmod>` guard measures the rendered page, not a list of
  its ingredients.** `scripts/check-sitemap-lastmod.mjs` held each route's
  date against the git history of a hand-kept `PageSpec.sources` list, which
  drifted in both directions — a shared file such as `seo.ts` marked pages
  stale whose text had not moved, while a body reaching for an unlisted module
  changed the page unseen. It now reads the history of
  `app/prerender/<page>.html`, which is the literal answer to "when did this
  page change" and needs no bookkeeping to stay true. The comparison itself
  moved into `staleLastmods()` beside the renderer, where a unit test drives
  its four cases (committed, uncommitted, no history, the route-less 404).
- **`/open-pr` retires the "add the PR number to the fragment" step.**
  `tools.changelog` never required a `(#NNN)`, and the number is unknowable
  until the PR exists, so the step meant a follow-up commit carrying one token
  — which three agents in one day did with `sed -i`, against the rule that
  repo files are edited with Edit/Write only. The fragment may now be written
  without a number, and the skill and `changelog.d/README.md` say so. The
  skill's merge section also states the wait that #504 taught: the
  `copilot-pull-request-reviewer` check must be `completed` on the current
  head SHA and all review threads resolved, and a draft is made ready first —
  a draft is never reviewed at all.
