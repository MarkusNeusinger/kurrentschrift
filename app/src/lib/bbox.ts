import type { BboxIn, BboxOut } from '@/lib/api';

// Turn a stored bbox (API shape) back into the writable payload, echoing every
// persisted field — including `split` — unchanged, so partial updates can
// spread `{ ...bboxInFromOut(b), ...patch }` without dropping state.
export function bboxInFromOut(b: BboxOut): BboxIn {
  return {
    y0: b.y0,
    y1: b.y1,
    x0: b.x0,
    x1: b.x1,
    mask_strokes: b.mask_strokes,
    ink_strokes: b.ink_strokes,
    patches: b.patches,
    baseline_y: b.baseline_y,
    midband_y: b.midband_y,
    n_anchors: b.n_anchors,
    guides: b.guides,
    locked: b.locked,
    split: b.split,
    fill_holes_max_area: b.fill_holes_max_area,
  };
}
