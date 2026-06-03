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

// Practice-sheet-style guide lines (Hilfslinien) drawn over a glyph crop —
// same vocabulary as the worksheet rulers in lib/lineatur.ts. baseline + waist
// come from the bbox calibration; ascender/descender are toggleable; slant is
// the positionable, angled main line (degrees from vertical, worksheet
// convention). slant_count/slant_spacing allow the few letters that need
// several parallel main lines. Mirrors GuideConfig in api/schemas.py.
export interface GuideConfig {
  slant_deg?: number | null;
  slant_x?: number | null;
  slant_count?: number;
  slant_spacing?: number;
  show_ascender?: boolean;
  show_descender?: boolean;
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
  guides: GuideConfig;
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
  guides?: GuideConfig;
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

export interface FitMeta {
  success: boolean;
  message: string;
  iterations: number;
  geo_rmse_px: number;
  geo_rmse_px_initial: number;
  width_rmse_px: number;
  reg_energy: number;
  max_anchor_delta: number;
  lambda_reg: number;
  width_weight: number;
  n_samples: number;
}

export interface FitData {
  glyph: string;
  position: string;
  advance: number;
  anchors: Array<[number, number]>;
  half_widths: number[];
  entry: CouplingPointOut;
  exit_pt: CouplingPointOut;
  fit: FitMeta;
  half_widths_px: number[];
  crop_size: { w: number; h: number };
  skeleton_polyline_px: Array<[number, number]>;
  fitted_polyline_px: Array<[number, number]>;
  canonical_polyline_px: Array<[number, number]>;
  placement: { x_origin_px: number; baseline_y_px: number; unit_px: number };
}
