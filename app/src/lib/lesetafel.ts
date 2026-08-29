// Lesetafel — the printable letter chart of the Schreibtafel (/tafel): all
// three Vorlagen on A4, to lay beside an old letter while deciphering (the
// Schriftkunde's advice „Lege eine Buchstabentafel neben den Brief" — until
// now the screen was the only tafel). One page per script:
//   · a WRITTEN script (the Sütterlin today) — its locked letters as filled
//     silhouettes from the render payloads (`outline_paths`, the same rings
//     WrittenGlyph/WrittenSheet draw), reflowed into rows on a faint ruling,
//     each labelled with its Antiqua letter;
//   · an ORIGINAL-only script (Kurrent, Offenbacher) — its public-domain plate
//     as one image, fitted to the page, with the source's attribution.
// Pure composition: payloads and plate JPEGs come in, a Blob goes out — the
// browser glue (sections/tafel/useLesetafelPdf.ts) fetches and rasterises.

import type { GlyphRenderData } from './api';
import { A4 } from './lineatur';
import { ContentStream, PdfDocument, helvWidthMm, type Mm } from './pdf';

type Pt = [number, number];
type Ring = Pt[];

export interface WrittenLetter {
  /** The display character(s) — `MarkedSlot.glyph` (ſ, ß, ch …). */
  glyph: string;
  data: GlyphRenderData;
}

export interface PlateImage {
  jpeg: Uint8Array;
  width: number;
  height: number;
}

interface SheetBase {
  /** Script name (Kurrent · Sütterlin · Offenbacher). */
  name: string;
  /** Writing instrument line (Spitzfeder …). */
  feder: string;
  /** Source title + attribution for the page caption. */
  title: string;
  attribution: string;
}

export type LesetafelSheet =
  | (SheetBase & { kind: 'written'; ratio: number[]; letters: WrittenLetter[] })
  | (SheetBase & { kind: 'plate'; image: PlateImage });

/** The fixed strings of the sheet — from the locale (de.tafel.pdf). */
export interface LesetafelText {
  heading: string;
  writtenLine: string;
  plateLine: string;
  footer: string;
  /** Label for the long ſ, which Helvetica/WinAnsi cannot set. */
  longS: string;
}

// --- geometry ---------------------------------------------------------------

export const X_HEIGHT_MM = 7; // one template unit (baseline → midband) on paper
export const MARGIN_MM = 14;
export const HEADER_MM = 22; // page title + subline
export const FOOTER_MM = 12;
const GAP = 0.7; // between the ink of neighbouring letters, template units (WrittenSheet's)
const LEAD = 0.3; // row edge padding, template units
const PAD_Y = 0.14; // air above the ascender / below the descender, template units
const LABEL_PT = 9;
const LABEL_MM = 5.5; // label band under a row
const ROW_GAP_MM = 3;
const INK = '#1f1a14';
const RULE_BASE = '#8a949c';
const RULE_FAINT = '#c3ccd3';
const CAPTION = '#6b6a63';

// Template-space Lineatur levels from a style ratio — WrittenSheet's rule:
// x-height (baseline → midband) is the unit, Oberlänge/Unterlänge relative.
export function guidesFromRatio(ratio: number[]): GlyphRenderData['template_guides'] {
  const [ober = 1, mittel = 1, unter = 1] = ratio;
  const m = mittel || 1;
  return { baseline: 0, midband: 1, ascender: 1 + ober / m, descender: -(unter / m) };
}

// Per-stroke silhouette rings: the capsule-union rings, else the legacy
// ribbon polygons; a payload without a silhouette yields nothing.
export function glyphRings(data: GlyphRenderData): Ring[][] {
  if (data.outline_paths?.length) return data.outline_paths as Ring[][];
  if (data.outline_polygons?.length) return data.outline_polygons.filter((p) => p.length > 2).map((p) => [p as Ring]);
  if (data.outline_polygon && data.outline_polygon.length > 2) return [[data.outline_polygon as Ring]];
  return [];
}

