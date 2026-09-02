### Fixed

- **Four skills that were unusable as written.** `/verify-api` swept `/hands`
  and `/diagnostic` as public reads (both answer 401 since they were placed
  behind the open-core gate) and drove five lines with the positional
  `n-medial` key that migration `0017` removed; `/verify-migrations` offered
  only Docker and a web-container path, neither of which exists on the
  author's machine, so the gate CLAUDE.md calls mandatory before every
  Alembic push could not actually be run; `/optimize-glyphs` crashed on its
  own spot-check command (`KeyError: no fixture 't-medial'`) and invited a
  silent re-export of the frozen fixture root; `/start` recommended
  `alembic upgrade head` against what is the shared production DB. Each fix
  was verified by running it (#484).
- **A raw NUL byte made a TypeScript file binary to git and grep.**
  `SpecimenStrip/payloads.ts` joined its cache signature on a literal NUL, so
  `file` reported the source as `application/octet-stream`, every diff on it
  read `Bin 0 -> 2722 bytes`, and the licence audit's payload sweep skipped
  it entirely. The separator is now a comma — same job, and the file is text
  again (#484).

### Added

- **A rootless path for the migrations gate, verified end to end.**
  `/verify-migrations` now leads with the `pgserver` wheel (no Docker, no
  root), gains the `.env` trap as §0 — `alembic/env.py` calls `load_dotenv()`,
  so an un-exported `DATABASE_URL` silently aims at production — a single-head
  check as the fourth check, and the snapshot precondition before any
  DROP/rewrite revision (#484).
- **Four new skills for procedures that had none.** `/verify-trace` turns the
  five-step Tintenfolger measurement liturgy into a checklist with the BLAS
  pinning in the command line rather than in prose, and the "base and arm are
  the same stack but one knob" rule as an abort condition — the failure that
  produced two wrong measurements in two days. `/dbsnapshot` carries the
  create-only archive rules and the correct entry point. `/release` covers the
  fold, the tag on the merge commit and the condensed-notes rule.
  `/dependabot` covers the weekly batch and the `update-branch` trap (#484).
- **`tests/test_agent_instructions.py` pins the agent guides against drift.**
  136 backticked paths must resolve, 48 `§N` references must hit a real
  heading (a range like `§3–§6` asserts every section in it), and 22 rules
  must be present in BOTH `CLAUDE.md` and
  `copilot-instructions.md` — the two files claim to stay in sync, and until
  now nothing checked it (#484).

### Changed

- **`/work-basket` states what a second round after a rejection costs.**
  The skill said only "re-read the row before you close it", which no
  longer describes the API: closing now reads `stage` and `resolution`
  from the PATCH itself, never from the stored row, so a bare
  `{"status":"done"}` answers 422 instead of quietly reinstating the
  restatement the author had just rejected (#484).
- **`/verify-frontend` now judges against the binding spec, and measures
  a11y the only way that works.** Style checks pointed at
  `style-guide.md`, which says itself that tokens are no longer maintained
  there, while the binding `design-system.md` appeared in no skill at all;
  the skill also never named the three static gates CI runs. It now carries
  both, plus two measurement gotchas that each produced a false negative:
  a scripted `element.focus()` does not trigger `:focus-visible`, so focus
  rings must be driven with real key events (a Tab walk), and a type-floor
  sweep must count only elements with their own visible text — an invisible
  MUI switch input measures ~13.33 px and is not a legibility problem
  (#484).
- **The rules now reach both audiences.** Five rules lived only in
  `copilot-instructions.md` (never merge a PR yourself, `core/` PRs quote
  bench numbers, the code standards, never silently diverge, Codecov as
  reviewer) and four author directives lived only in a machine-local memory
  that no cloud session and no Copilot ever sees (`Fixes #N` in the PR body,
  the sibling-repo transfer rule, using asymmetric findings instead of
  discarding them, and that the author authors in the PROD admin so admin-UI
  reports are against `origin/main`). All nine are now in both files, the
  pre-commit section states what is actually configured, and rotting file
  lists became pointers. `prime.md` shed the repository map it duplicated out
  of date (#484).
- **Two licence nets that had stopped working.** The hidden-payload sweep
  matched a bare `;base64,` and needed an exclusion list that had fallen five
  files behind, so its OK branch could never fire; it now matches the payload
  class itself — a long literal blob — and reports nothing repo-wide while
  still catching a synthetic embedding. The history sweep only ever saw binary
  extensions, so the reserved-data blob committed in June as a `.ts` file was
  invisible to it; a content pickaxe over the payload keys now names it
  (#484).

- **Data provenance closed at four gaps.** `igerman98` — the one source with
  real copyleft obligations — was missing from the provenance index and its
  server-data-only rule from both agent guides; the specimen actually shipped
  on /schriftkunde had no provenance while a documented 900 px variant is
  referenced by nothing; `chart.svg` and `words.json` carried no SHA256; and
  §5 described the compose golden as "no templates" when it holds the full
  render payloads of 27 glyph keys. All corrected against measurement, and the
  audit battery now also sweeps `data/corpora`, `data/samples` and the shipped
  specimens (#484).
