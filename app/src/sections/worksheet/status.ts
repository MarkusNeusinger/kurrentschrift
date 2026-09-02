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
import type { InputLine, PlacedText } from '@/lib/uebungstext';
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

/** "Zeile 3", "Zeile 3 und 4", "Zeile 3, 4 und 5" — a list a person reads
 * aloud, not a comma-separated dump. */
export function lineList(lines: readonly InputLine[]): string {
  const nos = lines.map((l) => String(l.no));
  const head = nos.slice(0, -1).join(', ');
  const joined = nos.length > 1 ? `${head} und ${nos[nos.length - 1]}` : nos[0];
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
  // The per-line complaints are read in the order of the field, whichever
  // kind they are — „Zeile 2 …“ before „Für Zeile 1 …“ reads like a slip.
  const perLine: Array<{ no: number; text: string }> = placed.tooWide.map((line) => ({
    no: line.no,
    text:
      line.fits > 0
        ? fmt(t.tooWide, { no: line.no, chars: line.chars, xh: mm, fits: line.fits })
        : fmt(t.tooWideNone, { no: line.no, xh: mm }),
  }));
  if (placed.noRow.length) {
    perLine.push({
      no: Math.min(...placed.noRow.map((l) => l.no)),
      text: fmt(t.noRow, { lines: lineList(placed.noRow) }),
    });
  }
  perLine.sort((a, b) => a.no - b.no);
  notes.push(...perLine.map((n) => n.text));
  const letters = lettersFromKeys(placed.missing);
  if (letters) notes.push(fmt(t.missing, { letters }));
  if (!notes.length) return null;
  // Pending and missing letters are news; a dropped line is a defect the
  // writer has to answer, and wears the field's error colour for it.
  const error = written.failed.length > 0 || placed.tooWide.length > 0 || placed.noRow.length > 0;
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
