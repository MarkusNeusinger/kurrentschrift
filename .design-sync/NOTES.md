# design-sync notes — kurrentschrift.ink

Target project: **kurrentschrift.ink Design System** (`2f6a4b78-bdcf-4999-ac4d-01c7cef353ff`).
First sync 2026-06-20 **replaced** the old hand-authored project (preview/*.html,
ui_kits/, colors_and_type.css, assets/) with the converter bundle (6 brand components).

## Shape & key decisions (app-only repo, no Storybook)

- **Package shape with a CURATED entry**, not blind synth-entry. `app/designsync-entry.tsx`
  (`cfg.entry`) re-exports the 6 brand components + an `AppProviders` wrapper
  (ThemeProvider + CssBaseline + MemoryRouter). It lives in `app/` (NOT `app/src/`) on
  purpose: outside tsconfig `include:["src"]` so it never enters app type-check/CI, and
  the converter walks up from it to `app/package.json` → `PKG_DIR = app/`. The blind
  synth-entry would `export *` every src file incl. `main.tsx`, whose top-level
  `createRoot().render()` would run on bundle load.
- **`cfg.tsconfig` → `.design-sync/tsconfig.designsync.json`**: maps every `@/` BARREL
  directory (theme, locales, lib/api, the 6 component barrels, routes, setup-wizard) to
  its `index.ts` BEFORE the `@/*` wildcard. The converter's tsconfig-paths plugin matches
  a barrel dir at the empty-extension step and esbuild then errors `… is a directory`.
  **If a synced component starts importing a NEW barrel dir via `@/<dir>`, add it here.**
  **Keep this file free of `//`-prefixed keys (no `"//"` / `"//ttf"` JSONC-style doc
  keys).** The plugin's comment-stripper (`/(^|[^:])\/\/.*$/gm` in `lib/bundle.mjs`)
  treats a `"//…"` STRING KEY as a line comment, mangles it, and `JSON.parse` then throws
  → `tsconfigPathsPlugin` SILENTLY returns null. With the plugin dead, esbuild's
  auto-discovered `app/tsconfig.json` still resolves `@/*` natively, so barrels keep
  working and nothing looks broken — but our explicit overrides (the `.ttf` shim below)
  are NOT applied. If a `@/`-override stops taking effect, suspect a parse-break here
  first: `node -e "JSON.parse(require('fs').readFileSync('.design-sync/tsconfig.designsync.json','utf8').replace(/\/\*[\s\S]*?\*\//g,'').replace(/(^|[^:])\/\/.*$/gm,'$1'))"` must succeed.
- **Suetterlin TTF shim** (`.design-sync/shims/suetterlin-font.ts`): since 2026-06-23
  PaperBackground imports `@/assets/fonts/suetterlin-hjz-1911.ttf` (a 2nd `@font-face`,
  the Sütterlin specimen face) injected globally for OTHER pages. The IIFE bundle's
  esbuild loader map (`lib/bundle.mjs`) has **no `.ttf` loader** and exposes no config
  hook, and `lib/bundle.mjs` MUST NOT be forked (output contract). Fix is config-only: an
  EXACT `@/assets/fonts/suetterlin-hjz-1911.ttf` → shim rule (listed before `@/*`) in
  `tsconfig.designsync.json`, where the shim `export default ''`. Result: PaperBackground
  emits an inert `@font-face{font-family:'Suetterlin';src:url()}` no synced component uses
  (none render Suetterlin text), the bundle carries no 82 KB TTF, and shipping it as a
  settable face would anyway violate the brand legibility rule. GLKurrent (`.woff2`, loader
  present) is untouched. **If a future component genuinely needs the `.ttf` inlined**, the
  only loader-level fix would be a declared `cfg.libOverrides` fork — escalate to the user.
- **Previews** import components from the pkg name `kurrentschrift-app` (shimmed to the
  bundle global). Layout scaffolding uses plain HTML + design tokens via **RELATIVE**
  imports (`../../app/src/styles/paper`), NOT `@/…` — the preview build pass runs the
  storyImports policy plugin before the paths plugin, so `@/` does NOT resolve there
  (pkg-only previews are fine). Relative imports also avoid bundling a 2nd MUI/theme.
- **Fonts**: `cfg.extraFonts` ships the @fontsource faces `main.tsx` loads (EB Garamond
  400/400i/600, Playfair 400/500/500i/600/600i) PLUS `.design-sync/glkurrent.css` — the
  brand "i" face (GLKurrent), declared in the GLOBAL stylesheet so InfoHint's mark renders
  in any design (in the app it's only injected when PaperBackground mounts).
- **overrides**: BootStatus / PaperBackground / PublicHeader → `cardMode: column`
  (full-width / full-page components crop in the multi-column grid).
- **Render check** runs against the system Chrome: `DS_CHROMIUM_PATH=/usr/bin/google-chrome`
  (only the small `playwright` npm pkg installed in `.ds-sync/`, no 200 MB browser download).
- **No `buildCmd`**: the converter IS the build. `npm run build` in app/ builds the app, not
  a library — irrelevant to the sync.

## WrittenGlyph (data-driven)

- Needs a real `DiagnosticData` payload. `.design-sync/previews/_writtenGlyphData.ts` is
  **codegen** from the LOCAL API — regenerate, don't hand-edit:
  `uv run uvicorn api.main:app` then
  `GET http://127.0.0.1:8000/sources/suetterlin-1922/templates/<key>/diagnostic`
  (keys used: `e-medial`, `t-medial`). NOTE: the local API serves at **root, no `/api`
  prefix** (the proxy adds `/api` in prod). **Prod is behind Cloudflare Access → no prod fetch.**
- The preview forces `prefers-reduced-motion` via a `matchMedia` shim so the frozen-clock
  capture renders the COMPLETE settled glyph; without it the CSS reveal animation is caught
  mid-stroke (half the ink hidden). Depends on `usePrefersReducedMotion` reading matchMedia
  at init.

## Known render warns

None outstanding. (GRID_OVERFLOW on PublicHeader was resolved with `cardMode: column`.)

## Re-sync risks (watch-list)

- `_writtenGlyphData.ts` is a diagnostic snapshot from sync time. If the ductus/template
  changes materially, regenerate it from the local API (keys above), rebuild, recapture.
- `conventions.md` repeats the palette hexes from `styles/paper.ts` §9. If the palette
  changes, update `conventions.md` (the conventions step name-checks fonts/components/dirs
  against the build, but NOT the literal hexes).
- New `@/` barrel-dir imports in a synced component → add to `tsconfig.designsync.json`.
- A synced component importing a NEW binary asset type the IIFE bundle's esbuild can't
  load (`.ttf`/`.otf`/`.eot` — `.svg/.png/.woff/.woff2` are fine) → bundle build fails
  with `No loader is configured for ".<ext>"`. Mirror the Suetterlin shim: exact
  `@/…/<file>` → empty-default `.ts` shim in `tsconfig.designsync.json` (only safe when
  no synced component RENDERS that asset). If it must inline, escalate (`cfg.libOverrides`
  fork of `lib/bundle.mjs`).
- Keep `tsconfig.designsync.json` parseable by the plugin's comment-stripper — see the
  cfg.tsconfig bullet above; a `//`-prefixed key silently kills all our `@/` overrides.
- The WrittenGlyph matchMedia shim assumes `usePrefersReducedMotion` reads matchMedia at
  init — revisit if that hook changes.
- The bundle is CSS-in-JS (MUI/emotion): `[CSS_RUNTIME]` is expected (self-styling), not a
  problem to chase.

## Re-sync command

```sh
DS_CHROMIUM_PATH=/usr/bin/google-chrome node .ds-sync/resync.mjs \
  --config .design-sync/config.json --node-modules ./app/node_modules \
  --out ./ds-bundle --remote .design-sync/.cache/remote-sync.json
```
(Fetch the project's `_ds_sync.json` → `.design-sync/.cache/remote-sync.json` first.)
```
