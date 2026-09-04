// Where a written text breaks into lines — the pure half of the Federprobe's
// Umbruch (owner decision 2026-09-04).
//
// The engine composes a whole text as ONE continuous run of pen strokes and the
// renderer scales that run into its frame. On a phone the frame is ~286 px, so
// a long sentence does not get smaller letters — it gets illegible ones: the
// 2026-09-02 site audit (finding 28) measured a 29-character sentence at 360 px
// landing on 7.1 px per template unit, i.e. an x-height of 7.1 px and 22.5 px
// of ink for the whole line.
//
// The decided answer is to break the text at word boundaries and let each line
// be composed and written as its OWN continuous stroke run — "Zug um Zug" then
// holds per line instead of per text, and every line start gets its proper
// Anstrich because shaping assigns the word position per slot. (The two
// rejected alternatives: a scale floor with a horizontally scrolling surface,
// and a viewport-coupled character cap with a notice.)
//
// This module answers only "where does it break"; components/WrittenWord owns
// the measuring, the per-line composition requests and the rendering.

// The floor a line must clear, in px per template unit. Template coordinates
// put the baseline at 0 and the midband at 1 (core/template.py), so one unit
// IS the written x-height — the floor reads "a written x-height never falls
// below 14 px".
//
// 14 px is the design system's own floor for the smallest type it allows
// (§9: "Caption ≥ 14 px"). Written forms get at least what printed type gets,
// and arguably need more: what tells a Sütterlin u from an n, or a loop from a
// Spitze, sits INSIDE the x-height band and is a fraction of it, while a
// printed letter's distinguishing parts are the whole glyph. It is also twice
// the 7.1 px the audit called unreadable, and it leaves the surfaces that
// already write above it untouched (the landing hero's one-word line, every
// quiz word) — a single word never breaks anyway, see below.
export const MIN_XHEIGHT_PX = 14;

export interface LinePlan {
  // Width available for the ink in px: the measured frame, capped by the
  // caller's own maxWidth.
  availPx: number;
  // Average advance per character in template units, measured on the
  // composition of the WHOLE text — so the estimate carries the actual hand
  // (a wide Laufform fits fewer characters per line than a narrow one) instead
  // of a hard-coded average. It is an average: a line of narrow letters ends
  // up a little above the floor, one of wide letters a little below. The
  // practice sheet's `AVG_ADVANCE_UNITS` (1.55, lib/uebungstext.ts) is the
  // same quantity measured once over the alphabet; its `maxCharsPerLine` is
  // this budget in mm. Here the number comes per text, because the text has
  // already been composed by the time the question is asked.
  unitsPerChar: number;
  // Template units the renderer spends on air around a line rather than on
  // letters (WrittenWord frames each line with a hairline on both sides). They
  // scale with the writing, so they come out of the budget: a plan that ignores
  // them promises the line more room than it gets and lands just under the
  // floor — /lesen/vergleichen's "Muhme Wittib" did, at 13.9 px.
  padUnits?: number;
  minXHeightPx?: number;
}

// Break `text` into the lines the renderer should compose, or return it
// unbroken. Breaks happen at spaces only — never inside a word, because a
// hyphenated Sütterlin word would be a claim about the script the project has
// not made. The honest consequence: a SINGLE word wider than the frame stays
// one line and is written below the floor; there is nothing to break.
export function planLines(
  text: string,
  { availPx, unitsPerChar, padUnits = 0, minXHeightPx = MIN_XHEIGHT_PX }: LinePlan,
): string[] {
  const words = text.split(/\s+/).filter(Boolean);
  // Nothing to break at, or nothing measured yet (a frame of 0 px is "not
  // measured", not "no room"): leave the text alone.
  if (words.length < 2 || !(availPx > 0) || !(unitsPerChar > 0) || !(minXHeightPx > 0)) return [text];

  // How many characters a line may carry before its x-height drops under the
  // floor: the frame is worth `availPx / floor` template units at the floor,
  // the renderer's air comes off the top, the rest buys characters. Below one
  // character even a single letter sits under the floor — breaking cannot
  // rescue that, so say so by not breaking.
  const budget = Math.floor((availPx / minXHeightPx - padUnits) / unitsPerChar);
  if (budget < 1 || budget >= text.length) return [text];

  const lines: string[] = [];
  let line = '';
  for (const word of words) {
    if (!line) line = word;
    else if (line.length + 1 + word.length <= budget) line += ` ${word}`;
    else {
      lines.push(line);
      line = word;
    }
  }
  if (line) lines.push(line);
  return lines;
}
