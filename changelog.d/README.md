# changelog.d — one fragment per PR

Every PR that changes code adds ONE file here instead of editing
`CHANGELOG.md`: `changelog.d/<slug>.md`, the slug naming the change (the
branch name minus its prefix does fine — `tafel-detail.md`,
`lesarten-dictionary.md`). Nothing else touches `CHANGELOG.md` between
releases, so two PRs never meet at the same line again — the reason this
directory exists (2026-08-30; before it, every sibling merge conflicted the
others under `[Unreleased]`, and the union merge driver healed only the
local rebase).

A fragment is a slice of the changelog in the changelog's own format:

```markdown
### Added

- **The thing, named as the reader will meet it.** One clause on what it
  does and where, then why it is the right shape — the rationale a diff
  cannot carry.

### Fixed

- **What was wrong, as a title.** What it did, what it does now.
```

**The `(#NNN)` reference is optional; the unfilled placeholder is not.** The
number does not exist until the PR does — so chasing it meant a second commit
carrying one token, which is how three `sed -i` edits slipped past the
Edit/Write rule in a single day (2026-09-02). Write the fragment without
one. The link is not lost either way: `git log --diff-filter=A -- <fragment>`
names the squash commit, whose subject ends in the PR number. Where a
number IS present — every fragment written before 2026-09-03 has one — it
stays; this is forward-only, not a sweep. What `check` refuses is the letter
N left standing where a number was meant to go: `(#NNN)` shipped as written
reads as a reference in the released section and points nowhere. So: a
number, or nothing. (Quoted in backticks it is prose ABOUT the placeholder —
this paragraph included — and passes.)

Rules, all enforced by `uv run python -m tools.changelog check`:

- Headings are `### Added` · `### Changed` · `### Deprecated` · `### Removed`
  · `### Fixed` · `### Security` (Keep a Changelog), each at most once per
  fragment; a fragment has at least one bullet.
- A bullet opens with its bold title and wraps with two-space indentation,
  exactly like the entries already in `CHANGELOG.md`; English
  (sprachregelung.md §1 — GitHub-facing text), written like the existing
  entries: what, where, why. The closing `**` may sit on the continuation
  line — a long title is allowed to wrap — but it has to be there.
- No bare `(#NNN)`: fill the number in or leave the reference out.
- Nothing else in the file — no prose above the first heading, no `##`.

The CI job „Changelog (fragment)" requires a fragment in every PR — except
data-only PRs (everything under `data/`, covered by `SOURCE.md`), PRs
labelled `skip-changelog` and Dependabot's own PRs (a bot writes neither a
fragment nor a label, and its routine bumps are what the release notes leave
out anyway) — and refuses bullets ADDED to `[Unreleased]` directly.

Added, not merely different: a bullet is identified by its bold title, so
correcting the wording of an entry `[Unreleased]` already carries — a typo in
a shipped line, a sharper clause — passes, and only a title the base does not
have counts as a new entry that belongs in a fragment.
`uv run python -m tools.changelog check --base origin/main` is the
same check locally; `uv run python -m tools.changelog preview` prints the
pending section.

The release cut, `uv run python -m tools.changelog release X.Y.Z --title "…"`,
folds all fragments under the new version heading — newest first within a
category, by the commit that added the fragment — bumps `pyproject.toml`,
`uv.lock` and `CITATION.cff`, and deletes the fragments. This README stays.
