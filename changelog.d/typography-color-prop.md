### Fixed

- **The soft ink is back: `color="text.secondary"` was inert under MUI 9.**
  `Typography` resolves its `color` prop through theme variants only — the
  simple palette keys and the camel-case text keys
  `textPrimary`/`textSecondary`/`textDisabled`. A dotted path matched no
  variant and was silently swallowed, so 164 call sites across `app/src`
  stood in full ink instead of the colour the theme intends for them —
  visible on every admin page, in the quiz, on the 404 page and in the boot
  screen. Neither the type check nor `propTypes` catches it (the prop ends in
  `| (string & {})`), so `app/src/theme/paletteProp.guard.test.ts` now stands
  in the way: it reads the sources and rejects a dotted path on every
  component that resolves its colour through variants.
- **Ochre is a mark colour, not a text colour.** The eight sites that wanted
  `warning.main` or `success.main` as a text colour were inert for the same
  reason — and would not have been worth it as text either: `#cc7722` reaches
  3.37:1 on white, enough for a dot or a bar, too little for a caption. The
  warning lines stay ink and carry their meaning in words, the success lines
  take `paper.viridianText` (5.85:1), and the penalty bar beside them still
  carries severity as a graphic. The rule is written down in
  `docs/concepts/design-system.md` §2.
