// How big the Federprobe writes — the pure half of the Schriftgröße control
// (owner decision 2026-09-04: three steps, not a zoom; pinch zoom stays the
// browser's job and `app/index.html` leaves it alone).
//
// A step is a TARGET x-height in px per template unit. Template coordinates put
// the baseline at 0 and the midband at 1 (core/template.py), so one unit IS the
// written x-height: the step says "write this hand at 28 px x-height", and
// lib/lineWrap plans the line breaks for that size. A larger step therefore
// buys fewer characters per line and more lines — the accepted cost of bigger
// writing (the alternative, shrinking the hand to keep the line count, is the
// thing the Tintenboden was introduced against).

import { MIN_XHEIGHT_PX } from '@/lib/lineWrap';

export type ScribeSize = 'klein' | 'mittel' | 'gross';

// The ladder, in px per template unit.
//
// It is anchored on the one number the design system already fixes for written
// forms: the **Tintenboden of 14 px** (design-system.md §9). That floor is the
// ladder's zero rung — the size at which a written line is still readable, not
// one at which it is comfortable — and the three steps are √2 apart above it,
// the same ratio DIN paper and classic type scales use, so each step is a
// visible change rather than a nudge:
//
//   klein  = 14 · √2  ≈ 19.8 → 20
//   mittel = 14 · 2   =  28
//   gross  = 14 · 2√2 ≈ 39.6 → 40
//
// The rungs check out against what the page actually did before the control
// existed: a full desktop line measured **20.8 px per unit** at 1440 px
// (840 px `maxWidth` over a 29-character sentence, 2026-09-04) — so `klein`
// reproduces today's look and nothing is lost by adding the ladder, while
// `mittel`, the default, is 1.4× that and plainly larger. As a second reading:
// the Sütterlin school ruling writes a 6 mm Mittelband (`PRESETS`,
// lib/lineatur.ts), which is ~23 px at CSS 96 dpi — `mittel` is roughly an
// exercise book held at arm's length, `gross` is the same page brought close.
//
// The floor still wins where the frame is too narrow for the chosen step: the
// planner clamps the aim to what the longest (never-broken) word affords, and
// never below `MIN_XHEIGHT_PX`.
export const SCRIBE_SIZE_PX: Record<ScribeSize, number> = {
  klein: Math.round(MIN_XHEIGHT_PX * Math.SQRT2),
  mittel: MIN_XHEIGHT_PX * 2,
  gross: Math.round(MIN_XHEIGHT_PX * 2 * Math.SQRT2),
};

export const DEFAULT_SCRIBE_SIZE: ScribeSize = 'mittel';

// Where the viewer's own choice is remembered. Namespaced like a future second
// key would be, so `localStorage` stays readable in a debugger.
export const SCRIBE_SIZE_STORAGE_KEY = 'kurrentschrift:federprobe:size';

// An OWN-property check, not `in`: the value comes from a URL, and `in` walks
// the prototype chain — `?size=toString` would have named a step.
const isScribeSize = (value: unknown): value is ScribeSize =>
  typeof value === 'string' && Object.prototype.hasOwnProperty.call(SCRIBE_SIZE_PX, value);

/** A `?size=` value, or a stored one, if it names a step — otherwise null. */
export function parseScribeSize(value: string | null | undefined): ScribeSize | null {
  return isScribeSize(value) ? value : null;
}

/**
 * Which size a visit starts at. **The URL wins over the stored preference** so
 * a shared link reproduces the look its sender saw, whatever the recipient last
 * chose here; the stored choice answers every visit that carries no `?size=`.
 */
export function initialScribeSize(param: string | null | undefined, stored: string | null | undefined): ScribeSize {
  return parseScribeSize(param) ?? parseScribeSize(stored) ?? DEFAULT_SCRIBE_SIZE;
}

/** The remembered choice. Storage can throw outright (Safari's private mode, a
 * browser set to block site data) and can be absent entirely (anything running
 * this outside a browser), so a page without it must still render. Reached
 * through `globalThis` rather than `window` for exactly that second case — in
 * a browser the two are the same object. */
export function readStoredScribeSize(): ScribeSize | null {
  try {
    return parseScribeSize(globalThis.localStorage.getItem(SCRIBE_SIZE_STORAGE_KEY));
  } catch {
    return null;
  }
}

export function storeScribeSize(size: ScribeSize): void {
  try {
    globalThis.localStorage.setItem(SCRIBE_SIZE_STORAGE_KEY, size);
  } catch {
    /* no storage — the choice simply lasts for this visit */
  }
}
