### Fixed

- **Every focusable control on the public site now shows where the keyboard
  is.** MUI's `ButtonBase` sets `outline: 0`, so quiz answers, chips and icon
  buttons were pixel-identical focused and unfocused — the quiz simply could
  not be played from a keyboard, and Lighthouse cannot see it (`focusable-controls`
  is a manual audit). One theme rule on `MuiButtonBase`, `MuiChip` and `MuiLink`
  draws the 2px viridian ring that `PaperCardLink` and the header nav already
  had, instead of twelve per-component fixes. Measured over a real Tab walk of
  /quiz, /federprobe, /schreiben/uebungsblatt and /tafel?g=n: 4 of 38 stops
  showed a ring before, 30 of 38 after — the rest carry MUI's own focused field
  border or the Schreibtafel's cell-fill rule (#485).
- **Links in running prose are recognisable as links again.** They differed
  from the surrounding text by colour alone, and by 1.35:1 at that, with the
  underline appearing on hover — i.e. never for keyboard or touch (WCAG 1.4.1).
  `MuiLink` now underlines always and runs in the contrast-derived
  `viridianText` (5.15:1 on the paper ground); the three prose pages gave up
  their private `proseLink` constants so the rule cannot drift again. Header and
  footer keep their own undecorated chrome (#485).
- **Seventeen places under the binding 14px type floor.** Specimen captions
  rendered at 12.16px, the landing status marks at 13.6px, and every MUI
  `size="small"` chip, button and toggle at 13px. Lifted centrally in the theme
  plus two ad-hoc `fontSize` values turned into `variant="caption"`; the
  sanctioned 13px overline stays. The landing's „Lesen" CTA — the only
  Lighthouse contrast failure of the start page at 3.72:1 — now sets its label
  in 600, which makes 19.2px count as large text and clears AA without leaving
  the period tone #40826d (#485).
- **The 404 page had no footer and reported nothing.** A dead end is exactly
  where a visitor needs the Impressum link and the three areas, so the footer is
  back; and the page now sends a `page_not_found` event with its path, the only
  way to notice that something on the web links here wrongly (#485).

### Added

- **`hitArea()` — an invisible 44px touch target that leaves the optics
  alone.** The replay ↻ over the ink, the Kurrent-i of `InfoHint`, the quiet
  „beenden" and the Federprobe chips are deliberately small marks; making them
  physically bigger would shout where the design whispers. A centred `::after`
  of `max(100%, 44px)` gives the thumb what it needs instead
  (`app/src/styles/hitArea.ts`); toggle groups grow to 44px below `sm` via the
  theme. design-system.md §9.3 carries the rule — marked as a proposal until the
  author adopts the 44px floor, since WCAG itself is already met (#485).
- **`app/scripts/type-floor.mjs` — the standing grid under the type floor.** It
  walks every public route in a real browser, reads the computed font size of
  every element rendering text of its own and fails under 14px. No new
  dependency: it drives Chrome over the DevTools protocol using Node 22's
  built-in WebSocket. `npm run type-floor`; against the live site it reports the
  17 places above, against this branch none (#485).
- **A back-to-top button on the three long content pages.** /schriftkunde is
  about twenty phone screens tall and its only inner navigation is the jump list
  at the very top, unreachable after the first screen. The button appears after
  two screens of scrolling, is 44×44, and jumps rather than glides under
  `prefers-reduced-motion` (#485).
- **The page gutter now includes the safe area.** `index.html` opts into
  `viewport-fit=cover`, so on a notched phone in landscape the first ~47px of
  each edge sat under the cutout while nothing in the app compensated.
  `PageContainer` and `PublicFooter` state their padding as
  `max(designed, env(safe-area-inset-*))`, which keeps the designed gutter
  everywhere and yields only where the device asks for more (#485).

### Changed

- **A stale chunk after a deploy now recovers by itself.** `RouteError` existed
  for exactly that failure but asked the visitor to press a reload button for
  something they neither caused nor can understand. It now recognises the four
  browser wordings for a failed dynamic import and reloads once, guarded by a
  `sessionStorage` flag so a genuinely broken `index.html` cannot loop the tab;
  a thrown 404 renders the real 404 page. The guard fails toward the manual
  button: where `sessionStorage` throws, no automatic reload happens at all,
  because an unguarded one is the case that could spin the tab. Pattern taken
  from the sibling repo (#485).
