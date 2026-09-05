---
name: open-pr
description: Take a finished change from diff to an open, green, review-clean PR — run the matching verify skills and the local CI gates first, then commit, push and open the PR, watch the pipeline AND the Copilot review, fix sensible findings and resolve the review threads. Never merges unless the user explicitly asks in this session. Use when asked to commit, push, open or create a PR, ship a change, or finish up a change.
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
git diff --name-only origin/main...
```

(`origin/main...`, not `main...`: the author merges PRs live, so the local
`main` is regularly behind and a stale base silently shrinks this list.)

| Diff touches | Run |
|---|---|
| `app/` | `/verify-frontend` (click through the changed flow, console, both viewports) |
| `api/` | `/verify-api` (endpoint sweep, admin gate) |
| `core/`, `tests/` | `/verify-core` (pytest + direct-invocation smoke) |
| `alembic/` | `/verify-migrations` (the shared DB must never meet an unverified revision — this runs BEFORE the push, not after) |
| `docs/`, `CLAUDE.md` | `/write-docs` checklist (index, sync duties) |
| `data/`, new binaries, license files | `/audit-licenses` |
| any code | `/simplify` (built-in Claude Code skill, not under `.claude/skills/`) for a quality pass when the change is non-trivial |

A `/verify-*` gate only counts if the **diff's own flow** was driven —
rendering a proxy or injecting state via the API is not verification
(see the changed-path rule in `/verify-frontend` §2).

**Glossary gate:** if the change COINS a new Fachbegriff, metric, named
failure mode or repo idiom — anything a reader will meet in the PR body,
a doc or the UI and could not resolve on their own — it adds the entry to
`docs/reference/glossar.md` (themed section + alphabetical Schnellindex)
in the same PR. Format and scope: `/write-docs` § „New terms go in the
glossary“.

**Changelog gate:** every PR adds ONE fragment, `changelog.d/<slug>.md`,
in the CHANGELOG's own format (`### Category` over bold-titled English
bullets matching the existing entries; `changelog.d/README.md`) — never
a bullet in `CHANGELOG.md` itself; the CI job „Changelog (fragment)"
refuses both a PR without a fragment and a bullet ADDED to `[Unreleased]`
(correcting the wording of one already there is fine — the bullet's bold
title is its identity). Run the same gate locally before the push:
`uv run python -m tools.changelog check --base origin/main`. Data-only
commits (chart sources, authored templates) are exempt; their provenance
lives in `SOURCE.md`.

**The PR number in the fragment is optional — do not go back for it.**
`tools.changelog` does not require a `(#NNN)`, and the number is not
knowable until the PR exists, so fetching it meant a second commit whose
whole content was one token. That step is retired: write the fragment
without a number and leave it. (Three agents in one day on 2026-09-02
reached for `sed -i` to make that one-token edit — the Edit/Write rule
has no "but it is only one word" clause, so the cheapest fix is not to
have the step.) What the gate DOES refuse is the placeholder left
standing: write no reference at all, never a bare `(#NNN)`. If a number
does go in — because a later push exists anyway and you want the
reference — it goes in with **Edit**, never `sed`, never a heredoc,
never `>>`.

Then the local CI equivalents — the same commands the pipeline runs,
without the round trip (backend always; frontend build only if `app/`
changed). **This is a hard gate, not a suggestion: do not open the PR
while any of these is red.** A pipeline that fails on pytest or ruff
after pushing means this step was skipped:

```bash
uv run --extra test pytest
uv run --extra dev ruff check . && uv run --extra dev ruff format --check .
cd app && npm run lint && npm run test && npm run build
```

(All three frontend commands, not just `build`: the CI „Frontend (build)"
job runs `npm ci` → `npm run lint` → `npm run test -- --coverage` →
`npm run build`. A red ESLint or a red Vitest passes a `build`-only check
locally and fails in Actions.)

(`--extra test` matters on a fresh venv: pytest and its async deps
live in the `test` extra, not in the default deps.)

After this gate, the Actions run should only ever fail for
environment reasons (cache, runner), never for code — step 3a then
becomes a formality.

## 2 · Open the PR

Never commit on `main` — branch first. Commit messages and PR
title/body are English (sprachregelung: GitHub-facing text; style per
sprachregelung.md §4 — Google developer documentation style guide as
the fallback, house rules win). Push is
the same in both environments:

```bash
git push -u origin <branch>
```

**A PR that finishes an issue closes it from the body** (author directive,
2026-08-16): put the closing keyword on its own line — `Fixes #N` (or
`Closes #N`) — so the merge closes the issue instead of leaving it for a
manual sweep. One line per issue; a PR that merely touches an issue
references it without the keyword.

Then open the PR (ready for review, not a draft):

- **Local:** `gh pr create --title "<english title>" --body "<what + why>"`
- **Cloud:** `mcp__github__create_pull_request` with
  `owner=MarkusNeusinger`, `repo=kurrentschrift`, `base=main`,
  `head=<branch>`, the English title/body, and `draft=false`.

