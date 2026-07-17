import type { BboxIn, BboxOut } from '@/lib/api';

// Turn a stored bbox (API shape) back into the writable payload, echoing every
// persisted field unchanged, so partial updates can
// spread `{ ...bboxInFromOut(b), ...patch }` without dropping state.
// `n_anchors` is deliberately NOT echoed: the server keeps it in sync with the
// derived canonical (templates.py::_sync_bbox_anchor_count), so resending the
// client's copy on every bbox save would revert that correction. The one place
// that intends to change it (TraceStep) sends it explicitly.
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
    guides: b.guides,
    locked: b.locked,
    fill_holes_max_area: b.fill_holes_max_area,
  };
}
