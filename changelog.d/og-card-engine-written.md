### Changed

- **The share card is written by the engine, not set in the show font.** The
  1200×630 Open-Graph card (`app/public/og.png`) used to spell the brand word in
  GL-GermanCursive — which contradicted the page it advertises, where the hero
  writes "Kurrentſchrift" with the synthesis engine and touches that font only
  when the backend fails. It now takes the hero's own route,
  `GET /sources/{id}/write/word.svg`, and quotes the rest of the identity from
  where it lives: the viridian swash is `HeroWritten`'s `Flourish` path, the
  corner mark is the header `Wordmark` (minus its dot — the swash and the ".ink"
  already carry the accent), the lead is the landing page's own H1. `og:image:alt`
  and `twitter:image:alt` now say what the card shows and that it is written in
  Sütterlin, the same honesty the hero caption keeps.

### Added

- **`tools/ogcard` rebuilds that card on command.** A card bound to a template
  instead of a font has to be re-buildable when the template is re-traced, so the
  composition is a tool rather than a one-off image:
  `uv run python -m tools.ogcard`. One public GET, no database, no admin token;
  it renders with the headless Chromium Playwright already installs for
  `/verify-frontend` and checks the result before writing (right size, paper in
  all four corners — the silent failure when a browser sizes the window instead
  of the viewport). The composed geometry is fetched and never committed; only
  the published raster lands in the repo.
