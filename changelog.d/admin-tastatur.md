### Added

- **The workbench can be operated from the keyboard.** The four overviews
  are **Roving-Listen**: the whole list is ONE tab stop, the arrows move
  inside it (↑/↓ between rows, ←/→ between the controls of one row,
  `Home`/`End` to the ends), and Tab leaves again. Measured at 1440 × 900,
  same stack, same data: Buchstaben **77 → 19** stops, Übergänge
  **142 → 44**, Wörter **67 → 21**, Streifen-Galerie **22 → 19** (only five
  tiles in the test stack; the saving grows with the number of hits). Focus
  hangs on the row KEY rather than the index, so it survives a filter and a
  page change and never lands on `<body>`. A wrapping tile surface gets only
  ←/→ — a flex grid has no stable column count, and a ↓ over six tiles at
  1440 px and three at 1024 px would be worse than none — and it is a NAMED
  toolbar to a screen reader, which would otherwise stay in browse mode and
  never forward the arrows at all. **Not included:** the card wall behind
  „Galerie" (154 → 156 stops — the two come from the switch and the stepper)
  and the Nachfahr-Übersicht; both are card lists of the same shape and the
  next use of the hook.
- **Every detail has a Subjekt-Stepper** — ‹ › around the subject plus the
  same movement on **Alt + Shift + ← / →**. Übergänge and Wörter had none at
  all. It follows the order of the overview the reader came from, filter and
  sort included, and because the same two arrows therefore mean something
  different after a filter click, the head names the order visibly. Not
  `Alt+←/→`: that is the browser's Back/Forward, which the admin's linking
  doctrine lives on.
- **A „Kurztasten" switch at the end of the Scope-Leiste**, its state as a
  visible word and the key combination as a caption beside it. Default on,
  remembered per browser. Off, nothing is bound; the ‹ › buttons keep
  working and the Roving-Listen stay — they are structure, not a shortcut.
  The binding never fires in an input field or while a dialog is open: the
  wizard and the Bahn-Editor own their keys themselves.
- **Both measuring grids know the workbench** (`--admin`). A run of its own,
  not the default list: without `VITE_ADMIN_TOKEN` every admin route is the
  boot-error screen, and a run over those reported 11 targets instead of
  ~420 — the type floor even reported „all routes clear" without having seen
  a single control.

### Fixed

- **The status dot in the letter grid carried its state in colour alone.**
  Green against orange at 7 px is the same grey to a deuteranope. „Canonical"
  is now a filled disc and „nur Bbox" a hollow ring of the same size — shape
  carries, colour confirms. The open case in design-system.md §9.4 stays open
  as an author decision: the grid is read daily, and the old two-colour dot
  is one line away.
- **Four controls under the 44 px floor, found by the first admin run:** the
  gallery card's „Öffnen" (64 × 32.5, twenty per page), „Laufform
  überschreiben" in the letter detail (163 × 32.5), „Erneut versuchen" on the
  boot-error screen (125.6 × 36.5, in both shells) and „Seite neu laden" on
  the route-error screen (112 × 36.5). The last two are the same blind spot:
  a route run measures only the states a route reaches by itself, and no
  route reaches its own error screen — where each is the ONLY control.
- **The technical message of an error stood at 13 px**, under the caption
  floor of 14 — both the expandable summary and the raw line beneath it.
