// The one keyboard-focus ring of the site: 2px viridian, held off the element
// so it reads on the paper ground (design-system.md §9.1).
//
// It lived as a module-private const inside `theme/components.ts`, where the
// three MUI rules that use it are. That covered every ButtonBase, Chip and Link
// — and left every HAND-ROLLED focusable with no way to wear the same ring: the
// Eigenhand coverage cells are bare `<button>` elements with `appearance:none`,
// and a bare button shows nothing at all once MUI's reset has run. So the token
// moves here, beside `hitArea` — the other shared operability token — and
// `theme/components.ts` imports it instead of declaring it.
//
// Use it, never a hand-written outline: a second `2px solid` somewhere in a
// component file is how the ring drifts to a different colour or offset and
// stops reading as one ring.

import { paper } from '@/styles/paper';

/** Ring width in CSS px. */
export const FOCUS_RING_WIDTH = 2;
/** Distance between the element's border box and the ring, in CSS px. */
export const FOCUS_RING_OFFSET = 2;

/**
 * The ring itself. Spread it into the state selector the element actually
 * uses: `'&.Mui-focusVisible'` for MUI components, `'&:focus-visible'` for a
 * plain DOM element.
 */
export const focusRing = {
  outline: `${FOCUS_RING_WIDTH}px solid ${paper.viridian}`,
  outlineOffset: FOCUS_RING_OFFSET,
} as const;

/**
 * Ready-made `sx` for a hand-rolled focusable (a raw `<button>`, an `<a>` that
 * is not a `MuiLink`). MUI components get the ring from the theme and need
 * nothing here.
 */
export const focusRingSx = { '&:focus-visible': focusRing } as const;
