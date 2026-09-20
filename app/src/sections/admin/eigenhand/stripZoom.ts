// The magnification of the strip surface, shared by every tile, the Lupe and
// the eraser: one scale for the whole panel, so a strip, a word cut and an
// overlay drawn over either are always read at the same size.

// CSS pixels per stored pixel. ¼ is what the old fixed tile height came to on
// a 300-dpi strip; 1:1 shows the scan as captured.
export const ZOOMS = [0.25, 0.5, 1, 2] as const;
export type Zoom = (typeof ZOOMS)[number];
export const ZOOM_LABELS: Record<Zoom, string> = { 0.25: '¼', 0.5: '½', 1: '1:1', 2: '2×' };
export const LUPE_ZOOMS = { min: 0.5, max: 4, step: 0.25 };
