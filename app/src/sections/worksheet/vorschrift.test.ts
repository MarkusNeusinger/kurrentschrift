// The Vorschrift chain of the worksheet page, from the raw text field to the
// sentence under it: textLines → the server's composition → placeText →
// status.ts. This is the half `useWorksheetText` feeds, tested without React
// (the suite has no DOM environment; the hook itself is a debounce and a cache
// around fetchRenderWord, and its own contract is pinned in lib/api).
//
// The case that earns the file: the website audit of 2026-09-02 found a plain
// German sentence produce a completely empty A4 sheet with no hint anywhere on
// the page, while the help text promised 60 characters a line. The numbers
// below are the measured ones from that day.

import { describe, expect, it } from 'vitest';

import type { ComposedWordOut } from '@/lib/api';
import { buildLineature, PRESETS } from '@/lib/lineatur';
import { maxCharsPerLine, placeText, textLines, type TextLine } from '@/lib/uebungstext';

import { lineList, scriptMismatchNote, sheetNoteOf, textStatusOf } from './status';

// The sentence the audit typed, and what the live composer answered for it on
// 2026-09-02 (GET /write/word, suetterlin-1922): 46.268 template units wide.
// A single item is enough — placeText reads `bounds` for the width verdict.
const SENTENCE = 'heute schreibe ich Dir aus Straßburg.';
const SENTENCE_UNITS = 46.268;

const composedOf = (units: number): ComposedWordOut => ({
  text: SENTENCE,
  items: [
    {
      centerline: [
        [0, 0],
        [units, 1],
      ],
      stroke_width: 0.1,
      mask_width: 0.3,
      lift: false,
    },
  ],
  bounds: { min_x: 0, max_x: units, min_y: 0, max_y: 1 },
  guides: { baseline: 0, midband: 1, ascender: 2, descender: -1 },
  missing: [],
});

// The sheet the audit had on screen: the Sütterlin preset (6 mm Mittellänge,
// 15 mm margin), nothing else touched.
const SUETTERLIN = PRESETS.find((p) => p.id === 'suetterlin')!;
const sheet = buildLineature(SUETTERLIN);
const placeOpts = {
  xHeightMm: SUETTERLIN.xHeightMm,
  trace: true,
  practiceRows: 2,
  left: SUETTERLIN.marginMm,
  right: 210 - SUETTERLIN.marginMm,
};

const written = (lines: TextLine[]) => ({ lines, loading: false, failed: [] });

describe('a Vorschrift line the ruling is too narrow for', () => {
  it('never leaves the page empty without saying so (37 characters at 6 mm)', () => {
    const lines = textLines(SENTENCE).map((l) => ({ ...l, composed: composedOf(SENTENCE_UNITS) }));
    expect(lines[0].text).toHaveLength(37);
    const placed = placeText(lines, sheet.rows, placeOpts);

    // The line is not written — the Lineatur stays untouched, by decision.
    expect(placed.placed).toEqual([]);
    // …but it is named, with its row number and its length, and it is marked
    // on the sheet. THIS is the regression: an empty result with no note.
    expect(placed.tooWide).toEqual([{ no: 1, text: SENTENCE, chars: 37, fits: 23 }]);
    expect(placed.marks).toHaveLength(1);
    const status = textStatusOf(written(lines), placed, SUETTERLIN.xHeightMm);
    expect(status).not.toBeNull();
    expect(status!.error).toBe(true);
    expect(status!.text).toContain('Zeile 1');
    expect(status!.text).toContain('37 Zeichen');
    expect(status!.text).toContain('23');
  });

  it('promises the number of characters that actually fit, not the field cap', () => {
    // The help text used to say 60 — the textarea's own cap — while 20
    // characters already ran off the row at this Mittellänge.
    const fits = maxCharsPerLine(SUETTERLIN.xHeightMm, SUETTERLIN.marginMm, 210 - SUETTERLIN.marginMm);
    expect(fits).toBeGreaterThan(14); // the audit still saw 15 characters set
    expect(fits).toBeLessThan(20); // and none at 20
  });

  it('names the second row when the second line is the long one', () => {
    const raw = `Meine liebe Muhme,\n${SENTENCE}`;
    const lines = textLines(raw).map((l) => ({
      ...l,
      composed: composedOf(l.text === SENTENCE ? SENTENCE_UNITS : 28.44),
    }));
    const placed = placeText(lines, sheet.rows, placeOpts);
    expect(placed.placed).toEqual(['Meine liebe Muhme,']);
    expect(placed.tooWide.map((l) => l.no)).toEqual([2]);
    expect(textStatusOf(written(lines), placed, 6)!.text).toContain('Zeile 2');
  });
});

describe('the page speaks for itself', () => {
  it('names the rows it has no room for as a person would read them', () => {
    expect(lineList([{ no: 3, text: 'a' }])).toBe('Zeile 3');
    expect(lineList([{ no: 3, text: 'a' }, { no: 4, text: 'b' }])).toBe('Zeile 3 und 4');
    expect(
      lineList([
        { no: 3, text: 'a' },
        { no: 4, text: 'b' },
        { no: 7, text: 'c' },
      ]),
    ).toBe('Zeile 3, 4 und 7');
  });

  it('reads the complaints in the order of the field, whatever their kind', () => {
    // A page with no rows at all: line 1 has nowhere to go, line 2 is also too
    // wide — the note must still start at line 1.
    const lines = textLines(`kurz\n${SENTENCE}`).map((l) => ({
      ...l,
      composed: composedOf(l.text === SENTENCE ? SENTENCE_UNITS : 5),
    }));
    const placed = placeText(lines, [], placeOpts);
    const text = textStatusOf(written(lines), placed, 6)!.text;
    expect(text.indexOf('Für Zeile 1')).toBeLessThan(text.indexOf('Zeile 2 ist'));
  });

  it('says that the Vorschrift is Sütterlin under any other ruling', () => {
    expect(scriptMismatchNote('kurrent', 'lesen')).toContain('Kurrent');
    expect(scriptMismatchNote('offenbacher', 'lesen')).toContain('Offenbacher');
    // Nothing to warn about: same script, no text, or a hand-made setting
    // that claims no script at all.
    expect(scriptMismatchNote('suetterlin', 'lesen')).toBeNull();
    expect(scriptMismatchNote('kurrent', '   ')).toBeNull();
    expect(scriptMismatchNote('', 'lesen')).toBeNull();
  });

  it('explains an empty sheet instead of offering it as a PDF', () => {
    expect(sheetNoteOf(SUETTERLIN, sheet.rows.length)).toBeNull();
    // 99 parts of Oberlänge — the audit's typo — leaves no row on A4.
    const tall = { ...SUETTERLIN, ratioAscender: 99 };
    expect(sheetNoteOf(tall, buildLineature(tall).rows.length)).toBe(
      'Bei dieser Einstellung passt keine einzige Zeile auf das Blatt — eine kleinere Mittellänge, ein flacheres Verhältnis oder ein schmalerer Seitenrand bringt die Lineatur zurück.',
    );
    // A field cleared mid-edit is not a mistake, only unfinished.
    const clearing = { ...SUETTERLIN, xHeightMm: NaN };
    expect(sheetNoteOf(clearing, buildLineature(clearing).rows.length)).toContain('Ein Feld ist gerade leer');
  });
});
