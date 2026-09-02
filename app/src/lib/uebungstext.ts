// Übungstext — the model lines of a practice sheet (German: Vorschrift): text
// set in the written script on the ruling's own rows, with empty rows beneath
// to copy it into. This is vision.md §2's content-aware worksheet without the
// WeasyPrint backend architektur.md §15 planned: the composition comes from
// the server the way it does for the Federprobe (`GET /write/word`, the same
// draw items WrittenWord animates) and this module only PLACES it — template
// units (x-height = 1, baseline = 0, y up) → page millimetres (y down), one
// composed line per model row, the practice rows skipped, and what the page
// cannot hold reported instead of drawn — reported by its row number in the
// text field, because a note the writer cannot trace back to a line is no
// note at all (website audit 2026-09-02). Pure and framework-free like
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
/** The trace copy: light enough to write over, dark enough for a mono printer. */
export const TRACE = '#B8B6AE';
const INSET_MM = 3; // air between the ruling's end and the first letter
// A connector item without rings carries its width; the fallback only guards
// against a payload that predates the field.
const CONNECTOR_UNITS = 0.1;

// How wide one character runs, in template units (x-height = 1) — the figure
// the character estimate is built on. Measured 2026-09-02 against the live
// composer (`GET /write/word`, suetterlin-1922) on `abcdefghijklmnopqrstuvwxyz`:
// 40.354 units over 26 characters. German prose sits below it (0.6-mm-narrower
// per character: "heute schreibe ich Dir aus Straßburg." 1.250, "das denen
// lesen und der Tag" 1.456, "Guten Morgen" 1.728), so the alphabet's own
// average under-promises slightly rather than over — which is the direction an
// estimate on a practice sheet should err in. Single letters spread far wider
// than any average (i 1.06, m 3.04), so this number answers "roughly how much
// fits", never "this line will fit": the per-line verdict comes from the
// line's OWN composition in placeText.
export const AVG_ADVANCE_UNITS = 1.55;

/** The writing width of a row: between the ruling's ends, less the air at
 * both ends that the first and last letter keep. */
export function writingWidthMm(left: number, right: number): number {
  return right - INSET_MM - (left + INSET_MM);
}

/** Roughly how many characters a line holds at this x-height — the honest
 * replacement for the flat "60" the help text used to promise, which is only
 * the textarea's cap. Rounded down and never above that cap. */
export function maxCharsPerLine(xHeightMm: number, left: number, right: number): number {
  const width = writingWidthMm(left, right);
  if (!(xHeightMm > 0) || !(width > 0)) return 0;
  return Math.max(0, Math.min(MAX_LINE_LEN, Math.floor(width / (xHeightMm * AVG_ADVANCE_UNITS))));
}

/** A line of the text field, with the number it carries there. */
export interface InputLine {
  /** 1-based row in the text field, counted as typed — empty rows included, so
   * the number in a message names the row the writer sees. */
  no: number;
  text: string;
}

/** The non-empty lines of the text field, trimmed and NFC-normalised like the
 * server, capped in count and length, each keeping its own row number. */
export function textLines(text: string): InputLine[] {
  return text
    .split(/\r?\n/)
    .map((line, i) => ({ no: i + 1, text: line.normalize('NFC').trim().slice(0, MAX_LINE_LEN).trim() }))
    .filter((line) => line.text.length > 0)
    .slice(0, MAX_LINES);
}

export interface TextLine extends InputLine {
  /** The server's composition, or null while it is pending or failed. */
  composed: ComposedWordOut | null;
}

export interface PlaceOptions {
  /** One template unit on paper — the ruling's Mittelband, mm. */
  xHeightMm: number;
  /** A grey copy of each model line on the row after it, to trace over. */
  trace: boolean;
  /** Empty rows after each model line (after its trace row, if any). */
  practiceRows: number;
  /** The writing width: the ruling's left and right end, mm. */
  left: number;
  right: number;
}

/** A line the ruling is too narrow for at this x-height. The Lineatur is not
 * negotiable (author's decision 2026-09-02: no scaling, no re-wrapping — the
 * model line's height must keep matching the rows it is written between), so
 * the line stays unwritten and says so, with the count it would need. */
export interface TooWideLine extends InputLine {
  /** The line's length, the figure the writer can act on. */
  chars: number;
  /** How many characters of THIS line fit — from its own composed width, not
   * from an average. 0 when even one character is too wide. */
  fits: number;
}

