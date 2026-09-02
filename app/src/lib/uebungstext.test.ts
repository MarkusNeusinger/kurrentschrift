import { describe, expect, it } from 'vitest';

import type { ComposedWordOut } from './api';
import { buildLineature, PRESETS, type RowMetrics } from './lineatur';
import { lineaturePdf } from './pdf';
import {
  AVG_ADVANCE_UNITS,
  INK,
  MAX_LINE_LEN,
  MAX_LINES,
  maxCharsPerLine,
  placeText,
  textLines,
  TRACE,
  type TextLine,
} from './uebungstext';

// A composed line: one square letter (a ring 0..w × 0..1 in template units)
// followed by a connector, `missing` as given.
const composed = (w: number, missing: string[] = []): ComposedWordOut => ({
  text: 'x',
  items: [
    {
      centerline: [
        [0, 0],
        [w, 1],
      ],
      rings: [
        [
          [0, 0],
          [w, 0],
          [w, 1],
          [0, 1],
        ],
      ],
      mask_width: 0.3,
      lift: false,
    },
    {
      centerline: [
        [w, 0.3],
        [w + 0.5, 0.3],
      ],
      stroke_width: 0.1,
      mask_width: 0.3,
      lift: false,
    },
  ],
  bounds: { min_x: 0, max_x: w + 0.5, min_y: 0, max_y: 1 },
  guides: { baseline: 0, midband: 1, ascender: 2, descender: -1 },
  missing,
});

const rows: RowMetrics[] = Array.from({ length: 6 }, (_, i) => ({
  top: 20 + i * 20,
  waist: 26 + i * 20,
  baseline: 32 + i * 20,
  bottom: 38 + i * 20,
}));
const opts = { xHeightMm: 6, trace: false, practiceRows: 2, left: 15, right: 195 };

// A text-field line, numbered as typed: the tests read easier when the row
// number is implicit, so `line('a', 1)` is spelled only where it matters.
const line = (text: string, composed: TextLine['composed'], no = 1): TextLine => ({ no, text, composed });

// Byte-preserving decode (see lesetafel.test.ts for why not TextDecoder).
async function latin1(blob: Blob): Promise<string> {
  const bytes = new Uint8Array(await blob.arrayBuffer());
  let s = '';
  for (let i = 0; i < bytes.length; i += 8192) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192) as unknown as number[]);
  return s;
}

describe('textLines', () => {
  it('trims, normalises and drops empty lines, capped in count and length', () => {
    expect(textLines('  Guten Morgen \n\n\r\nlesen\n')).toEqual([
      { no: 1, text: 'Guten Morgen' },
      { no: 4, text: 'lesen' },
    ]);
    expect(textLines('über')).toEqual([{ no: 1, text: 'über' }]); // NFC composes the umlaut, like the server
    expect(textLines(Array.from({ length: MAX_LINES + 3 }, (_, i) => `z${i}`).join('\n'))).toHaveLength(MAX_LINES);
    expect(textLines('x'.repeat(MAX_LINE_LEN + 10))[0].text).toHaveLength(MAX_LINE_LEN);
  });
});

describe('maxCharsPerLine', () => {
  it('scales with the Mittellänge instead of promising a flat 60', () => {
    // 210 mm page, 15 mm margins, 3 mm air at each end → 174 mm of writing width.
    expect(maxCharsPerLine(6, 15, 195)).toBe(Math.floor(174 / (6 * AVG_ADVANCE_UNITS)));
    // A smaller Mittellänge holds more characters — the trade the help text
    // now names instead of quoting the textarea's cap.
    expect(maxCharsPerLine(6, 15, 195)).toBeLessThan(maxCharsPerLine(2.5, 15, 195));
    // Never more than the field itself accepts, never negative, never NaN.
    expect(maxCharsPerLine(0.1, 15, 195)).toBe(MAX_LINE_LEN);
    expect(maxCharsPerLine(6, 100, 105)).toBe(0);
    expect(maxCharsPerLine(NaN, 15, 195)).toBe(0);
  });
});

