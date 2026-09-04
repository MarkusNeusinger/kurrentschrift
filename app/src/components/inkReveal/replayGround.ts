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
// The white frames are wider than the ink on every surface that shows the
// button, so the first choice is to STEP ASIDE: widen the box by a gutter on
// each side, keep the ink centred, and let the button hang in the right-hand
// one. Where the frame is as narrow as the ink — a full-width written line on a
// phone — there is nowhere to step aside, so the box reserves a gutter above
// and below instead and the button gets its ground under the writing.

// A gutter is one hit target wide (design-system §9.3: 44 px), which also
// clears the button's 30 px optics plus its 4 px inset with room to spare.
export const REPLAY_GUTTER = 44;

// `frameW` is the measured width of the frame the ink sits in; 0 means "not
// measured yet". The box centres its ink, so a vertical reservation is split
// between top and bottom — it takes TWO gutters to leave one of them below the
// writing.
export function replayGround(
  inkW: number,
  inkH: number,
  frameW: number,
  // Whether the box may grow TALLER where it cannot step aside. A written LINE
  // legitimately fills its frame's width, so it needs that fallback. A single
  // glyph never does — the audit's own case was 62.5 px of letter in a 290 px
  // card — and the admin builds fixed-size cells out of glyph boxes (the setup
  // wizard's overview grid), which growing one from the inside would break. So
  // the glyph keeps the box it has where there is nowhere to step, which is
  // exactly today's behaviour.
  { floor = true }: { floor?: boolean } = {},
): { width?: number; minHeight?: number } {
  const wanted = inkW + 2 * REPLAY_GUTTER;
  // Compared against the frame, not against `width - inkW`: subtracting the two
  // floats back apart left the quiz box one ulp under the gutter it had just
  // been given, and it reserved vertically in a frame with room to spare.
  const stepsAside = frameW >= wanted;
  return {
    width: frameW > 0 ? Math.min(frameW, wanted) : undefined,
    minHeight: stepsAside || !floor ? undefined : inkH + 2 * REPLAY_GUTTER,
  };
}
