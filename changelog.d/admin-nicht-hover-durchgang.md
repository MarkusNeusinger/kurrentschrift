### Changed

- **No state of the workbench lives in a hover any more.** Every `Tooltip` and
  every native `title=` under `/admin` was classified by one mechanical
  question — is the tooltip's child focusable at all? Whatever carried a state,
  a reason, a number or an instruction while hanging on a non-clickable chip, a
  `Typography`, a `Box` or the `<span>` around a disabled control is visible
  text now, or sits behind an `InfoHint` — a real button with the focus ring and
  a 44 px target that opens on click and therefore works under a finger too. A
  tooltip that merely DESCRIBED its own button went the same way: what it said
  was not a name, and naming is the one job a tooltip keeps. Among them: why
  „Einrichten" and „Diagnose" are grey (a line in the chart toolbar), why a sort
  option cannot be picked, the six sensor readings behind a strip's Befund, a
  pair's raw numbers, the note on a clipped word specimen, the wording of a load
  error, the seven definitions of the Landmarken legend, and how the
  Fleckenmaske's brush works. New in `design-system.md` as **§9.4 (binding)**,
  with the rule „one `InfoHint` per row and subject", and pinned by a source
  guard so the next native `title=` on a chip fails a test instead of a review.

- **A letter row's deductions have one honest explanation instead of six tiny
  ones.** Each category was a 22 px `Typography` with its own `tabIndex` — a tab
  stop with no focus ring, up to 72 of them on a list page, and none of them
  reachable by finger. Every number stays visible; what explains them is
  `ScoreHelp`, the one `InfoHint` of the row, which also says what the score is,
  why a form carries none and what „Fit ⌀" measures. Measured on the throwaway
  stack: not one tabbable `span` left on `/admin/buchstaben`, and every one of
  its 79 stops wears the viridian ring.

- **The header's Auftragskorb ⚑ no longer carries a count badge.** MUI sets that
  digit in 12 px, under the type floor, and it said in colour what the
  Scope-Leiste says in words one row down. The icon keeps a named `aria-label` —
  which now carries the count itself, because on a phone the bar scrolls its
  active field into view and the Vorlage field can sit off screen — and gains
  the 44 px target.

### Added

- **The focus ring is a shared token.** `focusRing` lives in
  `app/src/styles/focusRing.ts`, beside `hitArea`, and the theme imports it for
  its three MUI rules. It used to be a module-private constant, which left every
  hand-built focusable without it: three surfaces carried their own `2px solid`
  at a different offset, and four — the wordmark, the two landing CTAs and the
  Lesetafel's zoom area — showed nothing but Chrome's 1 px default, the wordmark
  being the FIRST tab stop of every page on the site. The Eigenhand coverage
  cells, bare `<button>` elements with `appearance: none`, showed nothing at
  all. A keyboard walk over twelve routes now finds one ring and no other:
  2 px viridian at 2 px offset, with only MUI's text fields keeping their
  documented border-based focus. A unit test pins the IDENTITY of the object in
  the theme rules, not its equality — a second literal with the same numbers is
  exactly the drift the export is written against.

### Fixed

- **The Eigenhand gallery's Lupe could not be reached by keyboard.** The opener
  was an `<img onClick>` with no role, no `tabIndex` and no key handling; it
  escaped the ESLint rule only because the JSX element is called `Box`. It is a
  `ButtonBase` with its own name now („S0001 · F01 groß ansehen") that opens on
  Enter — driven and confirmed in the browser. The same for the Auftragskorb
  row, which was a `<p role="link">` with a hand-rolled Enter/Space handler.

- **Touch targets under the 44 px floor in the workbench.** „Buchstabe wählen",
  the ‹ › step and the letter chip in the header, the four `?reiter=` switches
  and the strip zoom group of the Eigenhand page, the ~90 coverage cells, the
  buttons of the basket drawer, the chart toolbar, the actions of every view and
  panel head, and the chips that navigate from a word to its letters and joins
  all grow to the floor — grown, not overlaid, because they stand close
  together. Measured with one instrument over seven admin states (the four
  routes plus the three detail views), on synthetic material: 87 shortfalls
  before, none after, identical at 1440, 1024 and 390 px wide. `type-floor` over
  the same routes goes from four to none.

- **`touch-targets` measured the wrong element on an input field.** MUI renders
  a select as a combobox `div` plus an invisible `<input>` that exists only so
  the control submits with a form; the script measured that 21 px shim instead
  of the 44 px field root. A field is measured at the FIELD now — the same
  thought that already measured a control wrapped in a `<label>` at its label. A
  field root under the floor still fails. The change accounts for exactly two of
  the shortfalls above, which is why the before number was re-taken with the
  corrected script rather than quoted from the old one.
