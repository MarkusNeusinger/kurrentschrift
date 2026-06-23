// design-sync shim — resolves PaperBackground's
// `import suetterlinTtf from '@/assets/fonts/suetterlin-hjz-1911.ttf'`.
//
// Why this exists:
//  1. The IIFE bundle's esbuild loader map (lib/bundle.mjs) has no `.ttf`
//     loader and exposes no config hook for it, and lib/bundle.mjs must not be
//     forked (it defines the app self-check's output contract). Mapping the
//     exact asset specifier to this `.ts` module via cfg.tsconfig's paths is
//     the config-only way to keep the bundle building.
//  2. None of the six synced components render text in the Suetterlin face —
//     PaperBackground injects that @font-face globally only so OTHER app pages
//     (landing hero, /schriftkunde specimens) can show it. Shipping it as a
//     settable face in the design system would also contradict the brand's
//     binding legibility rule (historic scripts only as marked specimens).
//
// So the import resolves to an empty src: PaperBackground emits an inert
// `@font-face { font-family:'Suetterlin'; src:url() }` that no design uses,
// and the bundle carries no 82 KB TTF dead weight. GLKurrent (a `.woff2`,
// loader present) still inlines normally and InfoHint's mark renders.
export default '';
