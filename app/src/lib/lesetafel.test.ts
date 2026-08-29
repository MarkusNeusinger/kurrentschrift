import { describe, expect, it } from 'vitest';

import type { GlyphRenderData } from './api';
import { labelFor, layoutWritten, lesetafelPdf, pageCount, rowPitchMm, X_HEIGHT_MM, type LesetafelText } from './lesetafel';
import { A4 } from './lineatur';

const TEXT: LesetafelText = {
  heading: 'Lesetafel',
  writtenLine: 'nachgeschrieben',
  plateLine: 'Originaltafel',
  footer: 'kurrentschrift.ink/tafel',
  longS: 'langes s',
};

// A glyph whose silhouette is one square ring from x=0..w, y=0..1 (template units).
const square = (w: number): GlyphRenderData => ({
  anchors_template: [
    [0, 0],
    [w, 1],
  ],
  half_widths_template: [0.05],
  outline_paths: [
    [
      [
        [0, 0],
        [w, 0],
        [w, 1],
        [0, 1],
      ],
    ],
  ],
  template_guides: { baseline: 0, midband: 1, ascender: 2, descender: -1 },
});

const FAKE_JPEG = new Uint8Array([0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10, 0x4a, 0x46, 0x49, 0x46, 0xff, 0xd9]);

async function latin1(blob: Blob): Promise<string> {
  return new TextDecoder('latin1').decode(await blob.arrayBuffer());
}

describe('lesetafel', () => {
  it('reflows letters proportionally into rows that fit the content width', () => {
    const letters = Array.from({ length: 30 }, (_, i) => ({ glyph: String.fromCharCode(97 + (i % 26)), data: square(1.5) }));
    const rows = layoutWritten(letters, A4.widthMm - 28, 14);
    expect(rows.length).toBeGreaterThan(1);
    for (const row of rows) {
      const last = row[row.length - 1];
      expect(last.x + last.width).toBeLessThanOrEqual(A4.widthMm - 14);
      for (let i = 1; i < row.length; i++) expect(row[i].x).toBeGreaterThan(row[i - 1].x + row[i - 1].width);
    }
    expect(rows.flat()).toHaveLength(30);
    expect(rows[0][0].width).toBeCloseTo(1.5 * X_HEIGHT_MM);
  });

  it('drops a letter without a silhouette instead of placing an empty cell', () => {
    const rows = layoutWritten([{ glyph: 'x', data: { ...square(1), outline_paths: [] } }], 100, 10);
    expect(rows).toEqual([]);
  });

  it('labels the long ſ by name and a ligature by its plain letters (WinAnsi has no ſ)', () => {
    expect(labelFor('ſ', 'langes s')).toBe('langes s');
    expect(labelFor('ſt', 'langes s')).toBe('st');
    expect(labelFor('ß', 'langes s')).toBe('ß');
  });

  it('builds a valid multi-page PDF: filled paths, a JPEG plate, an xref that resolves', async () => {
    const written = {
      kind: 'written' as const,
      name: 'Sütterlin',
      feder: 'Gleichzugfeder',
      title: 'Sütterlin Ausgangsschrift (Leitfaden 1922)',
      attribution: 'Ludwig Sütterlin († 1917), via Wikimedia Commons, Public Domain Mark 1.0',
      ratio: [1, 1, 1],
      letters: [
        { glyph: 'a', data: square(1) },
        { glyph: 'ſ', data: square(0.6) },
      ],
    };
    const plate = {
      kind: 'plate' as const,
      name: 'Kurrent',
      feder: 'Spitzfeder',
      title: 'Loth Kurrent Vorlagen 1866',
      attribution: 'Johann Thomas Loth (zugeschrieben), via Wikimedia Commons, Public Domain Mark 1.0',
      image: { jpeg: FAKE_JPEG, width: 1633, height: 1869 },
    };
    const pdf = await latin1(lesetafelPdf([written, plate], TEXT));

    expect(pdf.startsWith('%PDF-1.4\n')).toBe(true);
    expect(pdf.match(/\/Type \/Page\b/g)).toHaveLength(2); // two page objects …
    expect(pdf).toContain('/Type /Pages /Kids [4 0 R 6 0 R] /Count 2'); // … under one /Pages node
    expect(pdf).toContain(' f*'); // filled silhouettes, even-odd
    expect(pdf).toContain('/Subtype /Image /Width 1633 /Height 1869');
    expect(pdf).toContain('/Filter /DCTDecode');
    expect(pdf).toContain('/Im1 Do');
    expect(pdf).toContain('(langes s) Tj');
    // The em dash and the dagger are WinAnsi bytes (0x97, 0x86), not '?'.
    expect(pdf).toContain('(Lesetafel \x97 S\xfctterlin) Tj');
    expect(pdf).toContain('\\(\x86 1917\\)'); // parentheses escaped inside the literal
    expect(pdf).not.toContain('?');

    // Every xref entry must point at "<n> 0 obj", and startxref at "xref".
    const startxref = Number(pdf.match(/startxref\n(\d+)\n%%EOF/)![1]);
    expect(pdf.slice(startxref, startxref + 4)).toBe('xref');
    const entries = [...pdf.slice(startxref).matchAll(/^(\d{10}) 00000 n /gm)].map((m) => Number(m[1]));
    expect(entries.length).toBeGreaterThan(5);
    entries.forEach((off, i) => expect(pdf.slice(off, off + `${i + 1} 0 obj`.length)).toBe(`${i + 1} 0 obj`));
    // The JPEG bytes survived the Latin-1 round trip byte for byte.
    expect(pdf).toContain(String.fromCharCode(...FAKE_JPEG));
  });

  it('counts pages: a plate is one, a long written sheet overflows', () => {
    const many = Array.from({ length: 400 }, () => ({ glyph: 'a', data: square(1.2) }));
    const sheet = { kind: 'written' as const, name: 'S', feder: 'F', title: 'T', attribution: 'A', ratio: [1, 1, 1], letters: many };
    expect(pageCount(sheet)).toBeGreaterThan(1);
    expect(pageCount({ kind: 'plate', name: 'K', feder: 'F', title: 'T', attribution: 'A', image: { jpeg: FAKE_JPEG, width: 10, height: 10 } })).toBe(1);
    expect(rowPitchMm([2, 1, 2])).toBeGreaterThan(rowPitchMm([1, 1, 1]));
  });
});
