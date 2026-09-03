# Guardrails — the long version

`CLAUDE.md` states each working guardrail as one line: the rule, its shortest
reason, its date. This file holds what does not fit there — the incident that
produced the rule, the recipe it implies, the numbers that make it credible.

The split exists because `CLAUDE.md` is loaded into **every** session, so its
cost is paid on every turn, while a retro narrative is needed only when
someone actually hits the situation. Nothing here is a new rule. If this file
and `CLAUDE.md` ever disagree, `CLAUDE.md` is the rule and this is the
commentary that fell behind.

Sections are in the order of the guardrail list.

---

## Fixes #N in the PR body

Author directive, 2026-08-16, prompted by PR #377 / issue #289.

The author merges live and does not want to close the matching issue by hand
after every merge. A closing keyword — `Fixes #N` or `Closes #N` — has to
stand in the PR body or in a commit message on the default branch; a bare
mention ("see #N") closes nothing and the connection is lost. Put it on its
own line near the top of the body, one line per issue.

## Carry a good solution to the sibling repo

Author directive, 2026-09-01, during the API image slimming.

kurrentschrift and anyplot share stack, deploy pattern and cloud account.
Every asymmetry between them is a defect that gets noticed exactly once and
then rots in whichever repo is weaker. The find that day: kurrentschrift's
Cloud Build deploy had `--no-traffic` + smoke + `update-traffic`, anyplot
deployed straight onto traffic — the same Dockerfile change was needlessly
riskier there.

Transfer in the same round, not as a note for later. One PR per repo, each
following its own conventions: here a `changelog.d/<slug>.md` fragment, there
a bullet under `[Unreleased]`. It holds in both directions — anyplot is the
reference for stack and deploy patterns.

## Use an asymmetric finding, don't discard it

Author directive, 2026-08-26, quoting the author: the more lopsided the ratio
of better to worse, the more important it is to try to USE the finding.

Chain v5 that day: Soll distance 125 → 79, **32 words better, 2 worse**, at
the price of 36 aiou losers. "Discard" was the wrong first reaction. A 32:2 on
one axis is not noise, it is a mechanism doing something real; the price on
the other axis is a SEPARATION task, not a rejection reason. The gates stay
immovable — they say "not like this", not "not at all".

How that case actually resolved: the 36 losers were a BASE artefact. v5 had
been measured against the follower without the structure guard instead of
against the pre-registered Soll stack. Against the correct base: zero losers,
aiou +0.039 median. A second opinion found it. Since then `k0eval` warns when
the two files carry different stacks and reports `guard_outcome` per word.

So, in order: verify base and arm are the same stack but for the ONE
registered knob (`k0eval` prints it; on a warning, interpret nothing and fix
the base first). Then decompose the losers into classes — do the winning axis
and the losing axis even move together? In the v5 case 8 words lost ink with
structure UNCHANGED, which is a pure defect, not a trade. Then pre-register a
rescue path per class. Partial adoption is legitimate. Discard only once the
rescue paths themselves have been measured and failed, and get a second
opinion before booking any asymmetric result as a negative.

## The author authors in the PROD admin

Author's working habit, recorded 2026-07-25.

The author traces glyphs in the DEPLOYED admin, not on a local dev server.
Two consequences.

First, a UI bug report is against `origin/main`, which can be AHEAD of the
branch you are on. On 2026-07-25 two wizard bugs were unreproducible in the
checkout because their cause — PR #230's `commitThenClear` — existed only on
`origin/main`, 13 commits ahead. Before diagnosing an admin-UI report:
`git fetch && git log --oneline main..origin/main`, and cut the fix branch
from `origin/main`.

Second, the report may simply be a stale tab: the admin tab stays open across
deploys and the SPA keeps its old bundle and its old fetched data until a
manual reload. On 2026-06-10 two of five bug reports were already fixed in
repo, DB and the served bundle. Verify what production actually serves —
`curl -s https://kurrentschrift.ink/ | grep -o 'assets/[^"]*\.js'` and grep
the bundle for the disputed string — before changing code. If prod is
current, the answer is "reload the tab".

And never unlock or modify the author's authored glyphs for testing; he works
the same shared DB in parallel.

## Changelog fragments

`changelog.d/<slug>.md` per PR, never a bullet in `CHANGELOG.md`.

`[Unreleased]` in `CHANGELOG.md` is one shared spot, and before the fragments
existed every sibling merge conflicted there (audit series 2026-08-29/30).
The union merge driver healed only the local rebase — GitHub's own
mergeability check ignores it — so the conflict still blocked merges. Since
2026-08-30 the CI job „Changelog (fragment)" refuses both a PR without a
fragment and a bullet written into `[Unreleased]` directly.

