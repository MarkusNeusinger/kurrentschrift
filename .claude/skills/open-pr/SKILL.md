---
name: open-pr
description: Take a finished change from diff to an open, green, review-clean PR — run the matching verify skills and the local CI gates first, then commit, push and open the PR, watch the pipeline AND the Copilot review, fix sensible findings and resolve the review threads. Never merges unless the user explicitly asks in this session. Use when asked to open or create a PR, ship a change, or finish up a change.
---

# Open a PR (ship a change)

From working tree to an open PR that is green and review-clean. The
end state is **an open PR, not a merged one** — the user merges
themselves; merge only on an explicit request, and re-check the live
PR state first (it may already be merged).

## 0 · Pick the GitHub interface (local vs. cloud)

This skill runs in two environments and the GitHub tooling differs.
Detect once, up front:

```bash
command -v gh >/dev/null && echo "gh path (local)" || echo "MCP path (cloud/web)"
```

- **`gh` present (local machine):** use the `gh`/`gh api` commands as
  written below.
- **`gh` absent (Claude Code on the web / remote container):** `gh`,
  `hub` and direct GitHub API access do **not** exist here. Use the
  GitHub MCP tools (`mcp__github__*`) instead. They are deferred —
  load each one's schema via `ToolSearch` with its **fully-qualified**
  name (the bare method name silently matches nothing), e.g.
  `select:mcp__github__create_pull_request,mcp__github__pull_request_read,mcp__github__resolve_review_thread`,
  before the first call.

`git` itself (commit / `push` / `fetch`) is identical in both — only
the PR/review/CI steps swap. Every step below gives both paths; the
mapping:

| Step | `gh` (local) | GitHub MCP (cloud/web) |
|---|---|---|
| Create PR | `gh pr create` | `mcp__github__create_pull_request` (ready for review, not draft) |
| List PRs | `gh pr list` | `mcp__github__list_pull_requests` |
| Read PR / reviews | `gh pr view --json …` | `mcp__github__pull_request_read` |
| Watch CI | `gh pr checks --watch` | `mcp__github__actions_list` / `mcp__github__actions_get` / `mcp__github__get_job_logs` (+ `mcp__github__subscribe_pr_activity` to be woken on results) |
| List review threads | `gh api graphql … reviewThreads` | `mcp__github__pull_request_read` (review-threads method) |
| Reply on a thread | `gh pr comment` | `mcp__github__add_reply_to_pull_request_comment` (thread) / `mcp__github__add_issue_comment` (PR-level) |
| Resolve a thread | `gh api graphql … resolveReviewThread` | `mcp__github__resolve_review_thread` |
| Request Copilot review | (auto / `gh`) | `mcp__github__request_copilot_review` |
| Merge (only if asked) | `gh pr merge` | `mcp__github__merge_pull_request` |

In the cloud, prefer `mcp__github__subscribe_pr_activity` over any
polling loop: CI/review events wake the session as
`<github-webhook-activity>` messages — never `sleep`-poll or
foreground-`Monitor` there.

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

**Changelog gate:** every PR adds its entries to `CHANGELOG.md` under
`[Unreleased]` (Keep-a-Changelog categories, English, bold-titled
bullets matching the existing entries) before the PR opens — that file
is how releases get posted. Data-only commits (chart sources, authored
templates) are exempt; their provenance lives in `SOURCE.md`.

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
title/body are English (sprachregelung: GitHub-facing text). Push is
the same in both environments:

```bash
git push -u origin <branch>
```

Then open the PR (ready for review, not a draft):

- **Local:** `gh pr create --title "<english title>" --body "<what + why>"`
- **Cloud:** `mcp__github__create_pull_request` with
  `owner=MarkusNeusinger`, `repo=kurrentschrift`, `base=main`,
  `head=<branch>`, the English title/body, and `draft=false`.

## 3 · After opening: pipeline + Copilot loop (do not skip)

Repeat this loop until **both** hold: all checks pass *and* there are
zero unresolved review threads.

**a. Wait for the pipeline** (the two jobs are named
`Backend (ruff + pytest)` and `Frontend (build)`):

- **Local:** `gh pr checks <num> --watch`.
- **Cloud:** `mcp__github__subscribe_pr_activity` for the PR and end
  the turn — CI results arrive as `<github-webhook-activity>` events.
  To inspect on demand use `mcp__github__actions_list` /
  `mcp__github__actions_get`; for a failed run pull
  `mcp__github__get_job_logs` (with `failed_only`).

If a check fails: read the run log, fix, push — the loop restarts.

**b. Wait for the Copilot review.** It arrives asynchronously a few
minutes after push; the bot's login is exactly
`copilot-pull-request-reviewer`.

- **Local:** don't foreground-sleep and don't hand-poll — load the
  `Monitor` tool via ToolSearch and run an until-loop sized to the
  wait (~10 min upper bound — past that, tell the user instead of
  spinning) on:
  `gh pr view <num> --json reviews --jq '.reviews[] | "\(.author.login): \(.state)"'`
- **Cloud:** the same `mcp__github__subscribe_pr_activity`
  subscription delivers the review as a webhook event — don't poll. To force a fresh pass
  after a fix-push, call `mcp__github__request_copilot_review`; to
  read the current reviews use `mcp__github__pull_request_read`.

**c. List unresolved threads** (id is needed for resolving):

- **Local:**
  ```bash
  gh api graphql -f query='query($owner:String!,$repo:String!,$pr:Int!){repository(owner:$owner,name:$repo){pullRequest(number:$pr){reviewThreads(first:50){nodes{id isResolved isOutdated path comments(first:3){nodes{author{login} body}}}}}}}' -F owner=MarkusNeusinger -F repo=kurrentschrift -F pr=<num> --jq '.data.repository.pullRequest.reviewThreads.nodes | map(select(.isResolved | not))'
  ```
- **Cloud:** `mcp__github__pull_request_read` with its review-threads
  method (`owner=MarkusNeusinger`, `repo=kurrentschrift`,
  `pullNumber=<num>`); filter to threads where `isResolved` is false.

**d. Per unresolved thread, judge — then act:**

- **Sensible finding** → fix it, commit, push (CI + possibly a new
  Copilot round restart the loop).
- **Not sensible / false positive** → reply on the PR with one
  sentence of reasoning. Local: a normal `gh pr comment` referencing
  the file. Cloud: `mcp__github__add_reply_to_pull_request_comment`
  (on the thread) or `mcp__github__add_issue_comment` (PR-level).
- Either way, **resolve the thread** so the PR ends review-clean:
  - **Local:**
    ```bash
    gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -F id=<thread-id>
    ```
  - **Cloud:** `mcp__github__resolve_review_thread` with the thread id
    from step c.

**e. Stop condition.** Checks green, zero unresolved threads → report
the PR URL and the final state. **Do not merge.** If the user asks to
merge, first re-fetch the live state — local
`gh pr view <num> --json state,mergeStateStatus`, cloud
`mcp__github__pull_request_read` — the user merges live and the PR may
already be gone.

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
