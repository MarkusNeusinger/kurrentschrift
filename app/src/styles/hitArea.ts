// One shared touch-target helper. Platform guidance (Apple HIG 44 pt, Material
// 48 dp) asks for ~44px in the smaller edge; several controls here are
// deliberately small as MARKS — the replay ↻ over the ink, the Kurrent-i of
// InfoHint, the quiet "beenden" text. Making them physically bigger would
// shout where the design whispers, so instead they keep their optics and grow
// an invisible pseudo-element that catches the thumb.
//
// design-system.md §9 carries the rule; this file is its one implementation, so
// the next small control inherits the fix instead of re-inventing it.

import type { SystemStyleObject, Theme } from '@mui/system';

/** The touch-target floor in CSS px (design-system.md §9). */
export const TOUCH_TARGET = 44;

/**
 * Grow an element's hit area to at least `size` px in both edges without
 * touching its optics. The pseudo-element is centred on the control, so the
 * extra area spreads evenly; `max(100%, …)` never SHRINKS a control that is
 * already larger.
 *
 * The host needs a positioning context — the helper sets `position: relative`
 * itself, so a caller that positions the control absolutely must spread this
 * helper FIRST and let its own `position: absolute` win.
 *
 * Returns a plain style object rather than `SxProps` so callers can spread it
 * into the `sx={[…]}` array form — `SxProps` is itself a union with an array
 * member and would not compose.
 */
export const hitArea = (size: number = TOUCH_TARGET): SystemStyleObject<Theme> => ({
  position: 'relative',
  '&::after': {
    content: '""',
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: `max(100%, ${size}px)`,
    height: `max(100%, ${size}px)`,
  },
});
