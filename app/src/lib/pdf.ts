// Minimal, dependency-free PDF writer for the two printable sheets the site
// makes in the browser: the lineature worksheet (`lineaturePdf`, straight
// strokes + a caption) and the Lesetafel (lib/lesetafel.ts — filled letter
// silhouettes, rulings, labels, and the public-domain plates as JPEG images).
// A hand-rolled PDF 1.4 beats pulling in a renderer for that; the doc's
// WeasyPrint pipeline (architektur.md §15) stays reserved for the heavier
// content-aware worksheet (text set in the script on a matching ruling). The
// built-in Helvetica font (WinAnsi) renders German umlauts without embedding.
//
// Everything is encoded as Latin-1 (one char → one byte), which keeps xref
// byte offsets equal to string lengths; JPEG streams ride along as byte-chars.

import { A4, DRAW_ORDER, ROLE_STYLES, type RoleStyle, type LineRole, type Segment, type TextMark } from './lineatur';

export const PT_PER_MM = 72 / 25.4;

export function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const n = parseInt(hex.replace('#', ''), 16);
  return { r: ((n >> 16) & 0xff) / 255, g: ((n >> 8) & 0xff) / 255, b: (n & 0xff) / 255 };
}

const rgbOp = (hex: string, op: 'rg' | 'RG'): string => {
  const c = hexToRgb(hex);
  return `${c.r.toFixed(3)} ${c.g.toFixed(3)} ${c.b.toFixed(3)} ${op}`;
};

// The WinAnsi code points above Latin-1 that the sheets actually use: the
// typographic dashes, quotes and the dagger of an attribution („† 1917"), the
// ellipsis. Everything else outside Latin-1 becomes '?'.
const WIN_ANSI: Record<string, number> = {
  '€': 0x80, // €
  '‚': 0x82, // ‚
  '„': 0x84, // „
  '…': 0x85, // …
  '†': 0x86, // †
  '‘': 0x91, // ‘
  '’': 0x92, // ’
  '“': 0x93, // “
  '”': 0x94, // ”
  '•': 0x95, // •
  '–': 0x96, // –
  '—': 0x97, // —
};

// Escape a PDF literal string; map the WinAnsi specials, drop the rest of
// what lies outside Latin-1.
export function escapePdfText(s: string): string {
  let out = '';
  for (const ch of s) {
    const code = ch.codePointAt(0) ?? 0;
    if (WIN_ANSI[ch] !== undefined) {
      out += String.fromCharCode(WIN_ANSI[ch]);
    } else if (code > 0xff) {
      out += '?';
    } else if (ch === '\\' || ch === '(' || ch === ')') {
      out += '\\' + ch;
    } else {
      out += ch;
    }
  }
  return out;
}

function latin1Bytes(s: string): Uint8Array {
  const out = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i) & 0xff;
  return out;
}

// Binary stream data (a JPEG) as byte-chars, so it can live in the Latin-1
// body string like everything else. Chunked: `fromCharCode` takes arguments,
// and a plate is a few hundred kB.
function bytesToLatin1(bytes: Uint8Array): string {
  let s = '';
  const CHUNK = 8192;
  for (let i = 0; i < bytes.length; i += CHUNK) {
    s += String.fromCharCode.apply(null, Array.from(bytes.subarray(i, i + CHUNK)));
  }
  return s;
}

// Helvetica (base-14) advance widths in 1000-unit em — enough to right-align
// or centre text without embedding a font. Unknown glyphs fall back to 556
// (the average lowercase advance), which is plenty accurate for a short label.
const HELV_WIDTH: Record<string, number> = {
  ' ': 278, '!': 278, '"': 355, '#': 556, $: 556, '%': 889, '&': 667, "'": 191,
  '(': 333, ')': 333, '*': 389, '+': 584, ',': 278, '-': 333, '.': 278, '/': 278,
  ':': 278, ';': 278, '<': 584, '=': 584, '>': 584, '?': 556, '@': 1015, '[': 278,
  '\\': 278, ']': 278, '^': 469, _: 556, '`': 333, '{': 334, '|': 260, '}': 334,
  '~': 584, '°': 400, '·': 278, '—': 1000, '–': 556,
  A: 667, B: 667, C: 722, D: 722, E: 667, F: 611, G: 778, H: 722, I: 278, J: 500,
  K: 667, L: 556, M: 833, N: 722, O: 778, P: 667, Q: 778, R: 722, S: 667, T: 611,
  U: 722, V: 667, W: 944, X: 667, Y: 667, Z: 611,
  a: 556, b: 556, c: 500, d: 556, e: 556, f: 278, g: 556, h: 556, i: 222, j: 222,
  k: 500, l: 222, m: 833, n: 556, o: 556, p: 556, q: 556, r: 333, s: 500, t: 278,
  u: 556, v: 500, w: 722, x: 500, y: 500, z: 500,
  ä: 556, ö: 556, ü: 556, ß: 556, Ä: 667, Ö: 778, Ü: 722,
};

