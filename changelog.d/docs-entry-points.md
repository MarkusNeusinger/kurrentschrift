### Added

- **A short glossary, chosen by counting.** `docs/reference/kurzglossar.md`
  carries the 77 terms that actually turn up where a session reads them — a
  term qualifies when it occurs, matched with word boundaries, in at least two
  of three sources: the code (`core/`, `api/`, `tools/`, `alembic/`,
  `app/src/`), the agent files, and the bodies of the last 40 merged PRs. One
  or two sentences each, every entry linking into its themed block of the full
  glossary, which stays the lookup instance and keeps its Schnellindex. It
  replaces `glossar.md` on the mandatory reading list, where 56 000 tokens of
  vocabulary were more than half the budget.
- **Stand blocks on the six large docs.** `qualitaetsmetrik.md`,
  `messjournal.md`, `menschliche-bewertung.md`, `frontend-stack.md`,
  `werkzeuge.md` and `architektur.md` now open with a dated block of at most 40
  lines saying what currently holds, what is open and where the detail lives —
  every summary sentence carrying the anchor of the section it summarises. It
  is what a session reads instead of the file.
- **Per-track reading paths in both agent guides.** A table naming, per kind of
  work, the sections to read and roughly what they cost: a measurement round
  reads the journal's register rather than its entries (≈ 15k instead of 143k),
  a frontend change reads the design system plus two sections of the stack doc.

### Changed

- **`docs/index.md` is a map again.** One row per file with its purpose and
  when to open it, nothing repeated from the docs themselves — 12 265 tokens
  down to 3 643. The lifecycle vocabulary and the table of Nachzieh-Pflichten
  moved verbatim into the new `docs/dokument-status.md`, so the starting page
  is not also the maintenance manual. Together with the short glossary the
  mandatory reading list falls from 110 796 to 52 943 tokens.
