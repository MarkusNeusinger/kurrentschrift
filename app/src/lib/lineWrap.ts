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
// Since 2026-09-04 the same module also answers "where does it break BECAUSE
// the writer typed a break" (`planParagraphs`) and lays the text out at a
// chosen x-height instead of only at the floor (`targetXHeightPx`, the
// Federprobe's size ladder).
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

// The longest line a single composition request may carry. It is the practice
// sheet's own row length (`MAX_LINE_LEN`, lib/uebungstext.ts) — one written
// line is one written line, whether it goes to a printer or to the screen —
// and it sits far under the composer's per-request cap of 160 characters
// (api/routers/write.py), so a wrapped block never asks for more than the
// server will compose. In practice the x-height target bites long before this
// does; the cap is the guarantee, not the mechanism.
export const MAX_CHARS_PER_LINE = 60;

// The composer's own per-request cap (`MAX_TEXT_LEN`, api/routers/write.py):
// the longest text one `GET /write/word` accepts, over which it answers 422.
export const MAX_COMPOSE_CHARS = 160;

// The first run of non-space characters too long for ONE composition request,
// or null. It is the one input a line plan cannot rescue: breaking happens at
// spaces, so a run without any stays whole however narrow the frame — and past
// this length the composer refuses it outright.
//
// Reported rather than split, the way the practice sheet reports a row its
// ruling is too narrow for (`TooWideLine`, lib/uebungstext.ts): splitting a
// word without a hyphen invents a break the script never had, and splitting it
// WITH one is the claim about Sütterlin this project has not made. So the
// caller says what it cannot write and names it, instead of sending a request
// that is answered with an error.
export function tooLongRun(text: string, maxChars = MAX_COMPOSE_CHARS): string | null {
  for (const run of text.split(/\s+/)) if (run.length > maxChars) return run;
  return null;
}

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
  // The x-height the text should be WRITTEN at, px per template unit — the
  // Federprobe's size ladder (sections/scribe/size.ts, owner decision
  // 2026-09-04). It is an aim, not a promise: lines are packed so they land
  // near it, and a bigger aim therefore buys fewer characters per line and more
  // lines. Defaults to the floor, which is exactly what every other surface
  // asks for — "as much text per line as the Tintenboden allows".
  targetXHeightPx?: number;
  // Hard cap on a line's length, characters. Defaults to `MAX_CHARS_PER_LINE`.
  maxChars?: number;
}

// One planned line, and whether a paragraph gap precedes it.
export interface PlannedLine {
  text: string;
  // First line after a blank row in the typed text — the renderer spends an
  // extra leading on it.
  paragraphBreak: boolean;
}

// Break `text` into the lines the renderer should compose, or return it
// unbroken. Breaks happen at spaces only — never inside a word, because a
// hyphenated Sütterlin word would be a claim about the script the project has
// not made. The honest consequence: a SINGLE word wider than the frame stays
// one line and is written below the floor; there is nothing to break.
export function planLines(
  text: string,
  {
    availPx,
    unitsPerChar,
    padUnits = 0,
    minXHeightPx = MIN_XHEIGHT_PX,
    targetXHeightPx,
    maxChars = MAX_CHARS_PER_LINE,
  }: LinePlan,
): string[] {
  const words = text.split(/\s+/).filter(Boolean);
  // Nothing to break at, or nothing measured yet (a frame of 0 px is "not
  // measured", not "no room"): leave the text alone.
  if (words.length < 2 || !(availPx > 0) || !(unitsPerChar > 0) || !(minXHeightPx > 0)) return [text];

  // The size the split is planned FOR. A chosen size the frame cannot carry is
  // not a size, it is a promise the renderer has to break: since a word never
  // breaks, the widest word sets the block's scale, so planning above the
  // x-height at which THAT word still fits only shreds the text into one-word
  // lines that are then written smaller than asked anyway. So the aim is
  // clamped to what the longest word affords — the honest reading of "a word
  // that cannot fit at the chosen size falls below the chosen size" — and
  // never below the floor, which is the one number that is a promise.
  const longestWord = Math.max(...words.map((w) => w.length));
  const wordFitPx = availPx / (longestWord * unitsPerChar + padUnits);
  const target = Math.max(minXHeightPx, Math.min(targetXHeightPx ?? minXHeightPx, wordFitPx));

  // How many characters a line may carry before its x-height drops under the
  // target: the frame is worth `availPx / target` template units there, the
  // renderer's air comes off the top, the rest buys characters. Below one
  // character even a single letter sits under the target — breaking cannot
  // rescue that, so say so by not breaking.
  const budget = Math.min(Math.floor((availPx / target - padUnits) / unitsPerChar), maxChars);
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

// One typed row, read the way the composer reads a text: NFC like the server,
// whitespace runs collapsed, ends trimmed. The collapse is what guarantees the
// rule below — a newline is whitespace, so no planned line can carry one — and
// it also gives two texts that differ only in spacing ONE cache key.
const readRow = (row: string): string => row.normalize('NFC').replace(/\s+/g, ' ').trim();

// Break a typed text into the lines the renderer should compose: the typed
// breaks FIRST, then `planLines` inside each paragraph (owner decision
// 2026-09-04, „ein getippter Umbruch ist immer ein Umbruch"). A row the frame
// is too narrow for still wraps, so a hard break can only ever add breaks,
// never remove one.
//
// The row model is MIRRORED from the practice sheet's `textLines`
// (lib/uebungstext.ts) — same split, same per-row normalisation — rather than
// reused: that one drops empty rows and caps the sheet at `MAX_LINES`, and the
// Federprobe needs the blank rows precisely because a blank row is the
// paragraph gap it has to render.
//
// The blank-row rules, each because the alternative lies about the typing:
// one blank row is one paragraph gap; several in a row collapse into that same
// one gap (nobody means "four gaps" by four Enters, and the writing would fall
// out of the frame); leading and trailing blank rows are dropped, because a
// paragraph gap needs writing on both sides of it to be a gap at all.
//
// **No line this returns contains a newline** — that is the point. Each line
// becomes its own `GET /write/word`, and the composer treats a newline as an
// ordinary space (`core.shaping.shape_text`), so sending one would silently
// write the break as a gap in the middle of a line instead of as a break.
export function planParagraphs(text: string, plan: LinePlan): PlannedLine[] {
  const out: PlannedLine[] = [];
  let gapPending = false;
  for (const raw of text.split(/\r?\n/)) {
    const row = readRow(raw);
    if (!row) {
      // A blank row before any writing is not a gap, it is an empty start.
      gapPending = out.length > 0;
      continue;
    }
    planLines(row, plan).forEach((line, i) => out.push({ text: line, paragraphBreak: i === 0 && gapPending }));
    gapPending = false;
  }
  return out;
}