**A multi-paragraph message or body goes through a file — and that file is
named after the branch.** `git commit -F` and `gh pr create --body-file` keep
the prose out of shell quoting, but the scratchpad is shared by every agent
of one session, so a generic `commitmsg.txt` / `prbody.md` is overwritten by
a parallel agent and a later re-read commits someone else's text (seen
2026-09-05). Derive the name, or take a private directory:

```bash
BRANCH=$(git branch --show-current)
MSG="$SCRATCH/commitmsg-$BRANCH.txt"    # or: D=$(mktemp -d) and write inside it
```

Write it with the Write tool, then `git commit -F "$MSG"` in the SAME step
that wrote it — never re-read one of these files a turn later to reuse it,
because between the two the file may belong to another agent. They are
scratch input to one command, not a record; the record is the commit.

## 3 · After opening: pipeline + Copilot loop (do not skip)

Repeat this loop until **both** hold: all checks pass *and* there are
zero unresolved review threads.

**a. Wait for the pipeline** (three jobs: `Backend (ruff + pytest)`,
`Migrations (alembic upgrade head)` — the upgrade + `alembic check` +
downgrade-roundtrip sequence against a throwaway Postgres; run
`/verify-migrations` locally BEFORE pushing any alembic diff — and
`Frontend (build)`):

- **Local:** `gh pr checks <num> --watch`.
- **Cloud:** `mcp__github__subscribe_pr_activity` for the PR and end
  the turn — CI results arrive as `<github-webhook-activity>` events.
  To inspect on demand use `mcp__github__actions_list` /
  `mcp__github__actions_get`; for a failed run pull
  `mcp__github__get_job_logs` (with `failed_only`).

If a check fails: read the run log, fix, push — the loop restarts.

**b. Wait for the Copilot review.** It arrives asynchronously a few
minutes after the PR is OPENED — not after each push; see „One review per
PR" below. The bot's login has two spellings and a filter that
knows only one will silently miss it: `copilot-pull-request-reviewer` in
`gh pr view --json reviews`, `copilot-pull-request-reviewer[bot]` in the
REST API and in `requested_reviewers`.

- **Local:** don't foreground-sleep and don't hand-poll — load the
  `Monitor` tool via ToolSearch and run an until-loop sized to the
  wait (~10 min upper bound — past that, tell the user instead of
  spinning) on:
  `gh pr view <num> --json reviews --jq '.reviews[] | "\(.author.login): \(.state)"'`
- **Cloud:** the same `mcp__github__subscribe_pr_activity`
  subscription delivers the review as a webhook event — don't poll. To force a fresh pass
  after a SUBSTANTIVE fix-push, call `mcp__github__request_copilot_review`; to
  read the current reviews use `mcp__github__pull_request_read`.

**Do not request a review after every push** (owner, 2026-08-23; PR #406
collected ~15 requests in a day). Each request re-reads the whole diff and
the bot then raises „previously missed" findings in files the push never
touched — a docstring fix draws a finding elsewhere, which draws a push,
which draws a request. Request only after a substantive change, and stop
once a round brings no new inline comments but only carried-over suppressed
items. Green plus no open threads = done; report that and let the owner merge.

**One review per PR is the normal case now.** The ruleset „Automated Copilot
Code Review" (kurrentschrift 18516317, anyplot 10370785) carries
`review_on_push: false` since 2026-09-03 — the owner asked for the churn to
stop, and the setting, not any skill, was what re-reviewed. Consequence for
this loop: a FIX push starts no new Copilot run, so a `copilot-*` check on
the new head SHA is legitimately ABSENT. Waiting for one that will never
come is the failure mode to avoid — see §3e for what to require instead.

**b2. Read the Codecov patch report** (arrives as a PR comment from the
`codecov` bot once the backend coverage upload lands; only the backend
uploads coverage):

```bash
gh pr view <num> --json comments --jq '.comments[] | select(.author.login | test("codecov"; "i")) | .body'
```

Judge it like a reviewer, not a hard gate: uncovered NEW logic that a
unit test can reach cheaply (pure helpers, calibration maths, edge
branches) gets a test in the same PR — extracting a pure core from an
async/DB wrapper to make it testable is the preferred move. Lines only
a live DB/HTTP flow exercises (routers, pooled caches, threadpool glue)
are the `/verify-api` sweep's job, not a unit test's — leave those, and
say so in the PR if the patch percentage looks alarming.

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

