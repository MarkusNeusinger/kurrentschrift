### Changed

- **The trace round's five-step liturgy has one copy again, and
  `werkzeuge.md` its budget back.** The measurement liturgy of a Tintenfolger
  round stood twice: once in `.claude/skills/verify-trace/SKILL.md`, once as
  five copy-paste command blocks in `docs/reference/werkzeuge.md` — and #540
  had to write the same `--expect-root` flag into both. The doc now carries a
  pointer instead: what the skill does, when it is invoked (**before** a round,
  as a checklist, not looked up afterwards), and that it is the executable
  form. What stays in `werkzeuge.md` is what a tool index is for — the five
  entry points of `tools/tracebench` and `tools/pairlab/follow`, where their
  flags are documented, and the invariants that hang on them. The Stand block
  says the same in one line, because a session reads it instead of the file.
  The section falls from 4125 to **3704** proxy tokens, two off the 3702 that
  set its budget on 2026-09-04, so the stopgap raise #540 took —
  `werkzeug-abschnitt` 4073 → 4538 — **is reverted to 4073 unchanged**: the
  growth was moved out of the read path, which is what the gate asks for, and a
  budget re-measured to the same number is the proof. The glossary's `k0eval`
  entry and the skill's own opening paragraph now name which file holds which
  half.
