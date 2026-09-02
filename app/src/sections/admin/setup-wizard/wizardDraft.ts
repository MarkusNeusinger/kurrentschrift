// The rescue copy of a drawn Weg.
//
// The Weg is the only state in the Einrichten wizard that is not live-committed
// (Ausschluss, Tinte, Lineatur and Schräglage all PUT as they are made), and
// re-tracing a ductus is an author's step nobody else can repeat — so even a
// deliberate „Verwerfen" keeps the strokes, and the next opening offers them
// back. `sessionStorage` is the right shelf: the tab's own memory, gone when the
// tab is, which matches „you drew this a minute ago" exactly.
//
// Scoped by source AND glyph, so one glyph's draft can never surface on another.

import type { StrokePoint } from '@/lib/api';

export const draftKeyFor = (sourceId: string, glyphKey: string): string =>
  `kurrentschrift.wizard.${sourceId}.${glyphKey}`;

// What comes back out of sessionStorage is untrusted input: it is editable by
// hand and it outlives a deploy that changed the shape. So it is validated all
// the way down to the coordinates rather than cast — the canvas and the geometry
// downstream may never meet a point whose x/y is not a finite number.
const isStrokePoint = (v: unknown): v is StrokePoint => {
  if (typeof v !== 'object' || v === null) return false;
  const p = v as Record<string, unknown>;
  return Number.isFinite(p.x) && Number.isFinite(p.y);
};

export const isStrokeList = (v: unknown): v is StrokePoint[][] =>
  Array.isArray(v) && v.length > 0 && v.every((stroke) => Array.isArray(stroke) && stroke.every(isStrokePoint));

/** The stored draft for this glyph, or null — including for anything malformed. */
export function readDraft(sourceId: string, glyphKey: string): StrokePoint[][] | null {
  try {
    const raw = window.sessionStorage.getItem(draftKeyFor(sourceId, glyphKey));
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    return isStrokeList(parsed) ? parsed : null;
  } catch {
    // Private mode, a quota refusal, unparsable JSON — all the same answer.
    return null;
  }
}

/** Store the draft; an empty stroke list clears it. */
export function writeDraft(sourceId: string, glyphKey: string, strokes: StrokePoint[][]): void {
  try {
    const key = draftKeyFor(sourceId, glyphKey);
    if (strokes.length === 0) window.sessionStorage.removeItem(key);
    else window.sessionStorage.setItem(key, JSON.stringify(strokes));
  } catch {
    // The draft is a net, not a feature: if the browser refuses to hold it, the
    // confirmation dialog still stands between the author and the loss.
  }
}
