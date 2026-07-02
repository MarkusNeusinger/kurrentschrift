// Wire types — hand-synced with `api/schemas.py`. The API is small enough
// that codegen would be more bookkeeping than it saves.

// One freeform eraser stroke (German: Radierer): a brush polyline + radius, in
// chart-pixel coords. Replaces the old rectangle excludes. Mirrors MaskStroke
// in api/schemas.py.
export interface MaskStroke {
  points: Array<[number, number]>;
  radius: number;
}

// One crop patch (German: eingesetzte Zelle): a donor rectangle copied from
// elsewhere on the *same* chart into the crop at a destination, all chart-pixel
// coords. `src` is [x0, y0, x1, y1], `dst` is the top-left [x, y]. Composited by
// darken before binarisation, so only the donor's ink lands — lets a glyph with
// no own cell borrow another's strokes (e.g. ü/ö taking the umlaut from ä).
// Mirrors Patch in api/schemas.py.
export interface Patch {
  src: [number, number, number, number];
  dst: [number, number];
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

// A reading-drill quiz word. Mirrors QuizWordOut in api/schemas.py. `word` is
// the clean display/answer form; `fugen` is the optional render form carrying a
// `|` morpheme marker (round Schluss-s in compounds); `note` glosses dated
// words in the reveal. Same shape as the local WordEntry fallback.
export interface QuizWordOut {
  word: string;
  distractors: string[];
  era: 'modern' | 'historic';
  note?: string | null;
  fugen?: string | null;
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
// horizontal baseline (90° = upright; Kurrent um 1900 ~60-70°, the Loth 1866
// chart measures ~50°), matching source.slant_deg. slant_xs lists the baseline crossing of each slant line
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
  // Manual ink brush (German: Tinten-Pinsel): the eraser's positive twin, same
  // {points, radius} shape, painted as ink before binarisation.
  ink_strokes: MaskStroke[];
  // Crop patches (German: eingesetzte Zelle): donor regions from elsewhere on
  // the same chart composited into the crop, for glyphs with no own cell (e.g.
  // ü/ö borrowing ä's umlaut). See Patch.
  patches: Patch[];
  baseline_y: number;
  midband_y: number;
  n_anchors: number;
  guides: GuideConfig;
  // Manual "done" marker: the glyph is finished, shown as complete on the chart
  // and protected from accidental edits. See ChartPage / the wizard's lock step.
  locked: boolean;
  // Per-letter "positions authored separately" marker (German: aufgetrennt).
  // false (default): the three positional forms share one authored form and the
  // sidebar/quiz/lock treat the letter as one unit. true: positions differ and
  // are authored/locked/quizzed independently. Stored on all three sibling rows
  // and read with `.some` via isLetterSplit (constants.ts). See the wizard.
  split: boolean;
  // Per-glyph speck auto-fill (German: Lücken füllen): max enclosed-hole area
  // (px²) filled before skeletonisation; 0 = off.
  fill_holes_max_area: number;
}

export interface BboxIn {
  y0: number;
  y1: number;
  x0: number;
  x1: number;
  mask_strokes: MaskStroke[];
  ink_strokes: MaskStroke[];
  // Replace-semantics like ink_strokes: the client holds the full list and
  // resends it on every save, so an omitted/empty list clears the patches.
  patches: Patch[];
  baseline_y: number;
  midband_y: number;
  n_anchors: number;
  guides?: GuideConfig;
  // Optional so an omitted value preserves the stored flag (mirrors guides).
  locked?: boolean;
  // Optional so an omitted value preserves the stored flag (mirrors locked).
  // Written fanned out across the three sibling positions; see the wizard.
  split?: boolean;
  // Optional so an omitted value preserves the stored setting (mirrors locked).
  fill_holes_max_area?: number;
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
  // A locked glyph (Bbox.locked) rejects writes (423) unless this is set —
  // overriding the lock is an explicit, deliberate decision.
  force?: boolean;
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

// Render subset served by the public write endpoints (GET …/write/glyphs):
// exactly what the "as written" surfaces (WrittenGlyph/WrittenWord/WrittenSheet)
// draw — template-frame silhouettes + centerlines in writing order, resolved
// widths, lineature guides, and the §4 connection metadata for word
// composition. The admin /diagnostic payload (DiagnosticData) is a superset,
// so admin callers can hand their payload to the same renderers.
export interface GlyphRenderData {
  // Set on batch items so the client can key the response; absent on payloads
  // embedded in admin responses.
  glyph_key?: string;
  anchors_template: Array<[number, number]>;
  half_widths_template: number[];
  // Preferred silhouette: per pen-stroke a list of rings (exterior + holes)
  // from the backend capsule union — render all rings of one stroke as a
  // single path with fill-rule evenodd. Falls back to outline_polygons.
  outline_paths?: Array<Array<Array<[number, number]>>>;
  // Legacy ribbon fallbacks — only present on admin /diagnostic payloads.
  outline_polygon?: Array<[number, number]>;
  outline_polygons?: Array<Array<[number, number]>>;
  // One centerline polyline per pen-stroke, in writing order, running down the
  // spine of the matching silhouette. Drives the animated "as written" reveal.
  centerlines_template?: Array<Array<[number, number]>>;
  template_guides: { baseline: number; midband: number; ascender: number; descender: number };
  // Connection points for word composition (architektur.md §4): the renderer
  // places each glyph along the baseline and draws the Übergang from glyph A's
  // `exit_pt` to glyph B's `entry`. `xy` is in the same template frame as
  // `anchors_template`. Optional for back-compat with older payloads.
  entry?: CouplingPointOut;
  exit_pt?: CouplingPointOut;
  advance?: number | null;
}

// GET …/write/glyphs?keys=… — batch render payloads; keys without a canonical
// land in `missing` instead of failing the batch.
export interface WriteGlyphsOut {
  glyphs: GlyphRenderData[];
  missing: string[];
}

// One stroke/connector of a composed word, in the composed word frame (y up),
// in writing order. A glyph stroke carries filled silhouette `rings`; a
// connector carries a constant `stroke_width`. Both carry the `centerline` the
// renderer sweeps its reveal mask along (`mask_width` wide). `lift` = a pen
// lift precedes this item (short pause); `diacritic` marks the deferred
// floating marks (i-dot, u-bow, umlaut) flushed after the word body.
export interface DrawItemOut {
  centerline: Array<[number, number]>;
  // One stroke's silhouette rings (exterior + holes, drawn evenodd).
  rings?: Array<Array<[number, number]>>;
  stroke_width?: number;
  mask_width: number;
  lift: boolean;
  diacritic?: boolean;
}

// GET …/write/word?text=… — the whole word/line composed server-side
// (core.shaping + core.compose): shaping, placement and the generated
// Übergänge in one cacheable request; the client only animates the items.
export interface ComposedWordOut {
  text: string;
  items: DrawItemOut[];
  bounds: { min_x: number; max_x: number; min_y: number; max_y: number };
  // Lineature levels (from the first rendered glyph; all share the style ratio).
  guides: GlyphRenderData['template_guides'] | null;
  // glyph_keys that could not be placed (no canonical) — surfaced so callers
  // can flag the letters; closed-set ligatures already decomposed server-side.
  missing: string[];
}

export interface DiagnosticData extends GlyphRenderData {
  crop_size: { w: number; h: number };
  skeleton_polyline_px: Array<[number, number]>;
  anchors_px: Array<[number, number]>;
  half_widths_px: number[];
  // First polygon, kept for older clients (identical to outline_polygons[0]).
  outline_polygon: Array<[number, number]>;
  // One filled outline polygon per pen-stroke — a pen lift is a real gap, not a
  // bar bridging the two strokes.
  outline_polygons: Array<Array<[number, number]>>;
  baseline_y_crop: number;
  midband_y_crop: number;
  slant_deg: number;
  // Anchor indices sitting exactly on detected within-stroke reversal corners
  // (Umkehrpunkte) — rendered with distinct markers. Optional for back-compat.
  corner_anchors?: number[];
}

// Image-space quality of a template vs its crop (served by GET .../quality).
// One of two shapes depending on the style's metric, sharing the headline keys:
//   - Kurrent (core/quality.py::template_quality_metrics): geo_rmse_px, width_tv_*, waviness_ratio
//   - Sütterlin (core/quality_suetterlin.py::suetterlin_quality_metrics): naturalness, gate, components
// The metric-specific fields are optional; presence of `naturalness` discriminates.
export interface QualityData {
  iou: number;
  dice: number;
  chamfer_mean_px: number;
  chamfer_p95_px: number;
  pred_area_px: number;
  ink_area_px: number;
  // Aggregate 0–100 (higher better) and its complement (lower better).
  score: number;
  loss: number;
  n_samples: number;
  // Kurrent (pressure/Schwellzug) metric only.
  geo_rmse_px?: number;
  width_tv_rendered_px?: number;
  width_tv_ink_px?: number;
  waviness_ratio?: number;
  // Sütterlin (Gleichzug) naturalness metric only.
  gate?: number;
  naturalness?: number;
  geo_db_rmse_px?: number;
  components?: {
    smoothness: number;
    verticality: number;
    corner: number;
    collinearity: number;
    retrace: number;
    coverage: number;
    naturalness: number;
  };
}

// GET .../quality payload: what the DB holds vs what a fresh re-derivation
// with the current pipeline code would achieve (dry run, nothing written).
export interface QualityComparison {
  stored: QualityData;
  candidate: QualityData | null;
  candidate_refine: Record<string, unknown> | null;
}

// One variant of the POST .../trace-preview dry run: a DiagnosticData-shaped
// render payload (WrittenGlyph consumes it directly) plus its quality score
// and the crop-pixel silhouette (per-stroke rings) for the comparison/overlay.
export interface WrittenPreviewData extends DiagnosticData {
  quality?: QualityData | null;
  refine?: Record<string, unknown> | null;
  // Per pen-stroke a list of rings (exterior + holes, evenodd) in crop pixels —
  // drawn beside / over the crop image in the wizard's Optimieren step.
  silhouette_px?: Array<Array<Array<[number, number]>>>;
}

// POST .../trace-preview payload: the drawn Weg derived once raw (measured
// only) and once optimized — nothing written; the wizard compares both.
export interface TracePreviewOut {
  raw: WrittenPreviewData;
  refined: WrittenPreviewData;
}

export interface FitMeta {
  // Residual-based verdict (geo RMSE within tolerance) — what the UI shows.
  converged: boolean;
  // Mirror of `converged` kept for older payload consumers.
  success: boolean;
  // Raw scipy stop status — debugging only; it anti-correlates with quality.
  optimizer_success: boolean;
  message: string;
  iterations: number;
  n_evaluations: number;
  geo_rmse_px: number;
  geo_rmse_px_initial: number;
  width_rmse_px: number;
  // Skeleton→template distance: high values mean parts of the original ink
  // are not covered by the fitted template.
  coverage_rmse_px: number;
  reg_energy: number;
  max_anchor_delta: number;
  lambda_reg: number;
  width_weight: number;
  coverage_weight: number;
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
  // Filled silhouette of the fit in crop pixels: per pen-stroke a list of
  // rings (exterior + holes, evenodd) — overlay on the crop to judge whether
  // the fitted ink covers the original.
  fitted_outline_px?: Array<Array<Array<[number, number]>>>;
  placement: { x_origin_px: number; baseline_y_px: number; unit_px: number };
}
