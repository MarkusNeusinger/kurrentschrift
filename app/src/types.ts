// Wire types — parallel to api/core/schemas.py. Kept hand-synced; the API
// is small enough that codegen would be more bookkeeping than it saves.

export interface ExcludeRect {
  y0: number;
  y1: number;
  x0: number;
  x1: number;
}

export interface GlyphBbox {
  y0: number;
  y1: number;
  x0: number;
  x1: number;
  exclude: ExcludeRect[];
  baseline_y?: number | null;
  midband_y?: number | null;
  start_xy?: [number, number] | null;
  n_anchors?: number | null;
}

export interface BboxesResponse {
  _note?: string;
  image_size: [number, number];
  bboxes: Record<string, GlyphBbox | null>;
}

export interface StrokePoint {
  x: number;
  y: number;
  pressure?: number | null;
  t?: number | null;
}

export interface TraceRequest {
  path: StrokePoint[];
  n_anchors?: number | null;
}

export interface Canonical {
  version: string;
  glyph: string;
  position: string;
  variant: number;
  advance: number;
  _note?: string;
  strokes: Array<{
    curve_type: string;
    anchors: Array<[number, number]>;
    half_widths: number[];
  }>;
  entry: { xy: [number, number]; tangent_deg: number; coupling: string };
  exit: { xy: [number, number]; tangent_deg: number; coupling: string };
}
