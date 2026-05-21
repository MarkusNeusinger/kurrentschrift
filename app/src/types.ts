// Wire types — hand-synced with `api/schemas.py`. The API is small enough
// that codegen would be more bookkeeping than it saves.

export interface ExcludeRect {
  y0: number;
  y1: number;
  x0: number;
  x1: number;
}

export interface SourceOut {
  id: string;
  title: string;
  license: string;
  chart_path: string;
  chart_size: { w: number; h: number };
  style_ratio: number[];
  slant_deg: number;
  attribution: string | null;
}

export interface BboxOut {
  glyph_key: string;
  y0: number;
  y1: number;
  x0: number;
  x1: number;
  excludes: ExcludeRect[];
  baseline_y: number;
  midband_y: number;
  n_anchors: number;
}

export interface BboxIn {
  y0: number;
  y1: number;
  x0: number;
  x1: number;
  excludes: ExcludeRect[];
  baseline_y: number;
  midband_y: number;
  n_anchors: number;
}

export interface StrokePoint {
  x: number;
  y: number;
  pressure?: number | null;
  t?: number | null;
}

export interface TraceRequest {
  glyph: string;
  position: 'initial' | 'medial' | 'final';
  raw_path: StrokePoint[];
  n_anchors?: number | null;
  variant?: number;
}

export interface CouplingPointOut {
  xy: [number, number];
  tangent_deg: number;
  coupling: 'baseline' | 'midband' | 'ascender' | 'descender';
}

export interface GlyphSummary {
  glyph_key: string;
  glyph: string | null;
  position: string | null;
  variant: number;
  advance: number | null;
  has_data: boolean;
}

export interface GlyphOut {
  glyph_key: string;
  glyph: string;
  position: string;
  variant: number;
  advance: number;
  entry: CouplingPointOut;
  exit_pt: CouplingPointOut;
  anchors: Array<[number, number]>;
  half_widths: number[];
  raw_path: StrokePoint[];
  trace_meta: Record<string, unknown>;
  measurements: Record<string, unknown>;
}

export interface DiagnosticData {
  crop_size: { w: number; h: number };
  skeleton_polyline_px: Array<[number, number]>;
  anchors_px: Array<[number, number]>;
  half_widths_px: number[];
  anchors_template: Array<[number, number]>;
  half_widths_template: number[];
  outline_polygon: Array<[number, number]>;
  baseline_y_crop: number;
  midband_y_crop: number;
  template_guides: { baseline: number; midband: number; ascender: number; descender: number };
  slant_deg: number;
}
