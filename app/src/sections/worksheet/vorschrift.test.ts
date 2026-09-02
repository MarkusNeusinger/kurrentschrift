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
import {
  MAX_LINES,
  MAX_LINE_LEN,
  maxCharsPerLine,
  placeText,
  textLines,
  type InputLine,
  type TextLine,
} from '@/lib/uebungstext';

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

const written = (lines: TextLine[], overflow: InputLine[] = []) => ({
  lines,
  loading: false,
  failed: [],
  overflow,
});

describe('a Vorschrift line the ruling is too narrow for', () => {
  it('never leaves the page empty without saying so (37 characters at 6 mm)', () => {
    const lines = textLines(SENTENCE).lines.map((l) => ({ ...l, composed: composedOf(SENTENCE_UNITS) }));
    expect(lines[0].text).toHaveLength(37);
    const placed = placeText(lines, sheet.rows, placeOpts);

    // The line is not written — the Lineatur stays untouched, by decision.
    expect(placed.placed).toEqual([]);
    // …but it is named, with its row number and its length, and it is marked
    // on the sheet. THIS is the regression: an empty result with no note.
    expect(placed.tooWide).toEqual([{ no: 1, text: SENTENCE, typed: 37, chars: 37, fits: 23 }]);
    expect(placed.marks).toHaveLength(1);
    const status = textStatusOf(written(lines), placed, SUETTERLIN.xHeightMm);
    expect(status).not.toBeNull();
    expect(status!.error).toBe(true);
    expect(status!.text).toContain('Zeile 1');
    expect(status!.text).toContain('37 Zeichen');
    expect(status!.text).toContain('23');
  });

  it('owns the two caps the text field applies itself', () => {
    // Neither the 60-character cut nor the line cap may take its share in
    // silence — the same rule the too-wide line follows (review of #499).
    const long = 'x'.repeat(MAX_LINE_LEN + 8);
    // One over-long row plus MAX_LINES + 1 ordinary ones: two rows past the cap.
    const rows = Array.from({ length: MAX_LINES + 1 }, (_, i) => `Zeile ${i + 1}`);
    const read = textLines([long, ...rows].join('\n'));
    const lines = read.lines.map((l) => ({ ...l, composed: composedOf(2) }));
    const placed = placeText(lines, sheet.rows, { ...placeOpts, trace: false, practiceRows: 0 });
    const status = textStatusOf(written(lines, read.overflow), placed, 6)!;
    expect(status.error).toBe(true);
    expect(status.text).toContain(`Zeile 1 ist auf ${MAX_LINE_LEN} Zeichen gekürzt`);
    expect(status.text).toContain(String(MAX_LINE_LEN + 8));
    // The rows past the cap are named, not swallowed — here in one run with
    // the last row the A4 sheet itself has no space for.
    expect(read.overflow.map((l) => l.no)).toEqual([MAX_LINES + 1, MAX_LINES + 2]);
    expect(status.text).toMatch(new RegExp(`Für Zeile \\d+ bis ${MAX_LINES + 2} `));
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
    const lines = textLines(raw).lines.map((l) => ({
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
    expect(lineList([{ no: 3, text: 'a', typed: 1 }])).toBe('Zeile 3');
    expect(lineList([{ no: 3, text: 'a', typed: 1 }, { no: 4, text: 'b', typed: 1 }])).toBe('Zeile 3 und 4');
    expect(
      lineList([
        { no: 3, text: 'a', typed: 1 },
        { no: 4, text: 'b', typed: 1 },
        { no: 7, text: 'c', typed: 1 },
      ]),
    ).toBe('Zeile 3, 4 und 7');
    // Three or more in a row collapse — a full sheet leaves a dozen over, and
    // naming each one turns the sentence into a wall of numbers.
    const run = (from: number, to: number) =>
      Array.from({ length: to - from + 1 }, (_, i) => ({ no: from + i, text: 'x', typed: 1 }));
    expect(lineList(run(4, 15))).toBe('Zeile 4 bis 15');
    expect(lineList([...run(2, 4), { no: 9, text: 'x', typed: 1 }])).toBe('Zeile 2 bis 4 und 9');
  });

  it('reads the complaints in the order of the field, whatever their kind', () => {
    // A page with no rows at all: line 1 has nowhere to go, line 2 is also too
    // wide — the note must still start at line 1.
    const lines = textLines(`kurz\n${SENTENCE}`).lines.map((l) => ({
      ...l,
      composed: composedOf(l.text === SENTENCE ? SENTENCE_UNITS : 5),
    }));
    const placed = placeText(lines, [], placeOpts);
    const text = textStatusOf(written(lines), placed, 6)!.text;
    expect(text.indexOf('Für Zeile 1')).toBeLessThan(text.indexOf('Zeile 2 ist'));
  });

  it('does not group two no-row lines across a complaint that sits between them', () => {
    // Rows 1 and 3 have no room, row 2 is too wide: „Zeile 1 und 3 … · Zeile 2
    // …“ would read as a slip, so the run is only merged where it is a run
    // (review of #499). One row on the sheet, taken by the pending line 1.
    const lines = textLines(`eins\n${SENTENCE}\ndrei`).lines.map((l) => ({
      ...l,
      composed: composedOf(l.text === SENTENCE ? SENTENCE_UNITS : 5),
    }));
    const placed = placeText(lines, sheet.rows.slice(0, 1), { ...placeOpts, trace: false, practiceRows: 0 });
    expect(placed.noRow.map((l) => l.no)).toEqual([3]);
    const text = textStatusOf(written(lines), placed, 6)!.text;
    expect(text.indexOf('Zeile 2 ist')).toBeLessThan(text.indexOf('Für Zeile 3'));
    expect(text).not.toContain('Zeile 1 und 3');
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