Exempt: data-only commits (their provenance lives in `SOURCE.md`), a PR
labelled `skip-changelog`, and Dependabot's own PRs — a bot writes neither
fragment nor label, and its routine bumps are what release notes leave out
anyway (#468, 2026-08-31).

The union merge driver on `CHANGELOG.md` stays as the net under the release
cut itself, which is the one PR that does rewrite the file.

## Don't re-request a Copilot review after every push

Author, 2026-08-23. PR #406 collected roughly 15 review requests in one day.

Each request is a full re-read of the whole diff, and the bot then surfaces
"previously missed" findings in files the push never touched. A one-line
docstring fix draws a finding somewhere else, which draws another push, which
draws another request. Request a fresh review only after a SUBSTANTIVE change
— new behaviour, a reworked mechanism — and stop once a round yields no new
inline comments but only carried-over suppressed items: the field is grazed.
A PR that is green with no open threads needs no further round; say so and
let the author merge.

## Archive snapshots: create freely, never destroy

Author directive, 2026-08-08, for `tools/dbsnapshot`.

The archive holds the only copy of what no recomputation brings back —
`bboxes` and `templates.raw_path`. Cloud SQL's own backups are instance-wide
and keep 7 days; this project's failure mode is slower, a bad apply noticed
weeks later, and that is what the archive covers.

- Take one freely, and DO take one **before** anything that can overwrite
  geometry: `apply-laufform`, a migration with DROP or a rewrite, a harvest
  with `replace`, any DDL — and after an authoring session in which letters
  were traced.
- Every snapshot is a new timestamped directory. Never write into an existing
  one, never delete, move or rename one — not to tidy up, not when disk is
  short. Report instead of acting. The archive lives OUTSIDE the working tree
  precisely because `git clean -xfd` deletes gitignored files.
- Check plausibility before filing (row counts per table; the tool already
  fails a run that would file fewer rows than the previous one). A silent
  empty snapshot is worse than none, because it looks like safety.
- Never print archive contents into the transcript — that is the reserved
  dataset.
- Restoring is prod-touching and needs the author's say-so in the same
  session. `restore.py` is built for drills against a throwaway PostgreSQL:
  it refuses a URL equal to `DATABASE_URL`, refuses an occupied target
  without `--replace`, and writes nothing without `--apply`.

Operating detail and the full rule set: `/dbsnapshot`.

## Edit repo files with Edit/Write, never heredocs or sed

Appending with `>>` counts. On 2026-08-21 a `qualitaetsmetrik.md` §14 entry
went in via `cat >>` — appending at the end of a file is exactly the forbidden
path, however little it "feels" like editing.

When a Bash command legitimately mutates a tracked file (a formatter, codegen,
`git checkout`), read the file again before the next edit; stale-state errors
cascade otherwise.

The moment this rule gets broken is when an edit ANCHOR fails — "string not
found", "file modified since read". The answer is a fresh targeted read plus a
longer anchor, never a python-heredoc regex rewrite. That is precisely how
about 15 heredoc writes crept into `glossar.md`, `CHANGELOG.md` and
`qualitaetsmetrik.md` (retro of 2026-08-14).

## Manual author tasks go to Todoist

Author directive, 2026-08-07.

Whenever a session identifies a step only the human can or should do — a
wizard re-trace, a rendering-affecting DB apply that needs a go, a decision on
a bulk re-derive — create a task in the author's Todoist project
**kurrentschrift** naming the concrete action and its context, instead of
leaving it buried in a chat reply. Korb rows still carry the protocol; the
Todoist task is the actionable pointer.

## The perfect result, not the fast one

Author directive, 2026-08-05, from the ceiling question of the
writing-systems research note.

When a cheap symptomatic fix and a correct structural fix compete, take the
structural one — even when it looks like a regression at first. Concretely:
fix the model, the objective or the rule; never mute the alarm. Measure with a
pre-registered A/B against ground truth (the measured ink) before adopting. An
honest negative result that redirects the work is a valid outcome. CPU time on
offline measurement runs is not a reason to cut a corner.

## Every rejected measure names its rescue paths

Author directive, 2026-08-16.

A `qualitaetsmetrik.md` §14 entry that closes as an honest negative ends with
the named ways the goal could still be reached: a new mechanism, new evidence,
a new sensor — each with a fresh pre-registration. Never the same knob re-run
with softer gates. The standing table in `docs/proposals/tintenfolger.md` §7.9
gets its row in the same PR.

## The author merges PRs live

Seen twice on 2026-08-16: a squash-merge can race your last pushes.

Announce "green and review-clean" and prefer waiting for the merge before
pushing more. After a race, recover by cutting a fresh branch from the merged
`main` and cherry-picking exactly the missing commits — never re-push the
stale branch.

## Restarting a mandated branch after its squash-merge

For the case where force-push is blocked (cloud auto-mode classifier,
2026-08-21).

`git checkout -B <branch> origin/main`, work, and at the FIRST push integrate
the stale remote tip via a content-neutral merge — its content is already
inside the squash. The recipe is strict because `git add -A` during an
unresolved merge commits conflict markers, which happened once:

1. Resolve EVERY conflicted file with `git checkout --ours`.
2. Require `git diff --name-only --diff-filter=U` to come back empty.
3. Grep the tree for conflict markers (the seven-fold `<`; spelled out here it
   would make this file a permanent false positive of its own check).
4. Require `git diff ORIG_HEAD HEAD` to be EMPTY before committing.
   `ORIG_HEAD` is the pre-merge head, set by `git merge` itself.

Only then push normally.

## Delegated agents run on Opus by default

Author directive, 2026-08-11, refined 2026-08-16.

Pass `model: opus` when spawning subagents or workflows. Escalate to Fable for
genuinely hard tasks that need deep reasoning, drop to Sonnet for simple
mechanical grinding — but in most cases Opus is the right tier.

Escalation is for WEICHENSTELLUNGEN, not for every detail. Within its briefed
scope a delegate decides routine matters itself and documents them; otherwise
delegation gains nothing. What comes BACK to the main loop, which keeps the
overview, are genuine judgment calls: anything that changes scope, contradicts
the brief or the docs, touches a frozen ruler or a pre-registration, or would
be expensive to redo. Prompts to delegated agents state this split explicitly
— decide-and-document versus return-as-finding.

## Pin BLAS threads for solver measurement runs

Finding of 2026-08-16, recorded in `docs/reference/qualitaetsmetrik.md` §14
under „Wächter als Produktions-Kette".

The chain solve is not bit-reproducible across thread environments, so
cross-run comparisons are only valid within one pinned setting. Prefix the
run with `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`. Pinning also collapses
the runtime: a 63-word chain went from 87 minutes to 2.7.

The executable form of this is step 2 of `/verify-trace`.
