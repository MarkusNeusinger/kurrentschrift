### Changed

- **The 44px touch rule is binding, not a proposal.** design-system.md §9.3 went
  in as a suggestion because it goes beyond WCAG — SC 2.5.8 asks for 24×24 and
  the site already met it through the spacing exception. The author decided on
  2026-09-03 to hold the platform recommendation (Apple HIG 44 pt, Material
  48 dp) instead, so the section and the glossary entry now read as a rule. The
  companion decision, that links in running prose stay underlined, needed no
  change: §9.2 was already binding.

### Added

- **`npm run touch-targets` measures the touch rule instead of asserting it.**
  It sweeps every interactive element on every public route — 217 of them — and
  skips exactly the rule's one exception, recognised the way §9.2 marks it on the
  page: an underlined `<a>` is running-prose text, while chrome that only looks
  like a link sets `textDecoration: none` and is measured like everything else.
  For each axis where a control is drawn under 44px it asks
  `document.elementFromPoint` at the edge of the 44px square and requires the
  control itself to answer. That catches the way this rule breaks silently — an
  `overflow: hidden` clips the `hitArea()` pseudo-element, the drawing is
  unchanged and the target shrinks back unnoticed — which a computed-size check
  would sail past. Verified against a deliberately broken control: removing
  `hitArea()` from the replay button is reported, and only that one (#504).

### Fixed

- **Twelve controls were under the binding 44px floor.** The sweep found them
  once it stopped consulting a list: the four Lesart example chips, the Tafel
  step buttons, „Lesetafel als PDF", „Als PDF herunterladen", „Zur Startseite",
  the landing hero's „Schreiben →" and its replay line, the wordmark and the two
  footer links. All fixed without moving a pixel of the drawing, except the
  header area links, which take the floor from real padding — on phones the bar
  stacks into two rows whose centres sit 28px apart, and an invisible overlay
  there would have made adjacent targets overlap by 16px. Wrapped chip rows
  needed their `rowGap` raised for the same reason: 28px chip plus 12px gap is a
  40px pitch, so the lower row reached over the upper one and won its taps
  (#504).

- **The quiz setup hint sat at 13px, under the binding 14px floor.** It renders
  only for settings that actually offer a choice, which is why the measuring pass
  of the previous round walked past it and reported the site clear; the run that
  makes the sibling rule binding caught it. Now `variant="caption"` like every
  other hint (#504).
- **`npm run build` was failing on `main`.** The sitemap `lastmod` for
  `/schreiben/uebungsblatt` still read 2026-09-02 while its copy changed on
  2026-09-03, and the guard that holds those two together is part of `prebuild` —
  so every branch cut from `main` inherited a red frontend build. Bumped, with
  the prerendered „Stand" line that follows from it (#504).
