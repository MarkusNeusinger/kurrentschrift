### Added

- **An index over the campaign journal.** `qualitaetsmetrik.md` §14 opens
  with two tables: one row per dated entry (date, route, arm, type and
  verdict, linked to the section) and the headline ledger the running text
  never got — every wordbench headline since `aug14` with the fixture root
  it was measured on. 74 entries and ~47,000 words were previously
  navigable only by reading them (#489).
- **`tools/docs_register`, the gate that keeps the registers current.**
  `uv run python -m tools.docs_register check` requires a register row for
  every §14 entry, a number the journal already carries behind every ledger
  row, and a process-page ledger row for every duel-route entry; the CI job
  „Docs-Register" runs it beside the changelog gate. Three "same PR" duties
  written only in prose had decayed at once — a duty without a gate decays
  exactly that way (#489).
- **`tintenfolger.md` §7.11 „Offene Arme".** The next steps a closed round
  named used to live only in the running text of the entry that named them;
  they are now collected as a table, split into what a session can measure
  and what only the author can do. No numbers — those stay in §14 (#489).

### Fixed

- **The process pages were two adoptions and up to twelve days behind.**
  `verfahren.md` carried the chain as v3 and the index tree as v4 while the
  page itself said v5; the Lotse ledger knew neither the L-U ruler
  re-baseline nor the written Laufform map, and InkSight and Nullprobe had
  no row for either. All four pages now say what they measured and on which
  ruler cap, and the overview gains a „seit" column (#489).
- **Two headline pairs whose base nobody could name.** The root behind the
  `aug30` numbers was never declared a re-baseline, so it is marked as one:
  numbers from `aug30` on compare only with each other until the author can
  say where that export came from. A second dated note records that the
  roots lying in a working tree are the `aug14` export and do not reproduce
  the standing headline. From now on every headline names its `exported_at`
  and root digest (#489).
- **Five adopted mechanisms had no glossary entry.** Zonal rejection and
  the ratchet have been the chain's default since v5, the tail runout is
  the Lotse's first adopted constant, and the advance calibration carried
  the largest single drop of the word ruler — none of them was looked up
  anywhere. The Klassenregel entry listed six classes where
  `core/compose.py` carries fourteen; it now indexes the constants and
  names them as the source (#489).
- **Stale status headers and index rows.** `tintenfolger.md` still claimed
  no `FOLLOW_*` default had been adopted, two chain versions after the whole
  guard stack became the default; two docs used status words outside the
  small vocabulary; `eigenhand-erfassung.md` was missing from the structure
  tree and `tools/routeg`, `tools/inkpilot` from the tool inventory (#489).
