### Changed

- **The guardrail rationale moved out of the file every session loads.**
  `CLAUDE.md` is read on every turn, so its cost is paid on every turn — and
  its guardrail section had grown into retro narratives: the incident, the
  recipe, the numbers, inline. Each rule is now one binding line with its
  shortest reason and its date, and the stories moved to
  `.claude/guardrails.md`, which a session reads when it actually hits the
  situation. Condensing did quietly drop two triggers on the first pass — the
  snapshot owed AFTER an authoring session, and the re-read owed after a
  formatter or codegen rewrites a tracked file — and review caught both; they
  are back in their one-liners, which is what the correspondence test now
  exists to enforce. Otherwise no rule was dropped, softened or merged;
  `CLAUDE.md` shrank from
  34,546 to 29,132 bytes (−16 %). `.github/copilot-instructions.md` keeps its
  guardrails spelled out in full on purpose — Copilot Code Review reads that
  file and does not follow links — and now says so (#NNN).
- **`tests/test_agent_instructions.py` pins the split mechanically.** The new
  file joins the path and section checks, and every `##` section of the
  companion file must map to a phrase that actually appears in `CLAUDE.md` —
  both directions, so an unregistered section fails and a registration
  covering nothing fails too. That is what stops a rule from coming to rest
  where no session loads it; a disclaimer sentence alone would not have
  caught it. The mirrored-rule list also gained the two shared rules it was
  missing, the Copilot re-review and Todoist ones (#NNN).
