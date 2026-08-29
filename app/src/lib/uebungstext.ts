// Übungstext — the model lines of a practice sheet (German: Vorschrift): text
// set in the written script on the ruling's own rows, with empty rows beneath
// to copy it into. This is vision.md §2's content-aware worksheet without the
// WeasyPrint backend architektur.md §15 planned: the composition comes from
// the server the way it does for the Federprobe (`GET /write/word`, the same
// draw items WrittenWord animates) and this module only PLACES it — template
// units (x-height = 1, baseline = 0, y up) → page millimetres (y down), one
// composed line per model row, the practice rows skipped, and what the page
// cannot hold reported instead of drawn. Pure and framework-free like
// lib/lineatur.ts; the SVG preview and the PDF writer consume the same shapes,
// so the printout matches the screen.

import type { ComposedWordOut } from './api';
import type { RowMetrics } from './lineatur';
import type { InkShape, Mm } from './pdf';

export const MAX_LINES = 12;
export const MAX_LINE_LEN = 60;
/** The textarea's own cap: every line at full length plus its newline. */
export const MAX_TEXT_CHARS = MAX_LINES * (MAX_LINE_LEN + 1);
export const INK = '#1f1a14';
const INSET_MM = 3; // air between the ruling's end and the first letter
// A connector item without rings carries its width; the fallback only guards
// against a payload that predates the field.
const CONNECTOR_UNITS = 0.1;

/** The non-empty lines of the text field, trimmed and NFC-normalised like the
 * server, capped in count and length. */
export function textLines(text: string): string[] {
  return text
    .split(/\r?\n/)
    .map((line) => line.normalize('NFC').trim().slice(0, MAX_LINE_LEN).trim())
    .filter((line) => line.length > 0)
    .slice(0, MAX_LINES);
}

export interface TextLine {
  text: string;
  /** The server's composition, or null while it is pending or failed. */
  composed: ComposedWordOut | null;
}

export interface PlaceOptions {
  /** One template unit on paper — the ruling's Mittelband, mm. */
  xHeightMm: number;
  /** Empty rows after each model line. */
  practiceRows: number;
  /** The writing width: the ruling's left and right end, mm. */
  left: number;
  right: number;
}

export interface PlacedText {
  shapes: InkShape[];
  /** The lines drawn, in order. */
  placed: string[];
  /** Lines wider than the writing width at this x-height — left out. */
  tooWide: string[];
  /** Lines the page has no row left for — left out. */
  noRow: string[];
  /** glyph_keys the compositions could not place (their letters stay blank). */
  missing: string[];
}

/** Set the lines into the rows: line i takes the next free row and leaves
 * `practiceRows` empty ones after it. A pending line keeps its row, so the
 * sheet does not jump while a line is still being written. */
export function placeText(lines: readonly TextLine[], rows: readonly RowMetrics[], opts: PlaceOptions): PlacedText {
  const out: PlacedText = { shapes: [], placed: [], tooWide: [], noRow: [], missing: [] };
  const s = opts.xHeightMm;
  const x0 = opts.left + INSET_MM;
  const width = opts.right - INSET_MM - x0;
  if (!(s > 0) || !(width > 0)) return out;
  const step = 1 + (Number.isFinite(opts.practiceRows) ? Math.max(0, Math.floor(opts.practiceRows)) : 0);
  const missing = new Set<string>();
  let next = 0;
  for (const line of lines) {
    const c = line.composed;
    if (!c) {
      if (rows[next]) next += step;
      continue;
    }
    for (const key of c.missing) missing.add(key);
    if (!c.items.length) continue; // nothing writable in this line
    if ((c.bounds.max_x - c.bounds.min_x) * s > width) {
      out.tooWide.push(line.text);
      continue;
    }
    const row = rows[next];
    if (!row) {
      out.noRow.push(line.text);
      continue;
    }
    next += step;
    const mm = ([x, y]: readonly [number, number]): Mm => [x0 + (x - c.bounds.min_x) * s, row.baseline - y * s];
    for (const it of c.items) {
      if (it.rings?.length) {
        out.shapes.push({ kind: 'fill', color: INK, rings: it.rings.filter((r) => r.length > 2).map((r) => r.map(mm)) });
      } else if (it.centerline.length > 1) {
        out.shapes.push({
          kind: 'stroke',
          color: INK,
          widthMm: (it.stroke_width ?? CONNECTOR_UNITS) * s,
          points: it.centerline.map(mm),
        });
      }
    }
    out.placed.push(line.text);
  }
  out.missing = [...missing];
  return out;
}
