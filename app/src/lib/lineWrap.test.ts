import { describe, expect, it } from 'vitest';

import { MIN_XHEIGHT_PX, planLines } from './lineWrap';

// The audit's own case (finding 28): "Der Schreiber grüßt ergebenst" on a
// 360 px phone. The measured composition was ~44.5 template units wide for 29
// characters, and the card left ~286 px for the ink.
const AUDIT_TEXT = 'Der Schreiber grüßt ergebenst';
const AUDIT_UNITS_PER_CHAR = 44.5 / AUDIT_TEXT.length;
const PHONE_PX = 286;
const DESKTOP_PX = 728;

describe('planLines', () => {
  it('leaves a line that clears the floor unbroken', () => {
    expect(planLines(AUDIT_TEXT, { availPx: DESKTOP_PX, unitsPerChar: AUDIT_UNITS_PER_CHAR })).toEqual([AUDIT_TEXT]);
  });

  it('breaks the audit sentence on a phone, and every line clears the floor', () => {
    const lines = planLines(AUDIT_TEXT, { availPx: PHONE_PX, unitsPerChar: AUDIT_UNITS_PER_CHAR });
    expect(lines.length).toBeGreaterThan(1);
    for (const line of lines) {
      expect(PHONE_PX / (line.length * AUDIT_UNITS_PER_CHAR)).toBeGreaterThanOrEqual(MIN_XHEIGHT_PX);
    }
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
});