export function helvWidthMm(text: string, fontPt: number): number {
  let units = 0;
  for (const ch of text) units += /[0-9]/.test(ch) ? 556 : (HELV_WIDTH[ch] ?? 556);
  return ((units / 1000) * fontPt) / PT_PER_MM; // em-units → pt → mm
}

/** A point (or ring vertex) in page millimetres, top-left origin, y down. */
export type Mm = [number, number];

// One page's content stream, written in page millimetres (top-left origin,
// y down — the coordinate system every layout here thinks in) and converted to
// PDF points (bottom-left origin, y up) at the last moment.
export class ContentStream {
  private ops: string[] = [];

  private px(mm: number): string {
    return (mm * PT_PER_MM).toFixed(2);
  }

  private py(mm: number): string {
    return ((A4.heightMm - mm) * PT_PER_MM).toFixed(2);
  }

  raw(op: string): this {
    this.ops.push(op);
    return this;
  }

  /** A straight stroke; `dash` in mm (on, off). */
  line(a: Mm, b: Mm, style: { color: string; widthMm: number; dash?: readonly [number, number] | null }): this {
    this.ops.push(
      `q ${rgbOp(style.color, 'RG')} ${this.px(style.widthMm)} w 1 J ` +
        (style.dash ? `[${this.px(style.dash[0])} ${this.px(style.dash[1])}] 0 d ` : '') +
        `${this.px(a[0])} ${this.py(a[1])} m ${this.px(b[0])} ${this.py(b[1])} l S Q`,
    );
    return this;
  }

  /** Filled rings (exterior + holes), even-odd so loop counters stay open. */
  fillRings(rings: readonly (readonly Mm[])[], color: string): this {
    const parts: string[] = [];
    for (const ring of rings) {
      if (ring.length < 3) continue;
      parts.push(ring.map(([x, y], i) => `${this.px(x)} ${this.py(y)} ${i === 0 ? 'm' : 'l'}`).join(' ') + ' h');
    }
    if (parts.length) this.ops.push(`q ${rgbOp(color, 'rg')} ${parts.join(' ')} f* Q`);
    return this;
  }

  /** Helvetica text at a baseline point; `align` shifts the anchor. */
  text(
    at: Mm,
    text: string,
    style: { sizePt: number; color?: string; align?: 'left' | 'center' | 'right' },
  ): this {
    const w = helvWidthMm(text, style.sizePt);
    const x = style.align === 'center' ? at[0] - w / 2 : style.align === 'right' ? at[0] - w : at[0];
    this.ops.push(
      `q ${rgbOp(style.color ?? '#000000', 'rg')} BT /F1 ${style.sizePt.toFixed(2)} Tf ${this.px(x)} ${this.py(at[1])} Td (${escapePdfText(text)}) Tj ET Q`,
    );
    return this;
  }

  /** An image XObject (by the name `PdfDocument.addJpeg` returned) filling the box. */
  image(name: string, topLeft: Mm, widthMm: number, heightMm: number): this {
    this.ops.push(
      `q ${this.px(widthMm)} 0 0 ${this.px(heightMm)} ${this.px(topLeft[0])} ${this.py(topLeft[1] + heightMm)} cm /${name} Do Q`,
    );
    return this;
  }

  toString(): string {
    return this.ops.join('\n');
  }
}

interface JpegImage {
  name: string;
  width: number;
  height: number;
  jpeg: Uint8Array;
}

// A document: A4 pages + the images they reference. Objects are numbered at
// build time — 1 catalog, 2 pages, 3 font, then page + content pairs, then the
// images, which every page's resources reference (simplest, and legal).
export class PdfDocument {
  private pages: string[] = [];
  private images: JpegImage[] = [];

