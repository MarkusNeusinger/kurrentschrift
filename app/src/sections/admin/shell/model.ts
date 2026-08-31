// Shared vocabulary of the admin workbench: what can be marked as an Auftrag or
// put under a lens, how an occurrence box lands inside a specimen crop, and the
// colours the overlays draw with. Kept out of the component files so
// react-refresh only ever sees components there.
//
// This used to live under sections/admin/werkbank — it moved up into the shell
// when the three views (Buchstaben · Übergänge · Wörter) all became places
// where an element is inspected and complained about.

import type { InstanceOut, WordInstanceOut, WordSampleOut, WorkItemIn } from '@/lib/api';
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
  // Absent when the complaint is about a FREELY TYPED combination or word that
  // has no specimen at all: the admin must be able to type any letter pair or
  // word, see how the engine writes it and file that it looks wrong, even where
  // the plates never wrote it. The API takes the reference as optional — it
  // only insists that id and kind travel together.
  specimen?: SpecimenRef;
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
export const markKey = (mark: Mark): string => `${targetLabel(mark.target)}:${mark.specimen?.id ?? '-'}`;

// Stable per-card DOM id, so a lens thumbnail can scroll its word into view.
export const cardElementId = (specimenId: string): string => `werkbank-card-${specimenId}`;

export function scrollToCard(specimenId: string): void {
  document.getElementById(cardElementId(specimenId))?.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Worst-first ranking of a stored word trace: unfitted letters dominate, the
// mean fit RMSE breaks ties.
export function rmseMean(row: WordInstanceOut): number | null {
  const values = Object.values(row.measurements.geo_rmse_px_by_slot ?? {});
  if (values.length === 0) return null;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

export function badness(row: WordInstanceOut): number {
  return (row.measurements.unfitted_slots?.length ?? 0) * 10 + (rmseMean(row) ?? 0);
}

// Where a specimen stands in the manual tracing pass — the one question the
// word overview's status filter answers. Three states, and only three:
//   `authored`   — a hand-drawn trace is stored for it, the work is done;
//   `incomplete` — the sidecar flags the specimen's own ink as clipped, so the
//                  work can never be done (a cut-off i-dot, a last letter
//                  running off the plate). Not a to-do, and not a failure;
//   `open`       — everything else: still to trace.
// `authored` wins over `incomplete` deliberately: where a flagged specimen was
// traced anyway, the stored line is the truth about it, not the flag.
export type TraceStatus = 'authored' | 'open' | 'incomplete';

export function traceStatusOf(sample: WordSampleOut, traced: WordInstanceOut | null | undefined): TraceStatus {
  if (traced?.provenance === 'authored') return 'authored';
  return sample.incomplete ? 'incomplete' : 'open';
}

// The overview's filter over that status — `all` plus the three states.
export type TraceFilter = 'all' | TraceStatus;

export const matchesTraceFilter = (filter: TraceFilter, status: TraceStatus): boolean =>
  filter === 'all' || filter === status;

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

// The crop box of a JOIN occurrence — the union of the two letters it runs
// between. A `pair_instance` stores its geometry in the glyph_pairs frame
// (template units relative to the left glyph's exit) and therefore carries no
// pixel box of its own; but it names the specimen and the LEFT glyph's slot
// (`tools/pairlab/harvest.py::_adjacent_joined` walks adjacent slot pairs), and
// the letter occurrences of the same plate carry exactly those slots as boxes.
// So the join's pixels are found rather than stored.
//
// Both letters must be present AND carry the expected glyph key: a slot index
// that lands on a different letter means the two harvests disagree about the
// word's slotting, and showing the wrong ink is worse than showing none.
export function joinCropBoxOf(
  occ: { left_key: string; right_key: string; slot: number },
  letters: InstanceOut[] | undefined,
  rect: number[] | undefined,
): CropBox | null {
  const at = (slot: number, key: string) =>
    (letters ?? []).find((i) => i.measurements.slot === slot && i.glyph_key === key);
  const left = at(occ.slot, occ.left_key);
  const right = at(occ.slot + 1, occ.right_key);
  if (!left || !right) return null;
  const a = cropBoxOf(left, rect);
  const b = cropBoxOf(right, rect);
  if (!a || !b) return null;
  const x = Math.min(a.x, b.x);
  const y = Math.min(a.y, b.y);
  return { x, y, w: Math.max(a.x + a.w, b.x + b.w) - x, h: Math.max(a.y + a.h, b.y + b.h) - y };
}

// Where a word's units sit in its specimen crop. The stored trace AND the
// engine's composition of the same word live in the identical frame (baseline
// = 0, 1 unit = x-height), so ONE map serves both: px = (u·xh + tx,
// baselineRow − v·xh).
//
// This is the row's own MEASURED registration, and it matters: the overlay used
// to pin the composition to the crop's left edge instead, which put it a median
// 8.9 px (~0.3 xh) left of the ink over the 63 Sütterlin word rows — every
// composition read worse than it is. On the measured registration that median
// drops to 1.1 px; what remains is the real width difference, which is the
// thing worth seeing. The left-edge pin survives only as the fallback for a
// sample with no traced row (`row` null) — there is nothing measured to use.
export interface TraceFrame {
  xh: number;
  tx: number;
  baselineRow: number;
}

export function traceFrameOf(
  row: WordInstanceOut | null | undefined,
  sample: { baseline_y: number; midband_y: number },
): TraceFrame {
  const fallback = { xh: sample.baseline_y - sample.midband_y, tx: 0, baselineRow: sample.baseline_y };
  if (!row) return fallback;
  const reg = row.measurements.registration_px;
  return {
    xh: row.measurements.xh_px ?? fallback.xh,
    tx: reg?.tx ?? fallback.tx,
    baselineRow: (reg?.baseline_row ?? fallback.baselineRow) + (reg?.ty ?? 0),
  };
}

// SVG transform for a TraceFrame — y flipped, since units grow upwards.
export const traceMatrix = (f: TraceFrame): string => `matrix(${f.xh} 0 0 ${-f.xh} ${f.tx} ${f.baselineRow})`;

// The request body for one filed task. specimen_kind + specimen_id always go
// together — the API 422s on a half-given reference — and are simply absent for
// a freely typed target that was never seen on a plate.
export function workItemBodyOf(mark: Mark, note: string): WorkItemIn {
  const base = mark.specimen
    ? { note, specimen_kind: mark.specimen.kind, specimen_id: mark.specimen.id }
    : { note };
  if (mark.target.kind === 'letter') return { ...base, kind: 'letter', glyph_key: mark.target.glyphKey };
  if (mark.target.kind === 'pair') {
    return { ...base, kind: 'pair', left_key: mark.target.leftKey, right_key: mark.target.rightKey };
  }
  return { ...base, kind: 'word', word: mark.target.word };
}

// Overlay palette — the mockup's paper/ink set mapped onto the repo tokens.
// The trace green matches the word cards so every surface reads alike.
export const WERKBANK_COLORS = {
  trace: '#1c6b57', // pen paths on WHITE — the aggregate/pair sketches
  // The same pen path drawn ON TOP of plate ink, where the dark green all but
  // vanished exactly where it matters: over the stroke it is meant to follow.
  // A separate token rather than a brightened `trace`, because the sketches
  // need the dark one to stay readable on their white ground.
  traceOverInk: '#00b37e',
  box: paper.line, // dashed letter box, recessive
  accent: paper.sepia, // joins + hover
  selected: pigment.vermilion, // the element currently focused
  engine: '#e02030', // what the engine itself writes — overlay AND its own face
} as const;
