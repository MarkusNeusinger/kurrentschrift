### Changed

- **The ESLint parking lot is empty, and the gate now holds it there.** The 69
  warnings issue #227 parked — 35 `react-hooks/set-state-in-effect`, 25
  `react-refresh/only-export-components`, 4 `react-hooks/refs`, 4
  `react-hooks/exhaustive-deps` — are gone, rule by rule and without a single
  `eslint-disable`. The three `warn` downgrades in `eslint.config.js` are
  deleted, so those rules sit at `error` from the react-hooks preset, and
  `npm run lint` runs with `--max-warnings 0`: the next warning of any rule
  fails CI instead of joining a list.
- **State that belongs to a prop is now adjusted during render, not after
  it.** Every "reset when the input changes" effect became React's documented
  render-phase guard (`if (shownFor !== key) { setShownFor(key); …reset… }`).
  This is not only quieter but more correct: the reset lands in the SAME paint
  as the change, so a reused instance no longer shows one frame of the previous
  glyph's error line, the previous word's ink, or the previous source's
  workbench rows.
- **Contexts, route tables and shared constants are their own modules.** A file
  that exports a provider next to its hook — or a route table next to the
  components it names — takes no Fast-Refresh update, so editing the workbench
  provider reloaded the whole admin. `adminState.ts`, `korbState.ts`,
  `workbenchState.ts`, `publicPages.tsx`, `adminPages.tsx`, `RootBoundary.tsx`,
  `PageContainer/widths.ts` and `inkReveal/inkGroupSx.ts` split those apart; no
  behaviour moved with them.

### Fixed

- **The latest-ref writes moved out of the render phase.** Four hooks kept a
  callback or a snapshot current with `ref.current = value` during render,
  which is unsound under concurrent rendering. Each now writes in an effect —
  safe in every case, because the only readers are async continuations and DOM
  event handlers, which cannot run between render and commit.
- **`useElementSize` no longer measures twice.** The explicit first
  `setSize` beside `observe()` duplicated the initial callback a
  ResizeObserver delivers on its own for a rendered element, still before
  paint.
- **Two memoised lists stopped invalidating themselves every render.** The
  letter and join views built their `occurrences` array with `?? []`, handing
  the dependent `useMemo`s a fresh identity on each pass; the workbench context
  value omitted two callbacks it reads.
