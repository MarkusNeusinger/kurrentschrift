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

### Suetterlin (Zinken HJZ 1911)

- **Used for:** the Sütterlin specimen's cold-start fallback on `/schriftkunde`
  (the synthesis engine renders the live specimen). Decorative only, never UI text.
- **Source:** Hans J. Zinken, *Suetterlin HJZ 1911 Italic*
  (<http://www.zinken.net/Fonts/Suetterlin.html>); font file © 2017 Hans J. Zinken.
- **License:** freeware, redistribution explicitly permitted. The source page
  states: *"Dieser Font ist Freeware und darf zu persönlicher wie auch
  geschäftlicher Nutzung frei verwendet werden."* and, in its footer,
  *"Kopierrechte: © 1997-2014 vorbehalten, Verbreitung ausdrücklich gestattet!"*
  (English on the same page: *"This font is freeware and can be used either for
  private or for professional purpose."*). Modification is **not** granted.
- **Embedded metadata (this file):** the TTF name table reads *"Copyright (c)
  2017 by Hans J. Zinken. All rights reserved."*, version 1.000 (a 2024-03
  build), plus a trademark notice *"Suetterlin_Italic_3 is a trademark of Hans J.
  Zinken."* The "All rights reserved" is the author asserting copyright, not a
  withdrawal of the freeware grant above — the two coexist; the © 1997-2014 is
  the site-wide footer date, this particular face is © 2017. We reference the
  font only through the CSS family alias `Suetterlin` (the generic script name),
  never the trademarked string "Suetterlin_Italic_3".
- **License decision:** this redistribution-only, no-modification freeware grant
  is weaker than the OFL fonts above and was reviewed and accepted by the
  maintainer for use as this bundled cold-start showpiece.
- **Packaged as:** the original, **unmodified** TrueType file (80 KB), bundled at
  `src/assets/fonts/suetterlin-hjz-1911.ttf` and declared via `@font-face` in
  `PaperBackground.tsx`. It is deliberately *not* re-packed to WOFF2, because the
  grant covers redistribution but not modification — the TTF ships verbatim.

The font is a placeholder showpiece, not the project's ductus renderer. Note its
character map: the plain `s` already is the long ſ and the round End-s sits on
`#` (accented codepoints carry Anstrich/ligature variants), so text set in it
must use plain ASCII rather than U+017F.

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