  addPage(content: ContentStream): void {
    this.pages.push(content.toString());
  }

  /** Register a baseline JPEG (DCTDecode); returns the resource name to draw it by. */
  addJpeg(jpeg: Uint8Array, width: number, height: number): string {
    const name = `Im${this.images.length + 1}`;
    this.images.push({ name, width, height, jpeg });
    return name;
  }

  toBlob(): Blob {
    const W = (A4.widthMm * PT_PER_MM).toFixed(2);
    const H = (A4.heightMm * PT_PER_MM).toFixed(2);
    const firstPage = 4;
    const firstImage = firstPage + this.pages.length * 2;
    const xobjects = this.images.map((im, i) => `/${im.name} ${firstImage + i} 0 R`).join(' ');
    const resources = `/Resources << /Font << /F1 3 0 R >>${xobjects ? ` /XObject << ${xobjects} >>` : ''} >>`;
    const kids = this.pages.map((_, i) => `${firstPage + i * 2} 0 R`).join(' ');

    const objects: string[] = [
      '<< /Type /Catalog /Pages 2 0 R >>',
      `<< /Type /Pages /Kids [${kids}] /Count ${this.pages.length} >>`,
      '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>',
    ];
    this.pages.forEach((content, i) => {
      objects.push(
        `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${W} ${H}] ${resources} /Contents ${firstPage + i * 2 + 1} 0 R >>`,
      );
      // /Length counts only the stream data; the EOL marker before `endstream`
      // is excluded per ISO 32000-1 §7.3.8.1, so the trailing "\n" is correct
      // and content.length is the right length.
      objects.push(`<< /Length ${content.length} >>\nstream\n${content}\nendstream`);
    });
    for (const im of this.images) {
      const data = bytesToLatin1(im.jpeg);
      objects.push(
        `<< /Type /XObject /Subtype /Image /Width ${im.width} /Height ${im.height} ` +
          `/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${data.length} >>\nstream\n${data}\nendstream`,
      );
    }

    let body = '%PDF-1.4\n%\xE2\xE3\xCF\xD3\n';
    const offsets: number[] = [];
    objects.forEach((obj, i) => {
      offsets[i] = body.length;
      body += `${i + 1} 0 obj\n${obj}\nendobj\n`;
    });

    const xrefOffset = body.length;
    body += `xref\n0 ${objects.length + 1}\n`;
    body += '0000000000 65535 f \n';
    for (const off of offsets) {
      body += `${String(off).padStart(10, '0')} 00000 n \n`;
    }
    body += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF\n`;

    return new Blob([latin1Bytes(body) as BlobPart], { type: 'application/pdf' });
  }
}

/** The lineature worksheet: one A4 page of ruling segments plus labels. */
export function lineaturePdf(
  segments: Segment[],
  opts: {
    footerLeft?: string;
    footerRight?: string;
    marks?: TextMark[];
    // Ruling colour scheme; preview and PDF must receive the same map so the
    // printout matches the screen (defaults to the standard print look).
    styles?: Record<LineRole, RoleStyle>;
  } = {},
): Blob {
  const styles = opts.styles ?? ROLE_STYLES;
  const page = new ContentStream();
  for (const role of DRAW_ORDER) {
    const st = styles[role];
    for (const s of segments) {
      if (s.role !== role) continue;
      page.line([s.x1, s.y1], [s.x2, s.y2], { color: st.color, widthMm: st.widthMm, dash: st.dash });
    }
  }
  // Standalone labels (e.g. the pen-angle gauge degree).
  for (const m of opts.marks ?? []) {
    page.text([m.x, m.y], m.text, { sizePt: m.sizeMm * PT_PER_MM, color: m.color ?? '#6B6A63' });
  }
  // Footer in the bottom margin: spec on the left, site URL on the right.
  const footY = A4.heightMm - 9;
  if (opts.footerLeft) page.text([12, footY], opts.footerLeft, { sizePt: 8, color: '#6B6B66' });
  if (opts.footerRight) page.text([A4.widthMm - 12, footY], opts.footerRight, { sizePt: 8, color: '#6B6B66', align: 'right' });

  const doc = new PdfDocument();
  doc.addPage(page);
  return doc.toBlob();
}
