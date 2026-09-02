---
name: dependabot
description: Work through the open Dependabot PRs — check each one's state, judge a red or breaking bump, and avoid the two quirks that permanently break a bot branch (never update-branch a Dependabot PR; recover a poisoned head by approving its gated runs). Use when asked to handle, review, process or merge the Dependabot PRs, the dependency bumps, or the weekly dependency batch.
---

# Work through the Dependabot PRs

Three ecosystems open PRs weekly (`.github/dependabot.yml`): `uv` at the
repo root, `npm` in `/app`, and `github-actions`. Bumps are grouped
(`python-minor`, `npm-minor`, `react`, `mui`, `actions`), so a group is ONE
PR — treat it like any other PR, not like a batch.

**Dependabot PRs carry no changelog fragment and need none.** The CI job
„Changelog (fragment)" skips them by author (`ci.yml`: the check is
conditional on the PR author not being `dependabot[bot]`, #469) — a bot
writes neither fragment nor label, and routine bumps are exactly what the
release notes leave out anyway. They are summarised at release time instead.

**Copilot never reviews a Dependabot PR.** Don't wait for a review that will
not arrive.

## 1 · List the batch

```bash
git fetch origin
gh pr list --repo MarkusNeusinger/kurrentschrift --author "app/dependabot" \
  --json number,title,mergeStateStatus,statusCheckRollup
```

`mergeStateStatus` is computed asynchronously — a fresh `UNKNOWN` means "ask
again in a few seconds", not "blocked". Let it settle before judging.

## 2 · Per PR, judge — never bulk-anything

- **Checks green** → report it as ready. Whether it merges, and whether
  auto-merge (`gh pr merge <num> --auto --squash`; the repo allows it) is
  used, is the **author's call** — CLAUDE.md's "never merge a PR yourself"
  covers bot PRs too. Ask in-session rather than assuming.
- **Checks pending on an up-to-date branch** → nothing to do; they will
  report.
- **Checks red** → this is the actual work. A bump that breaks a build or a
  test usually changed an export or a config shape; read the failing job log
  and the library's own changelog for the version in question, then fix it
  on the Dependabot branch or flag the PR for manual handling. Do not
  disable the failing check.

## 3 · The two quirks that cost real time

- **A `BEHIND` branch is fine — leave it alone.** BEHIND does not block the
  merge here. **Never** run
  `gh api -X PUT repos/{owner}/{repo}/pulls/<num>/update-branch` on a
  Dependabot PR: the merge commit it creates is authored by
  `github-actions[bot]`, GitHub then gates that head's workflow runs behind
  manual approval (`action_required`, so the required checks never report),
  and Dependabot permanently stops rebasing a branch once a foreign commit
  lands on it. In the sibling repo one such update burned 174 workflow runs
  in 22 hours.
- **Already poisoned** (head commit authored by `github-actions[bot]`,
  checks stuck at `action_required`): approve the gated runs once —
  `gh api -X POST repos/{owner}/{repo}/actions/runs/<id>/approve`. Approved
  runs do report their contexts on a bot-authored head. `@dependabot
  recreate` also works and restores a clean `dependabot[bot]` head, but it
  re-resolves the versions.

## 4 · Stop cleanly

When every PR has an end state, **stop — do not leave a background monitor
running.** An orphaned monitor fires notifications into later sessions.

Report per PR: number, title, state, action taken or recommended, and for
anything red the reason.
