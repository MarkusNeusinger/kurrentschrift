---
name: verify-trace
description: Run one round of the Tintenfolger word-tracing measurement — fixture acceptance, the follower run with BLAS threads pinned, dev-19 scoring against the base report, the reference-free k0 protocol, sensors — and file the results where the doctrine requires (a §14 entry, the Verfahren ledger line, and a §7.9 rescue-path row on a negative). Use when asked to run a Tintenfolger round, measure a follower arm, score a candidate against the base, run tracebench or pairlab.follow, or pre-register a tracing experiment.
---

# Run a Tintenfolger round (the standing measurement liturgy)

The word-tracing duel (`docs/proposals/tintenfolger.md`; numbers and
pre-registrations in `docs/reference/qualitaetsmetrik.md` §14) has a
five-step liturgy that `werkzeuge.md` records and that §14 entries have
followed since `aug19`. It is the most error-prone standing procedure in the
repo — twice in two days (`aug25` L-U, `aug26` v5) a round was measured
against the WRONG follower — and this skill exists so the steps come from a
checklist instead of from memory.

This is measurement only: no DB writes, no `core/` edits, no rendering
changes. Frozen rulers and fixture roots stay frozen for the whole round.

## 0 · Before the first number: pre-register

Read `docs/reference/qualitaetsmetrik.md` §14 and
`docs/proposals/tintenfolger.md` §7 first — a mechanism already rejected
there is a repeat, not a hypothesis, and §7.9 lists which rescue paths are
still open for each closed arm.

Write down BEFORE running: the one knob being changed, the gates it must
pass, and what counts as a kill. Softening a gate after seeing the number is
the failure mode the pre-registration exists to prevent.

**Base and arm must be the SAME stack except for that one registered
knob.** This is the rule both misfires broke.

## 1 · Fixture acceptance

```bash
uv sync --all-extras
uv run python -m tools.wordbench.fetch_fixtures --set all --verify
```

`--verify` is a bit-exact acceptance of the fixture roots. Run
`uv sync --all-extras` FIRST: the verify path imports matplotlib from the
`viz` extra and dies with `ModuleNotFoundError` on a fresh venv without it
(so does `tools.pairlab.follow`; `uv run --extra viz …` works too).

A repaired plate is NOT a free refresh: a fixture re-export is a declared
re-baseline and owes a dated entry in `qualitaetsmetrik.md` §15.

## 2 · The follower run — BLAS pinned, always

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --extra viz python -m tools.pairlab.follow \
  --all --set words --jobs 4 --json <report.json> --candidate-out <cand.json>
```

**Never run this unpinned.** The chain solve is not bit-reproducible across
thread environments, so cross-run comparisons are only valid within one
pinned setting — and pinning also collapses the runtime (a 63-word chain
went 87 min → 2.7 min). That is a CLAUDE.md guardrail, and this command line
is where it has to actually happen.

Since Kette v5 (`aug26`) **the duel stack is the DEFAULT** — composition
Soll, ratchet, zone 0.55 — so a run without flags IS the chain. The
archaeology flags reproduce older bases:
`--no-structure-guard-ratchet --structure-guard-zone 0 --soll-source init`
is the K0-Z Soll stack (the base of K0-S and L-U), and
`--no-structure-guard` is the guard-free follower — a DIAGNOSTIC arm only,
never a headline: it covers more ink by destroying structure. Per-arm flags
live in `--help` and in that arm's own §14 entry.

## 3 · dev-19 scoring

```bash
uv run python -m tools.tracebench --split dev --candidate file \
  --candidate-file <cand.json> --json <arm-report.json> --compare <base-report.json>
```

Paired deltas, counters, gates. The dev split is frozen and append-never.

## 4 · The 63-word k0 protocol

```bash
uv run python -m tools.tracebench.k0eval <base-cand.json> <arm-cand.json>
```

Reference-free across all words: Soll distance per word (composition Soll
via `ductus_soll`), `aiou` against the frozen mask, stroke-identity classes
(it compares the parsed strokes, not the file bytes).

**`k0eval` prints both stacks and warns when they differ. A warning here
aborts the round** — that warning is exactly what went unread on `aug25` and
`aug26`. Do not interpret numbers from a mismatched pair; fix the stack and
re-run.

A candidate solved on a PATCHED root (a Laufform candidate card, §14 LF3b-W)
is scored with `--fixtures <root>` against the Soll of THAT root — the
composition Soll travels with the card, and the frozen root's Soll would be
the wrong ruler there. One call per root; lay the distances side by side by
hand.

## 5 · Sensors and eyeballing (as needed)

```bash
uv run python -m tools.tracebench.excursions <cand.json>   # the standing K-D paper-excursion sensor
uv run python -m tools.tracebench.view                     # the duel / eyeball page
```

## 6 · File the round (part of the round, not paperwork)

- A **§14 entry** in `docs/reference/qualitaetsmetrik.md` with the
  pre-registration, the measured numbers and the verdict. **Insert it
  BEFORE the `## 15.` heading, not at the end of the file** — §14 is a
  closed section, and appending is how five `sep02` rounds ended up
  outside it (repaired 2026-09-03). Add its row to the register table at
  the head of §14 in the same PR. `uv run python -m tools.docs_register
  check` catches both slips, with a different message each: a section
  behind §14 is named as a misplaced journal entry, and a section inside
  §14 without its row as a missing register row.
- The **ledger line** on the affected `docs/reference/verfahren-*.md` page
  in the SAME PR; on adoption also its „Aktueller Stand" and the Stand
  column in `verfahren.md` (`docs/index.md` § Dokument-Status).
- On an honest negative, the **rescue paths**: named ways the goal could
  still be reached (new mechanism, new evidence, new sensor — each with a
  fresh pre-registration, never the same knob re-run with softer gates),
  plus the row in `docs/proposals/tintenfolger.md` §7.9, same PR.
- **An asymmetric result is to be USED, not discarded** (author directive,
  2026-08-26): the more lopsided better:worse is (v5 measured 32:2), the
  more the loser is worth decomposing into classes — partial adoption is
  legitimate, and a second opinion belongs before every declared negative.

## Gotchas

- **Paired comparisons only hold inside ONE pinned environment** (the
  `aug16` lesson). A number from an unpinned run cannot be compared with a
  pinned one, however close it looks.
- **The rulers stay frozen during the round.** Edit the follower, never
  `word_metric.py`, `tracebench` or the fixture roots — that is the
  frozen-ruler rule, and breaking it silently rewrites history.
- **`routeg` (Nullprobe) is never optimised** by doctrine
  (`tintenfolger.md` §7.6) — it is the control, so a "better" Nullprobe is
  a bug in the round, not a result.
- Display names of the routes (Kette · Lotse · InkSight · Nullprobe) are in
  the glossary under „Duell-Namen"; use them in write-ups.