function inkExtent(strokes: Ring[][]): { minX: number; maxX: number } | null {
  let minX = Infinity;
  let maxX = -Infinity;
  for (const stroke of strokes) {
    for (const ring of stroke) {
      for (const [x] of ring) {
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
      }
    }
  }
  return Number.isFinite(minX) ? { minX, maxX } : null;
}

export interface PlacedLetter {
  glyph: string;
  strokes: Ring[][];
  /** Left ink edge on the page, mm. */
  x: number;
  /** Ink width, mm. */
  width: number;
  minX: number; // template units, subtracted when placing
}

/** Reflow the letters into rows that fit `contentW` mm, proportional widths
 * with a constant gap (WrittenSheet's layout rule), in the given order.
 * Letters without a silhouette are dropped. */
export function layoutWritten(letters: readonly WrittenLetter[], contentW: number, x0: number): PlacedLetter[][] {
  const gap = GAP * X_HEIGHT_MM;
  const lead = LEAD * X_HEIGHT_MM;
  const rows: PlacedLetter[][] = [];
  let row: PlacedLetter[] = [];
  let cursor = x0 + lead;
  for (const letter of letters) {
    const strokes = glyphRings(letter.data);
    const ext = inkExtent(strokes);
    if (!ext) continue;
    const width = (ext.maxX - ext.minX) * X_HEIGHT_MM;
    if (row.length && cursor + width > x0 + contentW - lead) {
      rows.push(row);
      row = [];
      cursor = x0 + lead;
    }
    row.push({ glyph: letter.glyph, strokes, x: cursor, width, minX: ext.minX });
    cursor += width + gap;
  }
  if (row.length) rows.push(row);
  return rows;
}

/** The Antiqua label under a written letter. Helvetica (WinAnsi) has no long
 * ſ, so the lone ſ gets its name and a ligature shows its plain letters. */
export function labelFor(glyph: string, longS: string): string {
  if (glyph === 'ſ') return longS;
  return glyph.replace(/ſ/g, 's');
}

// --- pages ------------------------------------------------------------------

function pageHeader(page: ContentStream, text: LesetafelText, sheet: LesetafelSheet): void {
  page.text([MARGIN_MM, MARGIN_MM + 6], `${text.heading} — ${sheet.name}`, { sizePt: 15, color: INK });
  const sub = `${sheet.feder} · ${sheet.kind === 'written' ? text.writtenLine : text.plateLine}`;
  page.text([MARGIN_MM, MARGIN_MM + 12.5], sub, { sizePt: 9, color: CAPTION });
}

function pageFooter(page: ContentStream, text: LesetafelText, sheet: LesetafelSheet, index: number, count: number): void {
  const y = A4.heightMm - 8;
  const contentW = A4.widthMm - 2 * MARGIN_MM;
  const right = `${text.footer} · ${index + 1}/${count}`;
  const rightW = helvWidthMm(right, 8);
  let left = `${sheet.title} — ${sheet.attribution}`;
  // One line: cut the attribution rather than run under the page number.
  while (left.length > 8 && helvWidthMm(left, 8) > contentW - rightW - 4) left = `${left.slice(0, -2).trimEnd()}…`;
  page.text([MARGIN_MM, y], left, { sizePt: 8, color: CAPTION });
  page.text([A4.widthMm - MARGIN_MM, y], right, { sizePt: 8, color: CAPTION, align: 'right' });
}

/** Row pitch of a written sheet in mm, for the given ratio. */
export function rowPitchMm(ratio: number[]): number {
  const g = guidesFromRatio(ratio);
  return (g.ascender - g.descender + 2 * PAD_Y) * X_HEIGHT_MM + LABEL_MM + ROW_GAP_MM;
}

