### Fixed

- **The admin detail pages no longer scroll sideways.** The workbench header
  hid its plain-text `h1` with a hand-rolled style object, and inside MUI's
  `sx` a `width: 1` is not one pixel but 100 % of the nearest positioned
  ancestor — which in the admin is the full-width paper ground. Every letter,
  join and word page therefore ran 16 px past the window on desktop and 8 px
  on a phone. It now uses MUI's own `visuallyHidden`, so the heading stays in
  the accessibility tree and the page ends where the viewport does.
- **The browser tab names the workbench subject.** Admin routes kept whatever
  title the last public page had set — a cold load showed the site default —
  so two open tabs were indistinguishable. `AdminLayout` now sets
  `document.title` from a pure `adminTitle(pathname, search)`, reading the
  same subject the view's heading spells out: „Buchstabe n · Werkbank",
  overviews „Buchstaben · Werkbank". Deliberately not through the public
  `usePageMeta`, which would also mint canonical and Open Graph tags for a
  gated route.
- **Two expected 404s left the admin console.** The pair editor asked for one
  override row and the Eigenhand setup panel for one hand's setup, both
  treating the 404 as „none yet" — the normal answer for nearly every pair
  and for a hand before its first session, and a red console line every time.
  Both now pick their row out of the list route the server already offers,
  which costs no extra request and answers 200. Picking from a list made the
  pair variant part of the identity everywhere it was not: the Übergänge
  matrix keyed its badges without it, and because the list arrives ordered by
  variant, a second variant of a pair would have badged the cell whose editor
  opens — and whose geometry the composer renders — from variant 0.

### Changed

- **The Admin-Redesign plan reads `teil-umgesetzt`.** These repairs are the
  first delivered stage of its Phase 0, so — as the docs lifecycle asks, in
  the same PR as the code — the plan's status header and its row in
  `docs/index.md` move from `offen` to `teil-umgesetzt`; nothing else in the
  plan changes here.
