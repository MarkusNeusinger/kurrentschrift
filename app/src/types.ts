// Wire types — hand-synced with `api/schemas.py`. The API is small enough
// that codegen would be more bookkeeping than it saves.

// One freeform eraser stroke (German: Radierer): a brush polyline + radius, in
// chart-pixel coords. Replaces the old rectangle excludes. Mirrors MaskStroke
// in api/schemas.py.
export interface MaskStroke {
  points: Array<[number, number]>;
  radius: number;
}

export interface StyleOut {
  id: string;
  name: string;
  width_resolver: string;
  default_slant_deg: number;
  default_style_ratio: number[];
  description: string | null;
  // Whether a teaching-chart source exists for this style yet (only then can
  // templates be authored against it).
  authorable: boolean;
}

export interface SourceOut {
  id: string;
  style_id: string;
  hand_id: string | null;
  kind: string;
  title: string;
  license: string;
  chart_path: string;
  chart_size: { w: number; h: number };
  // Resolved: per-source override if set, else the style default.
  style_ratio: number[];
  slant_deg: number;
  attribution: string | null;
  origin_url?: string | null;
  note?: string | null;
}

// Practice-sheet-style guide lines (Hilfslinien) drawn over a glyph crop —
// same vocabulary as the worksheet rulers in lib/lineatur.ts. baseline + waist
// come from the bbox calibration; ascender/descender are toggleable; slant is
// one or more positionable, angled main lines. slant_deg is measured from the
// horizontal baseline (≈65° = typical Kurrent; 90° = upright), matching
// source.slant_deg. slant_xs lists the baseline crossing of each slant line
// (all share slant_deg) — individually draggable for letters like m/n/u;
// slant_x is the single-line fallback. Mirrors GuideConfig in api/schemas.py.
export type CouplingHeight = 'baseline' | 'midband' | 'ascender' | 'descender';

export interface GuideConfig {
  slant_deg?: number | null;
  slant_x?: number | null;
  slant_xs?: number[] | null;
  show_ascender?: boolean;
  show_descender?: boolean;
  // Coupling height of the stroke's entry/exit — the guide line a neighbouring
  // letter joins at. Persisted per glyph; the trace/resample pipeline stamps it
  // onto entry.coupling / exit_pt.coupling.
  entry_coupling?: CouplingHeight;
  exit_coupling?: CouplingHeight;
}

export interface BboxOut {
  glyph_key: string;
  y0: number;
  y1: number;
  x0: number;
  x1: number;
  mask_strokes: MaskStroke[];
  baseline_y: number;
  midband_y: number;
  n_anchors: number;
  guides: GuideConfig;
  // Manual "done" marker: the glyph is finished, shown as complete on the chart
  // and protected from accidental edits. See ChartPage / the wizard's lock step.
  locked: boolean;
}

export interface BboxIn {
  y0: number;
  y1: number;
  x0: number;
  x1: number;
  mask_strokes: MaskStroke[];
  baseline_y: number;
  midband_y: number;
  n_anchors: number;
  guides?: GuideConfig;
  // Optional so an omitted value preserves the stored flag (mirrors guides).
  locked?: boolean;
}

export interface StrokePoint {
  x: number;
  y: number;
  pressure?: number | null;
  t?: number | null;
  // Last sample of a stroke before the pen is lifted (German: Absetzen); the
  // next point starts a new stroke. Absent/false continues the stroke, so a
  // single-stroke path carries no markers. Mirrors StrokePoint in schemas.py.
  pen_up?: boolean;
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
  // First polygon, kept for older clients (identical to outline_polygons[0]).
  outline_polygon: Array<[number, number]>;
  // One filled outline polygon per pen-stroke — a pen lift is a real gap, not a
  // bar bridging the two strokes.
  outline_polygons: Array<Array<[number, number]>>;
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
  // Index of each pen-stroke's first sample in the polylines, so the overlay can
  // draw separate strokes instead of bridging a pen lift. [0] => one stroke.
  polyline_stroke_starts: number[];
  placement: { x_origin_px: number; baseline_y_px: number; unit_px: number };
}
