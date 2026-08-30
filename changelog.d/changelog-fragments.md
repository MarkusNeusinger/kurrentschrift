### Added

- **Changelog fragments: one file per PR under `changelog.d/`, folded in at
  the release cut (`tools/changelog`).** Every PR used to add its bullets
  under `[Unreleased]` of the one shared file, and every sibling merge
  conflicted the others exactly there — the union merge driver of #461
  heals the local rebase, but GitHub's mergeability check ignores it, and a
  branch that moves changelog lines came out of the rebase duplicated. Now a
  PR adds `changelog.d/<slug>.md` in the changelog's own format
  (`### Category` over bold-titled bullets) and touches nothing else. The
  new CI job „Changelog (fragment)" runs
  `uv run python -m tools.changelog check --base origin/main`: a fragment
  per PR except data-only PRs and the `skip-changelog` label, and no bullet
  written into `[Unreleased]` directly; `preview` prints the pending
  section; `release X.Y.Z --title …` folds the fragments (newest first
  within a category, by the commit that added them) plus whatever
  `[Unreleased]` still holds under the new heading, bumps `pyproject.toml`,
  `uv.lock` and `CITATION.cff` and deletes the fragments — the cut the
  header used to describe as hand steps. Standard library only, pinned by
  `tests/test_changelog_tool.py` including the gate against a throwaway git
  repository; the union driver stays as the net under the cut PR itself
  (#462).
