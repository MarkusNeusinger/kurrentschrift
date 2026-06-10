# Third-Party Notices

This application bundles and self-hosts the following third-party assets.
Each is governed by its own license, independent of the project's MIT code
license — the font files are a separately-licensed asset, not covered by and
not affecting the MIT license of the source code.

## Fonts

### EB Garamond

- **Used for:** the body and UI serif site-wide (display headlines use
  Playfair Display, see below).
- **Copyright:** © 2017 The EB Garamond Project Authors
  (<https://github.com/octaviopardo/EBGaramond12>).
- **License:** SIL Open Font License, Version 1.1 (`OFL-1.1`).
- **Full license text:** [`public/fonts/EBGaramond-OFL.txt`](public/fonts/EBGaramond-OFL.txt),
  served in production at `/fonts/EBGaramond-OFL.txt`.
- **Packaged via:** [`@fontsource/eb-garamond`](https://www.npmjs.com/package/@fontsource/eb-garamond)
  (weights `400`, `400-italic`, `600` imported).

The OFL permits self-hosting, embedding and redistribution (including
commercial use). The font is unmodified; the copyright and license notice
above, plus the bundled license text, accompany the font as the license
requires.

### GL-GermanCursive

- **Used for:** the landing-page showpiece word ("Kurrent"), set on a ruled
  baseline as the hero — decorative only, never UI text.
- **Source:** Gutenberg-Labo, *GL-GermanCursive* (a copperplate-style
  Sütterlin/Kurrent mixed cursive).
- **License:** free — "Unlimited permission is granted to use, copy, distribute
  and modify it, with or without modification, commercially and noncommercially.
  THIS FONT IS PROVIDED 'AS IS' WITHOUT WARRANTY."
- **Packaged as:** a self-hosted WOFF2 (24 KB), bundled at
  `src/assets/fonts/gl-germancursive.woff2` and declared via `@font-face` in
  `PaperBackground.tsx`.

The font is a placeholder showpiece, not the project's ductus renderer; it is
self-hosted and redistributed under the permissive grant above, unmodified.

### Playfair Display

- **Used for:** display type — the landing hero headline, the brand wordmark and the
  section/pillar titles.
- **Copyright:** © 2017 The Playfair Display Project Authors
  (<https://github.com/clauseggers/Playfair-Display>), with Reserved Font Name
  "Playfair Display".
- **License:** SIL Open Font License, Version 1.1 (`OFL-1.1`).
- **Full license text:** [`public/fonts/PlayfairDisplay-OFL.txt`](public/fonts/PlayfairDisplay-OFL.txt),
  served in production at `/fonts/PlayfairDisplay-OFL.txt`.
- **Packaged via:** [`@fontsource/playfair-display`](https://www.npmjs.com/package/@fontsource/playfair-display)
  (weights `400`, `500`, `500-italic`, `600`, `600-italic` imported).

The OFL permits self-hosting, embedding and redistribution (including commercial
use); the font is unmodified.
