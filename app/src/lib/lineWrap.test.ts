import { describe, expect, it } from 'vitest';

import { MAX_CHARS_PER_LINE, MIN_XHEIGHT_PX, planLines, planParagraphs } from './lineWrap';

// The audit's own case (finding 28): "Der Schreiber grüßt ergebenst" on a
// 360 px phone. The measured composition was ~44.5 template units wide for 29
// characters, and the card left ~286 px for the ink.
const AUDIT_TEXT = 'Der Schreiber grüßt ergebenst';
const AUDIT_UNITS_PER_CHAR = 44.5 / AUDIT_TEXT.length;
const PHONE_PX = 286;
const DESKTOP_PX = 728;
// What WrittenWord's viewBox keeps free at both ends of a line.
const PAD = 0.3;

// The x-height a line of `chars` characters is written at — the promise the
// floor makes, measured the way the renderer computes it.
const xHeightPx = (chars: number, availPx = PHONE_PX, padUnits = 0) =>
  availPx / (chars * AUDIT_UNITS_PER_CHAR + padUnits);

describe('planLines', () => {
  it('leaves a line that clears the floor unbroken', () => {
    expect(planLines(AUDIT_TEXT, { availPx: DESKTOP_PX, unitsPerChar: AUDIT_UNITS_PER_CHAR })).toEqual([AUDIT_TEXT]);
  });

  it('breaks the audit sentence on a phone, and every line clears the floor', () => {
    const lines = planLines(AUDIT_TEXT, { availPx: PHONE_PX, unitsPerChar: AUDIT_UNITS_PER_CHAR });
    expect(lines.length).toBeGreaterThan(1);
    for (const line of lines) {
      expect(xHeightPx(line.length)).toBeGreaterThanOrEqual(MIN_XHEIGHT_PX);
    }
  });

  it('spends the padding around a line before it spends characters', () => {
    const withPad = planLines(AUDIT_TEXT, { availPx: PHONE_PX, unitsPerChar: AUDIT_UNITS_PER_CHAR, padUnits: PAD });
    for (const line of withPad) {
      // The floor holds against the width the line is ACTUALLY given, air
      // included — ignoring the pad is what put "Muhme Wittib" at 13.9 px.
      expect(xHeightPx(line.length, PHONE_PX, PAD)).toBeGreaterThanOrEqual(MIN_XHEIGHT_PX);
    }
    // And it never buys a longer line than the padless plan would.
    const padless = planLines(AUDIT_TEXT, { availPx: PHONE_PX, unitsPerChar: AUDIT_UNITS_PER_CHAR });
    expect(Math.max(...withPad.map((l) => l.length))).toBeLessThanOrEqual(Math.max(...padless.map((l) => l.length)));
  });

  it('keeps the words and their order', () => {
    const lines = planLines(AUDIT_TEXT, { availPx: PHONE_PX, unitsPerChar: AUDIT_UNITS_PER_CHAR });
    expect(lines.join(' ')).toBe(AUDIT_TEXT);
  });

  it('breaks only at spaces — a single over-long word stays one line', () => {
    const word = 'Donaudampfschifffahrtsgesellschaft';
    expect(planLines(word, { availPx: 60, unitsPerChar: 1.5 })).toEqual([word]);
  });

  it('gives an over-long word its own line instead of splitting it', () => {
    expect(planLines('im Donaudampfschiff fahren', { availPx: 100, unitsPerChar: 1.5 })).toEqual([
      'im',
      'Donaudampfschiff',
      'fahren',
    ]);
  });

  it('leaves the text alone while the frame is unmeasured', () => {
    expect(planLines(AUDIT_TEXT, { availPx: 0, unitsPerChar: AUDIT_UNITS_PER_CHAR })).toEqual([AUDIT_TEXT]);
    expect(planLines(AUDIT_TEXT, { availPx: PHONE_PX, unitsPerChar: 0 })).toEqual([AUDIT_TEXT]);
  });

  it('does not break when not even one character would clear the floor', () => {
    expect(planLines('ein Satz', { availPx: 10, unitsPerChar: 1.5 })).toEqual(['ein Satz']);
  });

  it('collapses the whitespace it breaks on', () => {
    expect(planLines('ein   zwei', { availPx: 60, unitsPerChar: 1.5 })).toEqual(['ein', 'zwei']);
  });

  it('honours a caller-supplied floor', () => {
    const generous = planLines(AUDIT_TEXT, { availPx: PHONE_PX, unitsPerChar: AUDIT_UNITS_PER_CHAR, minXHeightPx: 28 });
    const strict = planLines(AUDIT_TEXT, { availPx: PHONE_PX, unitsPerChar: AUDIT_UNITS_PER_CHAR });
    expect(generous.length).toBeGreaterThan(strict.length);
  });

  // ---------------------------------------------- the chosen size (Federprobe)

  it('buys fewer characters per line the larger the chosen x-height', () => {
    // A postcard's worth of text — the 29-character audit sentence fits on two
    // desktop lines at every step and could not tell them apart.
    const postcard = `${AUDIT_TEXT}. ${AUDIT_TEXT}. ${AUDIT_TEXT}. ${AUDIT_TEXT}`;
    const plan = (targetXHeightPx: number) =>
      planLines(postcard, { availPx: DESKTOP_PX, unitsPerChar: AUDIT_UNITS_PER_CHAR, targetXHeightPx });
    const [klein, mittel, gross] = [20, 28, 40].map(plan);
    // The ladder is monotone — bigger writing, never fewer lines — and it does
    // move: two adjacent steps can land on the same count, because words pack
    // in whole units and a budget of 23 characters holds the same words as one
    // of 22, but across the ladder the difference is real.
    expect(klein.length).toBeLessThanOrEqual(mittel.length);
    expect(mittel.length).toBeLessThanOrEqual(gross.length);
    expect(klein.length).toBeLessThan(gross.length);
    // …and every step still says the same text.
    for (const lines of [klein, mittel, gross]) expect(lines.join(' ')).toBe(postcard);
  });

  it('defaults to the floor, which is what every surface but the Federprobe asks for', () => {
    const opts = { availPx: PHONE_PX, unitsPerChar: AUDIT_UNITS_PER_CHAR };
    expect(planLines(AUDIT_TEXT, opts)).toEqual(planLines(AUDIT_TEXT, { ...opts, targetXHeightPx: MIN_XHEIGHT_PX }));
  });

  it('drops an aim the longest word cannot fit at, rather than shredding the text', () => {
    // 40 px per unit on a phone would leave room for ~4 characters, so every
    // word would sit alone AND still be written smaller than asked. The plan
    // falls back to the size the widest (never-broken) word affords.
    const shredded = planLines(AUDIT_TEXT, {
      availPx: PHONE_PX,
      unitsPerChar: AUDIT_UNITS_PER_CHAR,
      targetXHeightPx: 40,
    });
    const longest = Math.max(...AUDIT_TEXT.split(' ').map((w) => w.length));
    expect(Math.max(...shredded.map((l) => l.length))).toBeGreaterThanOrEqual(longest);
  });

  it('never plans below the floor, however small the aim', () => {
    const opts = { availPx: PHONE_PX, unitsPerChar: AUDIT_UNITS_PER_CHAR };
    // An aim under the Tintenboden would buy LONGER lines than the floor
    // allows — the floor is the one number that is a promise.
    expect(planLines(AUDIT_TEXT, { ...opts, targetXHeightPx: 4 })).toEqual(planLines(AUDIT_TEXT, opts));
  });

  it('keeps every line inside the hard cap, however wide the frame', () => {
    const text = Array.from({ length: 40 }, (_, i) => `wort${i}`).join(' ');
    const lines = planLines(text, { availPx: 100_000, unitsPerChar: AUDIT_UNITS_PER_CHAR });
    expect(lines.length).toBeGreaterThan(1);
    for (const line of lines) expect(line.length).toBeLessThanOrEqual(MAX_CHARS_PER_LINE);
  });
});