function writtenPages(doc: PdfDocument, text: LesetafelText, sheet: Extract<LesetafelSheet, { kind: 'written' }>, count: { n: number; i: number }): void {
  const g = guidesFromRatio(sheet.ratio);
  const contentW = A4.widthMm - 2 * MARGIN_MM;
  const rows = layoutWritten(sheet.letters, contentW, MARGIN_MM);
  const pitch = rowPitchMm(sheet.ratio);
  const top = MARGIN_MM + HEADER_MM;
  const bottom = A4.heightMm - FOOTER_MM - MARGIN_MM;
  const perPage = Math.max(1, Math.floor((bottom - top) / pitch));

  for (let start = 0; start < rows.length || start === 0; start += perPage) {
    const page = new ContentStream();
    pageHeader(page, text, sheet);
    rows.slice(start, start + perPage).forEach((row, r) => {
      // The row's ruling: baseline strongest, midband lighter, the outer
      // lines faint — reading context, like the screen's InkGuides.
      const rowTop = top + r * pitch;
      const baselineY = rowTop + (g.ascender + PAD_Y) * X_HEIGHT_MM;
      const yOf = (level: number) => baselineY - level * X_HEIGHT_MM;
      const x1 = MARGIN_MM;
      const x2 = MARGIN_MM + contentW;
      page.line([x1, yOf(g.ascender)], [x2, yOf(g.ascender)], { color: RULE_FAINT, widthMm: 0.15 });
      page.line([x1, yOf(g.descender)], [x2, yOf(g.descender)], { color: RULE_FAINT, widthMm: 0.15 });
      page.line([x1, yOf(g.midband)], [x2, yOf(g.midband)], { color: RULE_FAINT, widthMm: 0.2 });
      page.line([x1, baselineY], [x2, baselineY], { color: RULE_BASE, widthMm: 0.25 });
      for (const letter of row) {
        const rings: Mm[][] = [];
        for (const stroke of letter.strokes) {
          for (const ring of stroke) {
            rings.push(ring.map(([x, y]): Mm => [letter.x + (x - letter.minX) * X_HEIGHT_MM, baselineY - y * X_HEIGHT_MM]));
          }
        }
        page.fillRings(rings, INK);
        page.text([letter.x + letter.width / 2, yOf(g.descender) + LABEL_MM], labelFor(letter.glyph, text.longS), {
          sizePt: LABEL_PT,
          color: CAPTION,
          align: 'center',
        });
      }
    });
    pageFooter(page, text, sheet, count.i, count.n);
    doc.addPage(page);
    count.i += 1;
    if (!rows.length) break;
  }
}

function platePage(doc: PdfDocument, text: LesetafelText, sheet: Extract<LesetafelSheet, { kind: 'plate' }>, count: { n: number; i: number }): void {
  const page = new ContentStream();
  pageHeader(page, text, sheet);
  const name = doc.addJpeg(sheet.image.jpeg, sheet.image.width, sheet.image.height);
  const boxW = A4.widthMm - 2 * MARGIN_MM;
  const boxTop = MARGIN_MM + HEADER_MM;
  const boxH = A4.heightMm - FOOTER_MM - MARGIN_MM - boxTop;
  const scale = Math.min(boxW / sheet.image.width, boxH / sheet.image.height);
  const w = sheet.image.width * scale;
  const h = sheet.image.height * scale;
  page.image(name, [MARGIN_MM + (boxW - w) / 2, boxTop], w, h);
  pageFooter(page, text, sheet, count.i, count.n);
  doc.addPage(page);
  count.i += 1;
}

/** Count the pages a sheet will take (a written sheet may overflow one page). */
export function pageCount(sheet: LesetafelSheet): number {
  if (sheet.kind === 'plate') return 1;
  const rows = layoutWritten(sheet.letters, A4.widthMm - 2 * MARGIN_MM, MARGIN_MM);
  const perPage = Math.max(1, Math.floor((A4.heightMm - FOOTER_MM - MARGIN_MM - MARGIN_MM - HEADER_MM) / rowPitchMm(sheet.ratio)));
  return Math.max(1, Math.ceil(rows.length / perPage));
}

/** Compose the Lesetafel: one (or more) page per sheet, in the given order. */
export function lesetafelPdf(sheets: readonly LesetafelSheet[], text: LesetafelText): Blob {
  const doc = new PdfDocument();
  const count = { n: sheets.reduce((n, s) => n + pageCount(s), 0), i: 0 };
  for (const sheet of sheets) {
    if (sheet.kind === 'written') writtenPages(doc, text, sheet, count);
    else platePage(doc, text, sheet, count);
  }
  return doc.toBlob();
}