/** A row left empty on purpose, marked in the preview so nothing vanishes
 * silently. Preview only: a printed practice sheet carries no warnings. */
export interface RowMark {
  no: number;
  /** The x-height band of the reserved row, mm from the page top. */
  y: number;
  height: number;
  x: number;
  width: number;
}

export interface PlacedText {
  shapes: InkShape[];
  /** The lines drawn, in order. */
  placed: string[];
  /** Lines wider than the writing width at this x-height — left unwritten,
   * their row reserved and marked. */
  tooWide: TooWideLine[];
  /** Lines the page has no row left for — left out. */
  noRow: InputLine[];
  /** glyph_keys the compositions could not place (their letters stay blank). */
  missing: string[];
  /** Rows held open for a line that could not be written (preview only). */
  marks: RowMark[];
}

/** Set the lines into the rows: line i takes the next free row, its grey
 * trace copy the row after (when `trace`), and leaves `practiceRows` empty
 * ones after that. A pending line keeps its rows, so the sheet does not jump
 * while a line is still being written — and so does a line too wide for the
 * ruling, which is reported and marked instead of quietly dropped. */
export function placeText(lines: readonly TextLine[], rows: readonly RowMetrics[], opts: PlaceOptions): PlacedText {
  const out: PlacedText = { shapes: [], placed: [], tooWide: [], noRow: [], missing: [], marks: [] };
  const s = opts.xHeightMm;
  const x0 = opts.left + INSET_MM;
  const width = writingWidthMm(opts.left, opts.right);
  if (!(s > 0) || !(width > 0)) return out;
  const practice = Number.isFinite(opts.practiceRows) ? Math.max(0, Math.floor(opts.practiceRows)) : 0;
  const step = 1 + (opts.trace ? 1 : 0) + practice;
  const missing = new Set<string>();
  let next = 0;
  for (const line of lines) {
    const c = line.composed;
    if (c) for (const key of c.missing) missing.add(key);
    if (!c || !c.items.length) {
      // Pending, failed, or nothing writable (every letter still unwritten):
      // the line keeps its rows so the sheet does not jump, and the
      // missing-letter note names what stays blank. Without a row left it
      // is reported like any other line — it can never be placed.
      if (rows[next]) next += step;
      else out.noRow.push({ no: line.no, text: line.text });
      continue;
    }
    const lineWidth = (c.bounds.max_x - c.bounds.min_x) * s;
    if (lineWidth > width) {
      // Too wide for the ruling. The line is not scaled and not re-wrapped —
      // it would no longer sit in its rows — but it does not disappear
      // either: it keeps its row, the row is marked in the preview, and the
      // report says how many of its characters would have fitted.
      const perChar = lineWidth / line.text.length;
      out.tooWide.push({
        no: line.no,
        text: line.text,
        chars: line.text.length,
        fits: perChar > 0 ? Math.floor(width / perChar) : 0,
      });
      const held = rows[next];
      if (held) {
        out.marks.push({
          no: line.no,
          y: held.waist,
          height: held.baseline - held.waist,
          x: x0,
          width,
        });
        next += step;
      }
      continue;
    }
    const row = rows[next];
    if (!row) {
      out.noRow.push({ no: line.no, text: line.text });
      continue;
    }
    // The trace row is skipped silently at the page's end — the model line
    // still stands, only its grey copy has no room.
    const traceRow = opts.trace ? rows[next + 1] : undefined;
    next += step;
    const emit = (baseline: number, color: string) => {
      const mm = ([x, y]: readonly [number, number]): Mm => [x0 + (x - c.bounds.min_x) * s, baseline - y * s];
      for (const it of c.items) {
        if (it.rings?.length) {
          out.shapes.push({ kind: 'fill', color, rings: it.rings.filter((r) => r.length > 2).map((r) => r.map(mm)) });
        } else if (it.centerline.length > 1) {
          out.shapes.push({
            kind: 'stroke',
            color,
            widthMm: (it.stroke_width ?? CONNECTOR_UNITS) * s,
            points: it.centerline.map(mm),
          });
        }
      }
    };
    emit(row.baseline, INK);
    if (traceRow) emit(traceRow.baseline, TRACE);
    out.placed.push(line.text);
  }
  out.missing = [...missing];
  return out;
}