describe('placeText', () => {
  it('sets a line on its row baseline with the Mittelband as x-height, and skips the practice rows', () => {
    const placed = placeText([line('a', composed(1), 1), line('b', composed(1), 2)], rows, opts);
    expect(placed.placed).toEqual(['a', 'b']);
    const [fillA, strokeA, fillB] = placed.shapes;
    if (fillA.kind !== 'fill' || strokeA.kind !== 'stroke' || fillB.kind !== 'fill') throw new Error('shape kinds');
    // Inset from the ruling's end; the ring's top edge (y = 1 unit) one x-height above the baseline.
    expect(fillA.rings[0][0]).toEqual([18, 32]);
    expect(fillA.rings[0][2]).toEqual([24, 26]);
    expect(strokeA.widthMm).toBeCloseTo(0.6);
    expect(strokeA.points[0][0]).toBeCloseTo(24);
    expect(strokeA.points[0][1]).toBeCloseTo(32 - 1.8);
    // The second line leaves two practice rows: row 3.
    expect(fillB.rings[0][0]).toEqual([18, 32 + 3 * 20]);
  });

  it('adds a grey trace copy on the row after the model line, and skips it without room', () => {
    const placed = placeText([line('a', composed(1), 1), line('b', composed(1), 2)], rows, {
      ...opts,
      trace: true,
      practiceRows: 1,
    });
    expect(placed.placed).toEqual(['a', 'b']);
    const [inkA, , traceA, , inkB] = placed.shapes;
    if (inkA.kind !== 'fill' || traceA.kind !== 'fill' || inkB.kind !== 'fill') throw new Error('shape kinds');
    expect(inkA.color).toBe(INK);
    expect(traceA.color).toBe(TRACE);
    expect(traceA.rings[0][0][1]).toBe(rows[1].baseline);
    expect(inkB.rings[0][0][1]).toBe(rows[3].baseline); // model, trace, one practice row
    // A model line on the last row keeps its place; only the copy is dropped.
    const last = placeText([line('z', composed(1))], rows.slice(0, 1), { ...opts, trace: true });
    expect(last.placed).toEqual(['z']);
    expect(last.shapes).toHaveLength(2);
  });

  it('holds the row of a line too wide for the ruling, names it and marks it', () => {
    // The Lineatur is not negotiable (author's decision 2026-09-02): the line
    // is neither scaled nor re-wrapped. It keeps its rows, so the sheet does
    // not re-flow while the writer shortens it, and it is reported by number.
    const placed = placeText(
      [line('weit', composed(40), 1), line('wartet', null, 2), line('ok', composed(1), 3)],
      rows,
      opts,
    );
    expect(placed.tooWide).toEqual([{ no: 1, text: 'weit', chars: 4, fits: 2 }]);
    expect(placed.placed).toEqual([]);
    // Row 0 is held open for the too-wide line and marked over its Mittelband;
    // the pending line takes row 3, so 'ok' lands on row 6 — which this page
    // does not have.
    expect(placed.marks).toEqual([{ no: 1, y: rows[0].waist, height: rows[0].baseline - rows[0].waist, x: 18, width: 174 }]);
    expect(placed.noRow).toEqual([{ no: 3, text: 'ok' }]);
    // A line with nothing writable (every letter missing) keeps its rows too,
    // and its missing letters are named.
    const blank = placeText(
      [line('123', { ...composed(1, ['1', '2', '3']), items: [] }, 1), line('ok', composed(1), 2)],
      rows,
      opts,
    );
    expect(blank.placed).toEqual(['ok']);
    expect(blank.missing).toEqual(['1', '2', '3']);
    const ok = blank.shapes[0];
    if (ok.kind !== 'fill') throw new Error('kind');
    expect(ok.rings[0][0][1]).toBe(rows[3].baseline);
  });

  it('says how many characters of a too-wide line would have fitted', () => {
    // Ten characters over 20 units at a 12 mm Mittellänge — 24 mm each, so the
    // 174 mm of writing width take 7 of them. The figure comes from the line's
    // OWN composition, not from an average, so the sentence under the field
    // holds for this line rather than for a typical one.
    const placed = placeText([line('zehnzeilig', composed(19.5), 2)], rows, { ...opts, xHeightMm: 12 });
    expect(placed.tooWide).toEqual([{ no: 2, text: 'zehnzeilig', chars: 10, fits: 7 }]);
  });

  it('reports the lines without a row left and the union of the missing letters', () => {
    const lines = Array.from({ length: 4 }, (_, i) => line(`l${i}`, composed(1, [`k${i}`]), i + 1));
    const placed = placeText(lines, rows, { ...opts, practiceRows: 1 });
    expect(placed.placed).toEqual(['l0', 'l1', 'l2']);
    expect(placed.noRow).toEqual([{ no: 4, text: 'l3' }]);
    expect(placed.missing).toEqual(['k0', 'k1', 'k2', 'k3']);
  });

  it('puts nothing on a page without rows; a cleared practice count counts as none', () => {
    expect(placeText([line('a', composed(1))], [], opts).noRow).toEqual([{ no: 1, text: 'a' }]);
    // A pending line without a row left is reported too — it can never be placed.
    expect(placeText([line('wartet', null)], [], opts).noRow).toEqual([{ no: 1, text: 'wartet' }]);
    // Nor is a too-wide line given a mark it has no row to sit on.
    const noRows = placeText([line('weit', composed(40))], [], opts);
    expect(noRows.marks).toEqual([]);
    expect(noRows.tooWide).toHaveLength(1);
    const placed = placeText([line('a', composed(1), 1), line('b', composed(1), 2)], rows, {
      ...opts,
      practiceRows: NaN,
    });
    const fillB = placed.shapes[2];
    if (fillB.kind !== 'fill') throw new Error('kind');
    expect(fillB.rings[0][0][1]).toBe(rows[1].baseline);
  });
});

describe('lineaturePdf with an Übungstext', () => {
  it('writes the letter fills even-odd and the connectors as round-joined strokes', async () => {
    const { segments, marks, rows: sheetRows } = buildLineature(PRESETS[1]);
    expect(sheetRows.length).toBeGreaterThan(5);
    const placed = placeText([line('a', composed(1))], sheetRows, opts);
    const pdf = await latin1(lineaturePdf(segments, { marks, shapes: placed.shapes }));
    expect(pdf).toContain(' f* Q');
    expect(pdf).toMatch(/1 J 1 j [\d. ]+ m [\d. ]+ l S Q/);
    expect(pdf).toContain('%%EOF');
  });
});
