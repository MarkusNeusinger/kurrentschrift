### Added

- **The reading cost is a number with a gate now.** `tools/docs_budget`
  (CI job „Docs-Budget", `uv run python -m tools.docs_budget check`) measures
  what a session must load before it starts working — the mandatory reading
  list and each of the seven reading paths named in `CLAUDE.md` — and fails
  when one grows past its budget. The list is READ OUT of `CLAUDE.md` rather
  than copied into the tool, so adding a bullet moves the measured sum instead
  of quietly widening the list. It also checks the three things that make the
  cheap path actually cheap: a `lebend` doc over ~10 000 tokens carries a Stand
  block of at least 12 lines dated within 30 days, `docs/index.md` holds
  exactly one row per `.md` file under `docs/`, and every relative markdown
  link and `#anchor` in the repo resolves. Tokens are counted by a
  deterministic proxy shipped with the tool rather than by `tiktoken`: the job
  runs on the standard library like the other docs gates, and `tiktoken` would
  download its BPE table on every run. The budgets are stated in proxy units,
  so the gate compares like with like; the cross-check against `o200k_base` is
  in the module docstring.
- **A Stand block for `glossar.md`.** At 57 000 tokens it was the one large
  `lebend` doc still opening with a four-line status. It now says what the file
  is for, that the Schnellindex is the way in, and that the short glossary is
  what a session reads instead — which is also the first thing the new gate
  asked for.
