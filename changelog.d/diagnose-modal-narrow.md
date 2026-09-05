### Fixed

- **The penalty breakdown no longer writes „Deckungslücke" across its own
  bar.** The label column was a hard-coded 78 px — about nine characters of the
  monospace face it is set in — so the longest category name of the Sütterlin
  naturalness metric ran 32 px past its box and painted over the bar it belongs
  to, at every viewport. The column is measured from the labels themselves now
  (`labelColumnChars`, in `ch` because the face is monospace, and over the whole
  category set rather than the rows that happen to clear `PENALTY_EPS`), so the
  bars stay aligned across both cards and a renamed category re-measures itself
  instead of clipping. Pinned by `labelColumn.test.ts`. Only the Sütterlin
  metric reaches this surface at all: the Kurrent metric returns no
  `components`, so its cards carry no per-category breakdown.

- **The Diagnose modal stops scrolling sideways on a phone.** Its
  processing-stage columns were sized from `window.innerWidth − 64`, which is
  the page's gutter and not the modal's: the paper is a further 32 px narrower
  and pads another 32 px inside, so at 390 px every column stood 47 px wider
  than the box holding it, the dialog scrolled horizontally and the crop was cut
  off at the right edge. `useColumnWidth` now measures the container it is
  handed instead of the window — through a `ResizeObserver`, so a breakpoint
  change or the modal's own scrollbar re-measures too — and the dialog goes
  full-screen below `md` like the setup wizard, which buys back the 64 px of
  margin. Desktop is unchanged (420 px columns at 1440 px). The two score cards
  were already stacking at that width; they were not the cause.
