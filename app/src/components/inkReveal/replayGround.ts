// Ground for the ↺ so it never lands on the writing.
//
// `ReplayButton` hangs `position: absolute; bottom: 4; right: 4` INSIDE the ink
// box (inkReveal/index.tsx). Wherever that box collapses to the aspect of the
// writing, the button sits on the last letters — measured on the live page
// (site audit 2026-09-02, finding 28): on /federprobe at 390 px the 30 × 30
// rect overlapped the last glyph's bounding box, and in the quiz it sat inside
// a 62.5 px wide letter box, reading like a part of the letter on the very page
// that asks the reader to tell letter forms apart.
//
// Three tiers, in the order a hand would try them:
//
//   1. STEP ASIDE, comfortably — the white frames are wider than the ink on
//      every surface that shows the button, so the box takes a full gutter on
//      each side (the ink stays centred) and the button hangs in the right one.
//   2. STEP ASIDE, as far as the frame allows — a frame too narrow for the
//      comfortable gutter can still be wide enough to keep the button clear of
//      the ink. That takes only the button's own footprint, not a hit target.
//   3. RESERVE A FLOOR — where the writing genuinely fills the frame's width (a
//      wrapped line on a phone), there is nowhere to step, so the box grows and
//      the button gets its ground under the writing.
//
// The tiers are exhaustive, so the returned box never overlaps its ink — an
// unmeasured frame (`frameW` 0) falls to tier 3, which cannot overflow anything.

// The comfortable gutter is one hit target wide (design-system §9.3: 44 px).
export const REPLAY_GUTTER = 44;
// What the button actually occupies, and therefore the least clear ground that
// keeps it off the ink: 30 px of optics plus its 4 px inset. Its invisible 44 px
// hit area may reach over the writing — a target is not a mark.
export const REPLAY_CLEAR = 34;

// `frameW` is the measured width of the frame the ink sits in; 0 means "not
// measured yet", which takes tier 3. The box centres its ink, so a vertical
// reservation is split between top and bottom — it takes TWO gutters to leave
// one of them below the writing.
export function replayGround(inkW: number, inkH: number, frameW: number): { width?: number; minHeight?: number } {
  // Compared against the frame, never against `width - inkW`: subtracting the
  // two floats back apart left the quiz box one ulp under the gutter it had
  // just been given, and it reserved vertically in a frame with room to spare.
  if (frameW >= inkW + 2 * REPLAY_GUTTER) return { width: inkW + 2 * REPLAY_GUTTER };
  if (frameW >= inkW + 2 * REPLAY_CLEAR) return { width: frameW };
  return { width: frameW > 0 ? frameW : undefined, minHeight: inkH + 2 * REPLAY_GUTTER };
}
