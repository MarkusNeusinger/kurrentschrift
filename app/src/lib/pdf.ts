// Minimal, dependency-free PDF writer for the lineature worksheet.
//
// The worksheet is pure vector content — straight strokes plus one small text
// caption — so a hand-rolled PDF beats pulling in a renderer (and the doc's
// WeasyPrint pipeline, architektur.md §15, is reserved for the heavier
// content-aware worksheet). We emit PDF 1.4 with the built-in Helvetica font
// (WinAnsi, so German umlauts in the caption render without font embedding).
//
// Everything is encoded as Latin-1 (one char → one byte), which keeps xref
// byte offsets equal to string lengths and covers Western-European text.

import { A4, DRAW_ORDER, ROLE_STYLES, type RoleStyle, type LineRole, type Segment, type TextMark } from './lineatur';

const PT_PER_MM = 72 / 25.4;

function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const n = parseInt(hex.replace('#', ''), 16);
  return { r: ((n >> 16) & 0xff) / 255, g: ((n >> 8) & 0xff) / 255, b: (n & 0xff) / 255 };
}

// Escape a PDF literal string and drop anything outside Latin-1 (WinAnsi).
function escapePdfText(s: string): string {
  let out = '';
  for (const ch of s) {
    const code = ch.codePointAt(0) ?? 0;
    if (code > 0xff) {
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

// Helvetica (base-14) advance widths in 1000-unit em — enough to right-align
// footer text without embedding a font. Unknown glyphs fall back to 556 (the
// average lowercase advance), which is plenty accurate for a short caption.
const HELV_WIDTH: Record<string, number> = {
  ' ': 278, '!': 278, '"': 355, '#': 556, $: 556, '%': 889, '&': 667, "'": 191,
  '(': 333, ')': 333, '*': 389, '+': 584, ',': 278, '-': 333, '.': 278, '/': 278,
  ':': 278, ';': 278, '<': 584, '=': 584, '>': 584, '?': 556, '@': 1015, '[': 278,
  '\\': 278, ']': 278, '^': 469, _: 556, '`': 333, '{': 334, '|': 260, '}': 334,
  '~': 584, '°': 400, '·': 278,
  A: 667, B: 667, C: 722, D: 722, E: 667, F: 611, G: 778, H: 722, I: 278, J: 500,
  K: 667, L: 556, M: 833, N: 722, O: 778, P: 667, Q: 778, R: 722, S: 667, T: 611,
  U: 722, V: 667, W: 944, X: 667, Y: 667, Z: 611,
  a: 556, b: 556, c: 500, d: 556, e: 556, f: 278, g: 556, h: 556, i: 222, j: 222,
  k: 500, l: 222, m: 833, n: 556, o: 556, p: 556, q: 556, r: 333, s: 500, t: 278,
  u: 556, v: 500, w: 722, x: 500, y: 500, z: 500,
  ä: 556, ö: 556, ü: 556, ß: 556, Ä: 667, Ö: 778, Ü: 722,
};

function helvWidthMm(text: string, fontPt: number): number {
  let units = 0;
  for (const ch of text) units += /[0-9]/.test(ch) ? 556 : (HELV_WIDTH[ch] ?? 556);
  return ((units / 1000) * fontPt) / PT_PER_MM; // em-units → pt → mm
}

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
  const W = A4.widthMm * PT_PER_MM;
  const H = A4.heightMm * PT_PER_MM;
  // mm (top-left origin, y down) → pt (bottom-left origin, y up)
  const px = (mm: number) => (mm * PT_PER_MM).toFixed(2);
  const py = (mm: number) => ((A4.heightMm - mm) * PT_PER_MM).toFixed(2);
  const w = (mm: number) => (mm * PT_PER_MM).toFixed(2);

  const ops: string[] = ['1 J']; // round line caps
  for (const role of DRAW_ORDER) {
    const segs = segments.filter((s) => s.role === role);
    if (!segs.length) continue;
    const st = styles[role];
    const c = hexToRgb(st.color);
    ops.push(`${c.r.toFixed(3)} ${c.g.toFixed(3)} ${c.b.toFixed(3)} RG`);
    ops.push(`${w(st.widthMm)} w`);
    ops.push(st.dash ? `[${w(st.dash[0])} ${w(st.dash[1])}] 0 d` : `[] 0 d`);
    for (const s of segs) {
      ops.push(`${px(s.x1)} ${py(s.y1)} m ${px(s.x2)} ${py(s.y2)} l S`);
    }
  }

  // Standalone labels (e.g. the pen-angle gauge degree).
  for (const m of opts.marks ?? []) {
    const mc = hexToRgb(m.color ?? '#6B6A63');
    ops.push(`${mc.r.toFixed(3)} ${mc.g.toFixed(3)} ${mc.b.toFixed(3)} rg`);
    ops.push(
      `BT /F1 ${(m.sizeMm * PT_PER_MM).toFixed(2)} Tf ${px(m.x)} ${py(m.y)} Td (${escapePdfText(m.text)}) Tj ET`,
    );
  }

  // Footer in the bottom margin: spec on the left, site URL on the right.
  const footY = A4.heightMm - 9;
  if (opts.footerLeft || opts.footerRight) ops.push('0.42 0.42 0.40 rg');
  if (opts.footerLeft) {
    ops.push(`BT /F1 8 Tf ${px(12)} ${py(footY)} Td (${escapePdfText(opts.footerLeft)}) Tj ET`);
  }
  if (opts.footerRight) {
    const rx = A4.widthMm - 12 - helvWidthMm(opts.footerRight, 8);
    ops.push(`BT /F1 8 Tf ${px(rx)} ${py(footY)} Td (${escapePdfText(opts.footerRight)}) Tj ET`);
  }

  const content = ops.join('\n');

  const objects = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${W.toFixed(2)} ${H.toFixed(2)}] ` +
      `/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>`,
    // /Length counts only the stream data; the EOL marker before `endstream`
    // is excluded per ISO 32000-1 §7.3.8.1 ("an additional EOL marker,
    // preceding endstream, that is not included in the count"), so the trailing
    // "\n" here is correct and content.length is the right length.
    `<< /Length ${content.length} >>\nstream\n${content}\nendstream`,
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>',
  ];

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
