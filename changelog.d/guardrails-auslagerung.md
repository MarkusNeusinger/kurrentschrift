### Changed

- **The guardrail rationale moved out of the file every session loads.**
  `CLAUDE.md` is read on every turn, so its cost is paid on every turn — and
  its guardrail section had grown into retro narratives: the incident, the
  recipe, the numbers, inline. Each rule is now one binding line with its
  shortest reason and its date, and the stories moved to
  `.claude/guardrails.md`, which a session reads when it actually hits the
  situation. No rule was dropped, softened or merged; `CLAUDE.md` shrank from
  34,546 to 29,132 bytes (−16 %). `.github/copilot-instructions.md` keeps its
  guardrails spelled out in full on purpose — Copilot Code Review reads that
  file and does not follow links — and now says so (#NNN).
- **`tests/test_agent_instructions.py` pins the split.** The new file joins
  the path and section checks, and one test guards the two ways this
  arrangement rots: `CLAUDE.md` losing the pointer, so nobody finds the
  rationale, or the companion file starting to read like the authority, so a
  rule ends up living only where no session loads it. The existing
  mirrored-rule pin already keeps every binding keyword in both guides
  (#NNN).
