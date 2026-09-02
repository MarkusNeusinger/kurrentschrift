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
  It does not sweep the site — most small targets there are legitimate, and a
  blanket check would be a wall of false positives nobody reads. It guards the
  mechanism: the seven controls that are deliberately drawn small and get their
  44px from the invisible `hitArea()` pseudo-element. For each axis where a
  control is drawn under 44px it asks `document.elementFromPoint` at the edge of
  the 44px square and requires the control itself to answer. That catches the one
  way this rule breaks silently — an `overflow: hidden` clips the pseudo-element,
  the drawing is unchanged and the target shrinks back unnoticed — which a
  computed-size check would sail past. Verified against a deliberately broken
  control: removing `hitArea()` from the replay button is reported, and only that
  one (#500).

### Fixed

- **The quiz setup hint sat at 13px, under the binding 14px floor.** It renders
  only for settings that actually offer a choice, which is why the measuring pass
  of the previous round walked past it and reported the site clear; the run that
  makes the sibling rule binding caught it. Now `variant="caption"` like every
  other hint (#500).
- **`npm run build` was failing on `main`.** The sitemap `lastmod` for
  `/schreiben/uebungsblatt` still read 2026-09-02 while its copy changed on
  2026-09-03, and the guard that holds those two together is part of `prebuild` —
  so every branch cut from `main` inherited a red frontend build. Bumped, with
  the prerendered „Stand" line that follows from it (#500).
