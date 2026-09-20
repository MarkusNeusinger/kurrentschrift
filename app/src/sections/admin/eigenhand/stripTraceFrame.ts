// Where a word box's Bahn lies, in the pixels the editor actually draws on —
// and the way back into the pixels the column stores.
//
// A Streifen-Pfad's `registration_px` is the STRIP's own frame, because the
// strip is the one image that always exists; the editor works on the word CROP,
// whose frame is that minus the box rectangle (`rect_px`). One subtraction, and
// it has to be exact in both directions: a Bahn drawn, saved, read back and
// re-seeded must land on the same pixels, and an off-by-the-rectangle would
// look like a drawing error rather than an arithmetic one.
//
// Pure and JSX-free, so the round trip is a unit test instead of a screenshot.

import type { EigenhandPfad, EigenhandPfadList, EigenhandPfadRegistration, EigenhandPfadSpan } from '@/lib/api';
import type { TracePoint, TraceRegistration } from '@/sections/admin/belege/registration';
import { bahnenOf } from '@/sections/admin/eigenhand/pfadBahnen';

/** Where the frame under the drawing came from. */
export type FrameHerkunft =
  /** The stored Bahn's own registration — what the follower measured. */
  | 'bahn'
  /** The printed ruling of the Bogen — nominal, and labelled as such. */
  | 'saat';

export type StripTraceSeed = {
  /** The box rectangle in strip pixels, [x0, y0, x1, y1]. */
  rect: readonly number[];
  /** The crop's own pixel size — what the editor's viewBox spans. */
  width: number;
  height: number;
  /** The frame the strokes live in, expressed in CROP pixels. */
  reg: TraceRegistration;
  herkunft: FrameHerkunft;
  /** The stored Bahn as the drawing starts from it — empty where none. */
  strokes: TracePoint[][];
  /** The stored letter boundaries, `null` where the entry has none (a row
   * written under format 1 never has them). */
  spans: readonly EigenhandPfadSpan[] | null;
  /** The stored entry behind all of the above, for provenance. */
  entry: EigenhandPfad | null;
};

/** A stored frame moved into the crop's pixels. */
export const cropRegistration = (
  reg: EigenhandPfadRegistration,
  xhPx: number,
  rect: readonly number[],
): TraceRegistration => ({
  xh: xhPx,
  tx: reg.tx - rect[0],
  baselineRow: reg.baseline_row + reg.ty - rect[1],
});

/**
 * …and back into the strip's own pixels, which is what the column stores.
 *
 * `ty` goes out as 0 and the whole row shift rides in `baseline_row`, exactly
 * as the plate editor stores a re-anchored frame: the two fields are added
 * everywhere they are read, so keeping a second, redundant offset alive would
 * only give a later reader something to get wrong.
 */
export const stripRegistration = (reg: TraceRegistration, rect: readonly number[]): EigenhandPfadRegistration => ({
  tx: reg.tx + rect[0],
  ty: 0,
  baseline_row: reg.baselineRow + rect[1],
});

/**
 * Everything the editor needs to open one word box, or `null` where the box
 * cannot be drawn on at all.
 *
 * `null` means „keine Bogen-Geometrie": a Bogen printed before the cut geometry
 * existed has no rectangle, so there is neither a crop to show nor a frame to
 * store a path in — the same „nie machbar" the Nachfahr-Liste names, and the
 * reason the editor says it rather than opening an empty canvas.
 *
 * Where the box carries a Bahn, its own registration is the frame; where it
 * carries none (or a Skip-Eintrag, which has none by construction) the printed
 * ruling seeds it. The difference is not cosmetic and is shown: one is a
 * measurement, the other is where the writer was ASKED to write.
 */
export function stripTraceSeed(list: EigenhandPfadList, boxIndex: number): StripTraceSeed | null {
  const box = list.boxes.find((candidate) => candidate.index === boxIndex);
  const rect = box?.rect_px;
  if (!box || !rect || rect.length < 4) return null;
  const width = rect[2] - rect[0];
  const height = rect[3] - rect[1];
  if (width <= 0 || height <= 0) return null;
  const entry = (list.pfade ?? []).find((pfad) => pfad.box_index === boxIndex) ?? null;
  const bahn = bahnenOf(entry ? [entry] : [])[0] ?? null;
  if (bahn) {
    return {
      rect,
      width,
      height,
      reg: cropRegistration(bahn.registration_px, bahn.xh_px, rect),
      herkunft: 'bahn',
      strokes: bahn.strokes.map((stroke) => stroke.map(([x, y]) => [x, y] as TracePoint)),
      spans: bahn.letter_spans,
      entry,
    };
  }
  if (box.nominal_baseline_row == null || box.nominal_xh_px == null || box.nominal_xh_px <= 0) return null;
  return {
    rect,
    width,
    height,
    reg: {
      xh: box.nominal_xh_px,
      // The word's origin is the box's left edge: the printed ruling says
      // where the LINE is, and the box says where the word starts.
      tx: 0,
      baselineRow: box.nominal_baseline_row - rect[1],
    },
    herkunft: 'saat',
    strokes: [],
    spans: null,
    entry,
  };
}
