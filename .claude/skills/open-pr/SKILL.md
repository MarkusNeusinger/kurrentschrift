---
name: open-pr
description: Take a finished change from diff to an open, green, review-clean PR — run the matching verify skills and the local CI gates first, then commit, push and open the PR, watch the pipeline AND the Copilot review, fix sensible findings and resolve the review threads. Never merges unless the user explicitly asks in this session. Use when asked to open or create a PR, ship a change, or finish up a change.
---

# Open a PR (ship a change)

From working tree to an open PR that is green and review-clean. The
end state is **an open PR, not a merged one** — the user merges
themselves; merge only on an explicit request, and re-check the live
PR state first (it may already be merged).

## 1 · Pre-PR gates (pick by what the diff touches)

```bash
git diff --name-only main...
```

| Diff touches | Run |
|---|---|
| `app/` | `/verify-frontend` (click through the changed flow, console, both viewports) |
| `api/` | `/verify-api` (endpoint sweep, admin gate) |
| `core/`, `tests/` | `/verify-core` (pytest + direct-invocation smoke) |
| `docs/`, `CLAUDE.md` | `/write-docs` checklist (index, sync duties) |
| `data/`, new binaries, license files | `/audit-licenses` |
| any code | `/simplify` (built-in Claude Code skill, not under `.claude/skills/`) for a quality pass when the change is non-trivial |

A `/verify-*` gate only counts if the **diff's own flow** was driven —
rendering a proxy or injecting state via the API is not verification
(see the changed-path rule in `/verify-frontend` §2).

Then the local CI equivalents — the same commands the pipeline runs,
without the round trip (backend always; frontend build only if `app/`
changed). **This is a hard gate, not a suggestion: do not open the PR
while any of these is red.** A pipeline that fails on pytest or ruff
after pushing means this step was skipped:

```bash
uv run --extra test pytest
uv run --extra dev ruff check . && uv run --extra dev ruff format --check .
cd app && npm run build
```

(`--extra test` matters on a fresh venv: pytest and its async deps
live in the `test` extra, not in the default deps.)

After this gate, the Actions run should only ever fail for
environment reasons (cache, runner), never for code — step 3a then
becomes a formality.

## 2 · Open the PR

Never commit on `main` — branch first. Commit messages and PR
title/body are English (sprachregelung: GitHub-facing text). Then:

```bash
git push -u origin <branch>
gh pr create --title "<english title>" --body "<what + why>"
```

## 3 · After opening: pipeline + Copilot loop (do not skip)

Repeat this loop until **both** hold: all checks pass *and* there are
zero unresolved review threads.

**a. Wait for the pipeline** (the two jobs are named
`Backend (ruff + pytest)` and `Frontend (build)`):

```bash
gh pr checks <num> --watch
```

If a check fails: read the run log, fix, push — the loop restarts.

**b. Wait for the Copilot review.** It arrives asynchronously a few
minutes after push; the bot's login is exactly
`copilot-pull-request-reviewer`. Don't foreground-sleep and don't
hand-poll: load the `Monitor` tool via ToolSearch and run an
until-loop sized to the wait (~10 min upper bound — past that, tell
the user instead of spinning) on this check:

```bash
gh pr view <num> --json reviews --jq '.reviews[] | "\(.author.login): \(.state)"'
```

**c. List unresolved threads** (id is needed for resolving):

```bash
gh api graphql -f query='query($owner:String!,$repo:String!,$pr:Int!){repository(owner:$owner,name:$repo){pullRequest(number:$pr){reviewThreads(first:50){nodes{id isResolved isOutdated path comments(first:3){nodes{author{login} body}}}}}}}' -F owner=MarkusNeusinger -F repo=kurrentschrift -F pr=<num> --jq '.data.repository.pullRequest.reviewThreads.nodes | map(select(.isResolved | not))'
```

**d. Per unresolved thread, judge — then act:**

- **Sensible finding** → fix it, commit, push (CI + possibly a new
  Copilot round restart the loop).
- **Not sensible / false positive** → reply on the PR with one
  sentence of reasoning (a normal `gh pr comment` referencing the
  file is fine).
- Either way, **resolve the thread** so the PR ends review-clean:

```bash
gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -F id=<thread-id>
```

**e. Stop condition.** Checks green, zero unresolved threads → report
the PR URL and the final state. **Do not merge.** If the user asks to
merge, first re-fetch (`gh pr view <num> --json state,mergeStateStatus`)
— the user merges live and the PR may already be gone.

## Gotchas

- **`isOutdated` ≠ `isResolved`.** A force-push or fix can outdate a
  Copilot thread while it stays unresolved (seen on PR 54: a thread
  with `isOutdated: true, isResolved: false`). Outdated threads still
  count against review-clean — resolve them explicitly.
- **The user merges PRs live.** Between loop rounds, re-fetch PR and
  branch state before pushing or resolving — the base may have moved
  or the PR may be merged mid-loop.
- **Stacked PRs die when their base merges.** A live squash-merge of
  the base PR auto-closes dependent PRs and reopening fails — open a
  fresh PR from the same head instead, retarget to `main`, and clear
  the duplicated base diff via `git merge origin/main` resolved with
  `--ours`.
- **Copilot reviews every push round.** A fix-push can spawn new
  threads on the changed lines; that's the loop working, not noise —
  but don't chase it more than a couple of rounds for cosmetic nits;
  surface stalemates to the user.
- **Local gates first saves whole round trips** — the pipeline runs
  the same checks (pytest + ruff under a
  `uv sync --extra dev --extra test --frozen` env, `npm ci` +
  `npm run build`); anything red locally is guaranteed red in Actions.

## Troubleshooting

- Resolve mutation returns `NOT_FOUND: Could not resolve to a node` →
  the thread id is stale (e.g. PR state changed since the query) —
  re-run the thread query from step c and retry with the fresh id.
