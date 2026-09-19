### Changed

- **Phase 1 of the Admin-Redesign is booked as delivered in its plan
  (`docs/proposals/admin-redesign.md`).** §15.4 now carries all eight PR
  numbers — 1 Vokabular #621 · 2 Eigenhand-Reiter #622 · 3 Scope-Leiste and
  `h=` #626 · 4 Übergabekarte and `report --faellig` #625 · 5 Arbeitslisten I
  #624 · 6 Arbeitslisten II #627 · 7 Nicht-Hover-Durchgang #629 · 8 Tastatur
  #631, with the phase's decisions booked in #623 — and one line per PR on
  what it actually shipped, read out of the merged PR bodies rather than out
  of the plan's own promises. The status blockquote, the §15 Stand paragraph
  and the plan's row in `docs/index.md` say the same thing: phases 0 and 1
  are delivered in code, the production data step V1 is still the one open
  piece of phase 0, phase 2 (Tintentreue and Nachfahren) is next and starts
  with a read-only reconnaissance, and phase 5 stays blocked on the author
  (FM1–FM6 of `freigabe-maschine.md`, the read sweep over the admin API
  before M1, and V1). Every change is a dated Stand, nothing is rewritten
  silently.
- **The plan says once, plainly, what phase 1 was never seen doing.** Every
  browser verification of the wave ran on a throwaway Postgres with SYNTHETIC
  data — the reserved dataset is not seedable and no PR of the wave touched
  the shared database or the deployed API, not even reading — so the POPULATED
  letters, joins and words surfaces have not been seen with real data before
  the author's own look in the production admin. What is measured are ratios
  and mechanics (page heights, image counts, tab stops, hit targets), never
  product numbers. The one follow-up that closes the phase is named with it:
  issue #628, the inert `Typography color="text.secondary"` prop under MUI 9,
  fix in flight.

### Added

- **A collected list of the taste questions phase 0 and phase 1 left open
  (`admin-redesign.md` §15.5).** Twenty-eight items gathered out of the nine
  PR bodies that each carried their own „open author questions" section — the
  removed header Korb badge, the 9.6 px counter in the coverage grid,
  `ScoreHelp` per row versus once in the toolbar, the Übergänge sort, the
  tab-wide score sweep, the anchor letter replacing instead of pushing
  history, `Hand: —` under V19, `h=` as metadata only, the URL word `reiter`,
  the letter picker's filled/hollow status dots, roving outside the shortcut
  switch, the two surfaces left without roving, the translucent engine
  overlay and the dotted lift connector, and the vocabulary PR's three Q10
  labels. Each says what was built (always the recommendation) and where the
  one-line flip sits. It decides nothing: it exists so the author does not
  have to reconstruct nine PR bodies to find the knobs.
