// Interaction-tuning constants for the chart editor — feature-local UI values
// (hit sizes, zoom presets, new-bbox seeds), not theme tokens.

export type Mode = 'pan' | 'bbox' | 'edit';

export const MIN_BOX = 6;
// Resize grips are only the eight little squares (corners + edge midpoints).
// GRIP_HIT is their hit half-size in screen px (the caller divides by zoom),
// kept a touch larger than the drawn handle so it stays easy to grab on touch.
export const GRIP_HIT = 12;

export const ZOOM_PRESETS = [0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4];
export const ZOOM_MIN = ZOOM_PRESETS[0];
export const ZOOM_MAX = ZOOM_PRESETS[ZOOM_PRESETS.length - 1];

// New (rough) bbox: seed midband/baseline at sensible defaults — the wizard
// refines them. Midband at top third, baseline at ~70% so the calibration
// handles are visible immediately.
export const NEW_BBOX_MIDBAND_RATIO = 0.35;
export const NEW_BBOX_BASELINE_RATIO = 0.7;
// Default anchor count for a fresh bbox (templates.n_anchors). Mirrors
// core/pipeline.py DEFAULT_N_ANCHORS — bench-calibrated; the sweep data and
// why more/fewer anchors lose live in that constant's comment.
export const NEW_BBOX_N_ANCHORS = 120;
