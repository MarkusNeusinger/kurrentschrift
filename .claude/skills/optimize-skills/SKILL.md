---
name: optimize-skills
description: Mine past Claude Code session transcripts for recurring friction — problems the user had to find manually, corrections, repeated tool errors, hand-rolled loops — and turn the patterns into skill gotchas, memory entries, or CLAUDE.md rules. Use when asked to optimize the skills, run a retro, review past sessions, or find recurring problems.
---

# Session retro: mine friction, improve the loops

Past sessions are data. This skill extracts friction signals from the
transcript JSONL files and converts recurring patterns into fixes in
the right place: a gotcha in an existing skill, a memory entry, or a
CLAUDE.md rule. Transcripts live under `~/.claude/projects/<slug>/`,
where the slug is the absolute repo path with `/` replaced by `-` —
derive it from the working directory instead of hardcoding a
machine-specific path. The files are megabytes — **never read them
raw**, always extract with jq.

## 1 · Extract (per transcript)

```bash
ls -S ~/.claude/projects/$(pwd | tr '/' '-')/*.jsonl
```

Four extractors, each verified against real transcripts. `FILE` is one
transcript path:

**User texts** — the user's own words: bug reports the assistant
missed, corrections, re-instructions:

```bash
jq -r 'select(.type=="user") | .message.content | if type=="string" then . elif type=="array" then (map(select(.type=="text") | .text) | join(" ")) else empty end' FILE | grep -v '^$' | grep -v '^<' | head -80
```

**Tool errors**, deduplicated by class:

```bash
jq -r 'select(.type=="user") | .message.content[]? | select(type=="object" and .type=="tool_result" and .is_error==true) | .content | if type=="string" then . elif type=="array" then (map(.text? // empty) | join(" ")) else empty end' FILE | cut -c1-200 | sort | uniq -c | sort -rn | head -20
```

**Interruptions** (user broke in mid-action):

```bash
grep -c 'Request interrupted by user' FILE
```

**Command repetition** (hand-rolled loops a skill should own):

```bash
jq -r 'select(.type=="assistant") | .message.content[]? | select(type=="object" and .type=="tool_use" and .name=="Bash") | .input.command' FILE | awk '{print $1, $2}' | sort | uniq -c | sort -rn | head -10
```

## 2 · Judge into categories

- **undetected-problem** — the user reports something broken that the
  assistant did not catch itself (found via manual testing, a
  printout, a live click). The most valuable signal: each one means a
  verification loop has a hole.
- **user-correction** — the user redirects („nein", „nicht so",
  switching tool/approach).
- **recurring-tool-error** — same error class ≥ 3× (staleness
  cascades, permission denials, missing flags).
- **manual-repetition** — the same command sequence run many times
  (e.g. dozens of tsc/build/push cycles = the loop belongs in a skill).
- **workflow-friction** — anything else that cost a round trip
  (blocked sleeps, stalled background waits, harness denials).

Ignore: routine output, system reminders, skill texts pasted into user
messages, one-off typos.

## 3 · Scale: fan out for many sessions

For 1–2 transcripts, run the extractors inline. For more, use a
Workflow: one mining agent per transcript (each runs the §1 extractors
and returns structured findings), then a single synthesis agent that
clusters across sessions, ranks by `sessions × frequency`, and —
**after reading the current skill files** — proposes only fixes that
aren't already documented. First run (2026-06-10): 13 sessions →
84 raw findings → 10 patterns.

## 4 · Convert patterns into fixes

Route each accepted pattern to where it prevents the recurrence:

- behaviour during verification → a **gotcha/step in the matching
  `verify-*` / `open-pr` / `write-docs` skill**
- environment/infra knowledge → a **memory entry** (update existing
  files before creating new ones)
- session-spanning working rules → **CLAUDE.md** (mirror in
  copilot-instructions only if it's a domain rule, not a
  Claude-harness rule)

Apply small, low-risk fixes (gotchas, memory) directly and list them;
anything touching settings, plugins, or new repo code is a
recommendation for the user, not a unilateral change.

## Gotchas

- **Workflow `args` can arrive undefined** — inline the transcript
  file list in the script body instead of passing it via `args` (a
  run failed exactly this way on the first attempt).
- **`.message.content` is string OR array** depending on entry type —
  both extractor branches are needed, otherwise jq silently drops
  half the messages.
- **User-text extraction picks up pasted skill instructions** and
  command output; the `grep -v '^<'` filter drops system-reminder
  blocks, the rest needs judgment in §2.
- **Transcripts may contain secrets** (env output, tokens). Findings
  quote error *classes*, never raw transcript lines with values, and
  nothing from a transcript gets committed verbatim.
- **The current session is in the list** — including it is fine (its
  friction is the freshest), but its file keeps growing while you
  mine; frequencies for it are a snapshot.

## Troubleshooting

- jq prints nothing for a file that clearly has content → you are
  filtering on the wrong `.type`; inspect first:
  `jq -r '.type' FILE | sort | uniq -c`.