describe('planParagraphs', () => {
  const OPTS = { availPx: DESKTOP_PX, unitsPerChar: AUDIT_UNITS_PER_CHAR };

  it('makes every typed break a break', () => {
    expect(planParagraphs('erste Zeile\nzweite Zeile', OPTS)).toEqual([
      { text: 'erste Zeile', paragraphBreak: false },
      { text: 'zweite Zeile', paragraphBreak: false },
    ]);
  });

  it('marks one paragraph gap for a blank row, and only one however many', () => {
    const one = planParagraphs('oben\n\nunten', OPTS);
    const many = planParagraphs('oben\n\n\n\n\nunten', OPTS);
    expect(one).toEqual([
      { text: 'oben', paragraphBreak: false },
      { text: 'unten', paragraphBreak: true },
    ]);
    expect(many).toEqual(one);
  });

  it('drops leading and trailing blank rows', () => {
    expect(planParagraphs('\n\n  \nmitten\n\n\n', OPTS)).toEqual([{ text: 'mitten', paragraphBreak: false }]);
  });

  it('still wraps a typed row the frame is too narrow for', () => {
    const lines = planParagraphs(`kurz\n\n${AUDIT_TEXT}`, { availPx: PHONE_PX, unitsPerChar: AUDIT_UNITS_PER_CHAR });
    expect(lines.length).toBeGreaterThan(2);
    // The typed break survives the wrap: the paragraph's FIRST line carries it.
    expect(lines[0]).toEqual({ text: 'kurz', paragraphBreak: false });
    expect(lines[1].paragraphBreak).toBe(true);
    expect(lines.slice(2).every((l) => !l.paragraphBreak)).toBe(true);
    expect(lines.slice(1).map((l) => l.text).join(' ')).toBe(AUDIT_TEXT);
  });

  it('never hands a newline to the composer', () => {
    // Each line becomes its own `GET /write/word`, and the server reads a
    // newline as an ordinary space — it would write the break as a gap.
    const messy = '\r\nLiebe  Großmutter,\r\n\r\n heute schreibe ich \n\n Dir.\n';
    for (const line of planParagraphs(messy, OPTS)) {
      expect(line.text).not.toMatch(/[\r\n]/);
      expect(line.text).toBe(line.text.trim());
      expect(line.text).not.toMatch(/\s\s/);
    }
  });

  it('reads a text without breaks exactly as planLines does', () => {
    const opts = { availPx: PHONE_PX, unitsPerChar: AUDIT_UNITS_PER_CHAR };
    expect(planParagraphs(AUDIT_TEXT, opts).map((l) => l.text)).toEqual(planLines(AUDIT_TEXT, opts));
    expect(planParagraphs(AUDIT_TEXT, opts).some((l) => l.paragraphBreak)).toBe(false);
  });

  it('has nothing to plan for an empty text', () => {
    expect(planParagraphs('   \n\n  ', OPTS)).toEqual([]);
  });
});
