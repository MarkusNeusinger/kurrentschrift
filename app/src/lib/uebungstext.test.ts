import { describe, expect, it } from 'vitest';

import type { ComposedWordOut } from './api';
import { buildLineature, PRESETS, type RowMetrics } from './lineatur';
import { lineaturePdf } from './pdf';
import { INK, MAX_LINE_LEN, MAX_LINES, placeText, textLines, TRACE } from './uebungstext';

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

// Byte-preserving decode (see lesetafel.test.ts for why not TextDecoder).
async function latin1(blob: Blob): Promise<string> {
  const bytes = new Uint8Array(await blob.arrayBuffer());
  let s = '';
  for (let i = 0; i < bytes.length; i += 8192) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192) as unknown as number[]);
  return s;
}

describe('textLines', () => {
  it('trims, normalises and drops empty lines, capped in count and length', () => {
    expect(textLines('  Guten Morgen \n\n\r\nlesen\n')).toEqual(['Guten Morgen', 'lesen']);
    expect(textLines('über')).toEqual(['über']); // NFC composes the umlaut, like the server
    expect(textLines(Array.from({ length: MAX_LINES + 3 }, (_, i) => `z${i}`).join('\n'))).toHaveLength(MAX_LINES);
    expect(textLines('x'.repeat(MAX_LINE_LEN + 10))[0]).toHaveLength(MAX_LINE_LEN);
  });
});

describe('placeText', () => {
  it('sets a line on its row baseline with the Mittelband as x-height, and skips the practice rows', () => {
    const placed = placeText(
      [
        { text: 'a', composed: composed(1) },
        { text: 'b', composed: composed(1) },
      ],
      rows,
      opts,
    );
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
    const placed = placeText(
      [
        { text: 'a', composed: composed(1) },
        { text: 'b', composed: composed(1) },
      ],
      rows,
      { ...opts, trace: true, practiceRows: 1 },
    );
    expect(placed.placed).toEqual(['a', 'b']);
    const [inkA, , traceA, , inkB] = placed.shapes;
    if (inkA.kind !== 'fill' || traceA.kind !== 'fill' || inkB.kind !== 'fill') throw new Error('shape kinds');
    expect(inkA.color).toBe(INK);
    expect(traceA.color).toBe(TRACE);
    expect(traceA.rings[0][0][1]).toBe(rows[1].baseline);
    expect(inkB.rings[0][0][1]).toBe(rows[3].baseline); // model, trace, one practice row
    // A model line on the last row keeps its place; only the copy is dropped.
    const last = placeText([{ text: 'z', composed: composed(1) }], rows.slice(0, 1), { ...opts, trace: true });
    expect(last.placed).toEqual(['z']);
    expect(last.shapes).toHaveLength(2);
  });

  it('leaves out a line wider than the ruling and reports it; a pending line keeps its row', () => {
    const placed = placeText(
      [
        { text: 'weit', composed: composed(40) },
        { text: 'wartet', composed: null },
        { text: 'ok', composed: composed(1) },
      ],
      rows,
      opts,
    );
    expect(placed.tooWide).toEqual(['weit']);
    expect(placed.placed).toEqual(['ok']);
    const fill = placed.shapes[0];
    if (fill.kind !== 'fill') throw new Error('kind');
    expect(fill.rings[0][0][1]).toBe(rows[3].baseline); // row 0 stays with the pending line
  });

  it('reports the lines without a row left and the union of the missing letters', () => {
    const lines = Array.from({ length: 4 }, (_, i) => ({ text: `l${i}`, composed: composed(1, [`k${i}`]) }));
    const placed = placeText(lines, rows, { ...opts, practiceRows: 1 });
    expect(placed.placed).toEqual(['l0', 'l1', 'l2']);
    expect(placed.noRow).toEqual(['l3']);
    expect(placed.missing).toEqual(['k0', 'k1', 'k2', 'k3']);
  });

  it('puts nothing on a page without rows; a cleared practice count counts as none', () => {
    expect(placeText([{ text: 'a', composed: composed(1) }], [], opts).noRow).toEqual(['a']);
    const placed = placeText(
      [
        { text: 'a', composed: composed(1) },
        { text: 'b', composed: composed(1) },
      ],
      rows,
      { ...opts, practiceRows: NaN },
    );
    const fillB = placed.shapes[2];
    if (fillB.kind !== 'fill') throw new Error('kind');
    expect(fillB.rings[0][0][1]).toBe(rows[1].baseline);
  });
});

describe('lineaturePdf with an Übungstext', () => {
  it('writes the letter fills even-odd and the connectors as round-joined strokes', async () => {
    const { segments, marks, rows: sheetRows } = buildLineature(PRESETS[1]);
    expect(sheetRows.length).toBeGreaterThan(5);
    const placed = placeText([{ text: 'a', composed: composed(1) }], sheetRows, opts);
    const pdf = await latin1(lineaturePdf(segments, { marks, shapes: placed.shapes }));
    expect(pdf).toContain(' f* Q');
    expect(pdf).toMatch(/1 J 1 j [\d. ]+ m [\d. ]+ l S Q/);
    expect(pdf).toContain('%%EOF');
  });
});
