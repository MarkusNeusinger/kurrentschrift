### Fixed

- **The Diagnose modal confirms „Neu ableiten & speichern" again.** The success
  note was never on screen for a single frame: `apply()` raises the flag and
  then bumps `cropCacheBust`, and the render-phase reset that clears the view's
  transient state hung off a key carrying exactly that counter — so the one
  acknowledgement of a WRITE to the shared production database was wiped in the
  very pass that apply's own refetch triggered. The note is now adjusted on the
  selection (source + glyph), the only change that can make it stale, and a
  second attempt clears it up front so a failing re-run cannot report success
  and failure side by side. Website audit finding A39.

### Added

- **A DOM environment for the SPA test suite, and the first test that needs
  one.** `jsdom` joins the devDependencies and `QualityView.test.tsx` opts into
  it per file (`@vitest-environment jsdom`), driving the real click through
  React's own `act` with `postResample`, `getQuality` and the context's
  `refreshCrop` mocked. Everything else keeps rendering to static markup, which
  is enough for markup facts — but the bug above only exists across a click and
  the refetch that click triggers, so no markup assertion could have caught it,
  and both cases in the new file fail against the unfixed component.

### Changed

- **`engines.node` says `>=22.22.2`, the floor the install actually applies.**
  `.npmrc` has `engine-strict=true`, so the manifest's range is enforced at
  install time — and jsdom wants `^22.22.2`, which made the declared `>=22` a
  promise the tree could not keep: a Node 22.5 machine passed the manifest and
  was then refused by the dependency, with the version buried in an
  `EBADENGINE` line. `>=22` had in fact been understated since Vite 8
  (`>=22.12.0`); the floor now names what `npm ci` enforces. Nothing moves for
  the paths that build this app — `.nvmrc`, CI's `node-version: 22` and
  `node:22-alpine` all resolve to the newest 22.x.
