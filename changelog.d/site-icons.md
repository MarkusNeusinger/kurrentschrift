### Changed

- **The site icon is the engine's own written K, not a show-font letter.**
  `favicon.ico` and `apple-touch-icon.png` were a capital K set in
  GL-GermanCursive, rendered once by hand, that collapsed into a green
  smudge at 16 px. `python -m tools.favicon` now fetches the written K from
  `/write/glyphs/K.svg`, fits its outline into the icon square with the
  wordmark's viridian dot, and writes `favicon.svg`, a 16/32/48 `favicon.ico`
  and the 180 px touch icon from that one geometry — Pillow only, no browser.
  The icon is re-buildable after a re-trace, like the share card.

### Fixed

- **The prerendered crawler pages declared no icon.** A crawler never
  receives `index.html`, so its only icon candidate was the `/favicon.ico`
  fallback. `prerender.ts` now emits the same three icon links as the SPA
  shell, absolute, on all eleven pages.