**Merging on request: wait for the review, not just for green** (lesson
from #504, 2026-09-03). Four conditions, all read on the CURRENT head SHA —
re-read it after every push, `gh pr view <num> --json headRefOid`:

1. A draft is not reviewable — `gh pr ready <num>` first. Copilot does
   not review a draft, so a draft merged "green" was never reviewed, and
   `gh pr merge` on a draft fails silently anyway. Check `isDraft`.
2. Every non-Copilot check on the head SHA is `completed` and green.
   Dedupe the check runs **by name, newest wins**: a superseded run (a
   label re-trigger, a cancelled first attempt) stays beside the current
   one and reads as a red check that is not there any more.
   ```bash
   gh api repos/MarkusNeusinger/kurrentschrift/commits/$(gh pr view <num> --json headRefOid --jq .headRefOid)/check-runs \
     --jq '[.check_runs[]] | group_by(.name) | map(max_by(.started_at)) | .[] | "\(.name): \(.status) \(.conclusion // "")"'
   ```
   (`gh pr checks --json` does not exist in this `gh`; the check-runs
   API is the way. Poll it with `Monitor`, never a foreground `sleep`.)
3. **A Copilot review actually exists on the PR** —
   `gh pr view <num> --json reviews`, author `copilot-pull-request-reviewer`.
   The head-SHA check run does not prove one: a run reaches `completed`
   with conclusion `cancelled` and delivers nothing (§3b's "silent" gotcha).
   So read the check run only to learn whether a round is still RUNNING —
   `queued`/`in_progress` means wait — and read the review list to learn
   whether one was ever delivered. Since `review_on_push` is off (§3b) the
   normal state after a fix push is no run on the head at all and the
   review from the first round standing; that is reviewed, not unreviewed.
   If no review exists and the run was cancelled, one re-request is the
   whole budget; after that report green-and-unreviewed and let the author
   decide, never loop.
4. Zero unresolved review threads (step c), outdated ones included.

**Merge state is two different fields; read each by its own name.**
`mergeable` (`gh pr view --json mergeable`) is `MERGEABLE`, `CONFLICTING`
or `UNKNOWN` — `UNKNOWN` right after another merge is GitHub still
computing, so keep polling. `mergeStateStatus` is the richer enum, where
the conflicting case is `DIRTY`. A conflict is not transient and has a
symptom worth knowing: GitHub starts no CI at all, so the PR shows no red
check, just none (#524 and anyplot #11212, 2026-09-04, both read as
"checks pending" for a while). Report it and merge `origin/main` into the
branch instead of waiting.

Poll all of this from ONE script in the scratchpad rather than by hand —
and kill a stale wait loop with the bracket trick (`pkill -f "x[.]y"`), or
`pkill` matches its own calling shell.

## 4 · After the merge: watch the deploy

Green CI does not mean a green deploy. **CI never imports `api/` or
`core/`**, so an import error ships green and only fails in the deploy's
`kurrentschrift-migrate` step — and a change to the image or its
dependencies (PR #473's two-stage Dockerfile is exactly that class) can
break a rollout that every check approved.

Which trigger fires for which path: `api/**`, `core/**`, `alembic/**`,
`pyproject.toml` → the API build (`api/cloudbuild.yaml`); `app/**` → the
app build. Both build in `europe-west4`.

```bash
gcloud builds list --region=europe-west4 --limit 3 \
  --format='table(id,status,createTime,substitutions.TRIGGER_NAME,substitutions.SHORT_SHA)'
gcloud builds log --region=europe-west4 <id>      # only when one is red
```

**`--region` is load-bearing.** Without it the call lists the global
region, which here holds only months-old builds — it reads exactly like
"nothing was triggered" and has been misread that way before.

These are reads against the production project, which CLAUDE.md's
prod-touching rule covers: **name the command and ask in-session before
running it**, or simply hand the author the two lines to run. Never
`gcloud run deploy`, never a rollback, from this skill.

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
- **A fix push no longer starts a review round.** `review_on_push` is
  `false` since 2026-09-03 (§3b), so only an explicit — and substantive —
  re-request opens another round. When one does run, a fix-push round can
  raise new threads on the changed lines; that is the loop working, not
  noise, but don't chase it more than a couple of rounds for cosmetic
  nits and surface stalemates to the user.
- **Copilot runs can die silently.** The
  `copilot-pull-request-reviewer` check can end `cancelled` without
  delivering a review, and a re-request may spawn no new run at all
  (PR #400, 2026-08-21: cancelled after 20 min, the re-request stayed
  silent). Re-request exactly ONCE; if that also delivers nothing,
  report the PR as green and review-clean by absence — never loop
  requests waiting for a review that is not coming.
- **Never pipe a gate command** — without `set -o pipefail` a pipeline
  reports the LAST command's exit status, so
  `ruff format --check | tail -1` let an unformatted file reach a
  pushed commit (2026-08-14; the fix cost a force-push). Run gates
  bare and trim their output only after the exit code is captured —
  or enable `pipefail` explicitly if a pipe is unavoidable.
- **Local gates first saves whole round trips** — the pipeline runs
  the same checks (pytest + ruff under a
  `uv sync --extra dev --extra test --frozen` env, then `npm ci` +
  `npm run lint` + `npm run test -- --coverage` + `npm run build`);
  anything red locally is guaranteed red in Actions.

## Troubleshooting

- Resolve mutation returns `NOT_FOUND: Could not resolve to a node` →
  the thread id is stale (e.g. PR state changed since the query) —
  re-run the thread query from step c and retry with the fresh id.
