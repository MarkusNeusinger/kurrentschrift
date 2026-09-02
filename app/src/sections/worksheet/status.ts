// What the worksheet page SAYS about its own sheet — the sentences under the
// text field, the note over an empty preview, and the footnote a printed sheet
// carries when its Vorschrift is not in the ruling's script.
//
// It lives apart from WorksheetView because it is the half that has to be
// right: a sheet that silently drops a line, or a PDF button that stays
// eager over an empty page, is exactly what the website audit of 2026-09-02
// found here (Befund 3). Pure and testable — no React, no MUI.

import { lettersFromKeys } from '@/domain/glyphs';
import type { LineatureConfig } from '@/lib/lineatur';
import { MAX_LINE_LEN, type InputLine, type PlacedText } from '@/lib/uebungstext';
import { de, fmt } from '@/locales';

import type { WorksheetText } from './useWorksheetText';

/** The script the compositions come from — the only one written out so far
 * (CONFIG.sourceId is its Vorlage). Named here because three sentences on the
 * page have to agree about it. */
export const WRITTEN_SCRIPT = 'suetterlin';

export interface TextStatus {
  text: string;
  /** Something the writer has to act on, not just a note in passing. */
  error: boolean;
}

/** A millimetre figure as German prose: 2,5 — not 2.5. */
export const mmLabel = (v: number): string =>
  (Number.isFinite(v) ? v : 0).toLocaleString('de-DE', { maximumFractionDigits: 2 });

/** "Zeile 3", "Zeile 3 und 4", "Zeile 3, 4 und 7", "Zeile 4 bis 15" — a list a
 * person reads aloud, not a comma-separated dump. Three or more consecutive
 * rows collapse into a range: a full sheet leaves a dozen rows over, and
 * naming each of them turns the sentence into a wall of numbers. */
export function lineList(lines: readonly InputLine[]): string {
  const nos = [...lines].map((l) => l.no).sort((a, b) => a - b);
  const parts: string[] = [];
  for (let i = 0; i < nos.length; ) {
    let end = i;
    while (end + 1 < nos.length && nos[end + 1] === nos[end] + 1) end++;
    if (end - i >= 2) {
      parts.push(`${nos[i]} bis ${nos[end]}`);
      i = end + 1;
    } else {
      parts.push(String(nos[i]));
      i++;
    }
  }
  const joined = parts.length > 1 ? `${parts.slice(0, -1).join(', ')} und ${parts[parts.length - 1]}` : parts[0];
  return fmt(de.worksheet.text.lineNo, { no: joined });
}

/** The line under the text field: what is still being written or failed, which
 * line the sheet cannot hold and why, which letters stay blank. A line that
 * does not fit is named with its number and its length — the writer can act on
 * "Zeile 2 ist mit 37 Zeichen zu breit", not on a sheet that stays empty. */
export function textStatusOf(written: WorksheetText, placed: PlacedText, xHeightMm: number): TextStatus | null {
  const t = de.worksheet.text;
  const mm = mmLabel(xHeightMm);
  const notes: string[] = [];
  if (written.failed.length) notes.push(t.error);
  else if (written.loading) notes.push(t.loading);

  // Every complaint carries the row it is about, so the whole list can be read
  // in the order of the field whatever kind each one is — „Zeile 2 …“ before
  // „Für Zeile 1 …“ reads like a slip. The no-row lines are grouped only AFTER
  // sorting, and only where they are neighbours: rows 1 and 3 with a too-wide
  // row 2 between them stay three separate sentences in row order.
  const perLine: Array<{ no: number; kind: 'wide' | 'noRow' | 'cut'; line: InputLine; text: string }> = [];
  for (const line of placed.tooWide) {
    perLine.push({
      no: line.no,
      kind: 'wide',
      line,
      text:
        line.fits > 0
          ? fmt(t.tooWide, { no: line.no, chars: line.chars, xh: mm, fits: line.fits })
          : fmt(t.tooWideNone, { no: line.no, xh: mm }),
    });
  }
  for (const line of placed.noRow) perLine.push({ no: line.no, kind: 'noRow', line, text: '' });
  // The field's own two caps: a row shortened to MAX_LINE_LEN, and the rows
  // past MAX_LINES that never reached the sheet at all.
  for (const line of [...written.lines, ...written.overflow]) {
    if (line.typed > line.text.length) {
      perLine.push({
        no: line.no,
        kind: 'cut',
        line,
        text: fmt(t.tooLong, { no: line.no, typed: line.typed, max: MAX_LINE_LEN }),
      });
    }
  }
  for (const line of written.overflow) perLine.push({ no: line.no, kind: 'noRow', line, text: '' });
  perLine.sort((a, b) => a.no - b.no || a.kind.localeCompare(b.kind));

  for (let i = 0; i < perLine.length; i++) {
    const entry = perLine[i];
    if (entry.kind !== 'noRow') {
      notes.push(entry.text);
      continue;
    }
    const run = [entry.line];
    while (i + 1 < perLine.length && perLine[i + 1].kind === 'noRow') run.push(perLine[++i].line);
    notes.push(fmt(t.noRow, { lines: lineList(run) }));
  }

  const letters = lettersFromKeys(placed.missing);
  if (letters) notes.push(fmt(t.missing, { letters }));
  if (!notes.length) return null;
  // Pending and missing letters are news; a line the sheet drops or shortens
  // is a defect the writer has to answer, and wears the field's error colour.
  const error = written.failed.length > 0 || perLine.length > 0;
  return { text: notes.join(' · '), error };
}

/** The Vorschrift is set in Sütterlin whatever ruling is chosen — say so where
 * the text is entered, not only behind the „Mehr dazu“ popover. Null while the
 * ruling IS Sütterlin, while no text is entered, or under a hand-made setting
 * that claims no script at all. */
export function scriptMismatchNote(presetId: string, text: string): string | null {
  if (!text.trim() || !presetId || presetId === WRITTEN_SCRIPT) return null;
  const preset = de.worksheet.presets[presetId as keyof typeof de.worksheet.presets];
  if (!preset) return null;
  return fmt(de.worksheet.text.scriptMismatch, { script: preset.label });
}

/** The sheet has no rows: an empty page, either because a field is being
 * edited or because the ratio has outgrown A4. Both get a sentence instead of
 * a blank sheet, and both hold the PDF button — there is nothing to print. */
export function sheetNoteOf(cfg: LineatureConfig, rowCount: number): string | null {
  if (rowCount > 0) return null;
  const numbers = [
    cfg.ratioAscender,
    cfg.ratioXHeight,
    cfg.ratioDescender,
    cfg.xHeightMm,
    cfg.rowGapMm,
    cfg.marginMm,
  ];
  return numbers.every(Number.isFinite) ? de.worksheet.sheet.empty : de.worksheet.sheet.incomplete;
}
