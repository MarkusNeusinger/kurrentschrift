// Shared vocabulary of the Werkbank (/admin/werkbank): what can be marked or
// put under the lens, how an occurrence box lands inside a specimen crop, and
// the colours the spine overlay draws with. Kept out of the component files so
// react-refresh only ever sees components there.

import type { InstanceOut, WordInstanceOut, WorkItemIn } from '@/lib/api';
import { de } from '@/locales/admin';
import { paper, pigment } from '@/styles/paper';

// The three levels the doctrine knows (optimierungs-werkbank.md §5): a letter,
// a join, or the whole word. `word` is the only one without a glyph key.
export type WerkbankTarget =
  | { kind: 'letter'; glyphKey: string }
  | { kind: 'pair'; leftKey: string; rightKey: string }
  | { kind: 'word'; word: string };

// Where the element was SEEN — the words.json namespace, exactly the pair the
// work-item API demands together (an id without its kind may point at nothing).
export interface SpecimenRef {
  id: string;
  kind: 'word' | 'pair';
  word: string;
}

export interface Mark {
  target: WerkbankTarget;
  specimen: SpecimenRef;
}

// A lens selection is a mark whose target has a lens — the word level has none
// (a word complaint is filed, not inspected).
export type Selection = Mark & { target: Exclude<WerkbankTarget, { kind: 'word' }> };

export const pairKeyOf = (leftKey: string, rightKey: string): string => `${leftKey}→${rightKey}`;

// "Buchstabe a" / "Übergang d→a" / "Wort einen" — the level plus its target,
// as the filing dialog shows it back to the admin.
export function targetLabel(target: WerkbankTarget): string {
  const t = de.admin.werkbank;
  if (target.kind === 'letter') return `${t.kindLetter} ${target.glyphKey}`;
  if (target.kind === 'pair') return `${t.kindPair} ${pairKeyOf(target.leftKey, target.rightKey)}`;
  return `${t.kindWord} ${target.word}`;
}

// Identity of one mark — the filing dialog is remounted under this key so its
// pre-sort/note state always starts fresh instead of being reset by an effect.
export const markKey = (mark: Mark): string => `${targetLabel(mark.target)}:${mark.specimen.id}`;

// Stable per-card DOM id, so a lens thumbnail can scroll its word into view.
export const cardElementId = (specimenId: string): string => `werkbank-card-${specimenId}`;

export function scrollToCard(specimenId: string): void {
  document.getElementById(cardElementId(specimenId))?.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Same worst-first ranking as the Belege page: unfitted letters dominate, the
// mean fit RMSE breaks ties.
export function rmseMean(row: WordInstanceOut): number | null {
  const values = Object.values(row.measurements.geo_rmse_px_by_slot ?? {});
  if (values.length === 0) return null;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

export function badness(row: WordInstanceOut): number {
  return (row.measurements.unfitted_slots?.length ?? 0) * 10 + (rmseMean(row) ?? 0);
}

export interface CropBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

// Occurrence boxes are PAGE pixels of the plate, the crop starts at the word
// sample's rect origin — subtracting it puts the box in the crop's own frame
// (the SVG viewBox the spine card draws in). `rect` may be missing when a
// browser/CDN still serves the pre-`rect` word-samples schema (the endpoint's
// stale-while-revalidate spans days) — then there is no valid crop frame and
// the caller skips the interactive layer instead of drawing at page coords.
export function cropBoxOf(inst: InstanceOut, rect: number[] | undefined): CropBox | null {
  if (!rect || rect.length < 2) return null;
  return { x: inst.x0 - rect[0], y: inst.y0 - rect[1], w: inst.x1 - inst.x0, h: inst.y1 - inst.y0 };
}

// The request body for one filed task. specimen_kind + specimen_id always go
// together — the API 422s on a half-given reference.
export function workItemBodyOf(mark: Mark, note: string): WorkItemIn {
  const base = {
    note,
    specimen_kind: mark.specimen.kind,
    specimen_id: mark.specimen.id,
  };
  if (mark.target.kind === 'letter') return { ...base, kind: 'letter', glyph_key: mark.target.glyphKey };
  if (mark.target.kind === 'pair') {
    return { ...base, kind: 'pair', left_key: mark.target.leftKey, right_key: mark.target.rightKey };
  }
  return { ...base, kind: 'word', word: mark.target.word };
}

// Overlay palette — the mockup's paper/ink set mapped onto the repo tokens.
// The trace green matches the Belege page so both surfaces read alike.
export const WERKBANK_COLORS = {
  trace: '#1c6b57',
  box: paper.line, // dashed letter box, recessive
  accent: paper.sepia, // joins + hover
  selected: pigment.vermilion, // the element the lens currently shows
} as const;
