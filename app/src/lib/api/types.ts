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

// One connected-writing specimen (word or letter pair) from a source's
// words.json sidecar. Mirrors WordSampleOut in api/schemas.py. baseline_y /
// midband_y are crop-local pixels, so an engine-written overlay registers with
// scale = baseline_y - midband_y px per x-height unit; the crop bytes come
// from wordSampleCropUrl.
export interface WordSampleOut {
  id: string;
  word: string;
  kind: 'word' | 'pair';
  // Sidecar `set` tag — a plate by another writer (e.g. the Abb.-22
  // Schülerschrift); null for the headline hand.
  sample_set: string | null;
  width: number;
  height: number;
  baseline_y: number;
  midband_y: number;
  // The sample's rect on the plate page, [x0, y0, x1, y1] in PAGE pixels —
  // the origin that turns a page-pixel occurrence box (InstanceOut) into a
  // crop-local one: cropX = x0 - rect[0], cropY = y0 - rect[1]. Optional
  // because the endpoint is cached long (stale-while-revalidate spans days):
  // a browser/CDN may still serve the pre-`rect` schema after a deploy.
  rect?: number[];
}

// Fit context of one stored word trace (see tools/laufform/harvest.py). Every
// field optional: authored rows written by hand may carry less. registration_px
// + xh_px map trace units to crop pixels: px = (u·xh + tx, baseline_row + ty − v·xh).
// Slot indices (fitted/unfitted/rmse keys) index into the row's `slots` list.
export interface WordInstanceMeasurements {
  registration_px?: { tx: number; ty: number; baseline_row: number };
  xh_px?: number;
  fitted_slots?: number[];
  unfitted_slots?: number[];
  geo_rmse_px_by_slot?: Record<string, number>;
}

// One stored word-occurrence trace (handmodell H1/H2). Mirrors WordInstanceOut
// in api/schemas.py: slot labels + the traced pen path in the word's
// registration frame (template units, baseline = 0, midband = 1, y up), one
// polyline per pen-down stretch. `authored` rows are manual admin traces a
// re-harvest never overwrites; the matching crop comes from wordSampleCropUrl.
export interface WordInstanceOut {
  kind: 'word' | 'pair';
  specimen_id: string;
  word: string;
  slots: string[];
  strokes: Array<Array<[number, number]>>;
  provenance: 'traced' | 'authored';
  hand_id: string | null;
  measurements: WordInstanceMeasurements;
}

// One item of `PUT /sources/{id}/word-instances`. Mirrors WordInstanceItem in
// api/schemas.py — same frame as WordInstanceOut.strokes, plus the schema
// bounds the editor has to respect (1..128 strokes, 2..4096 points each,
// |coord| ≤ 100; see sections/admin/belege/registration.ts). `authored` marks a
// manual admin trace: it replaces a harvested row and survives every re-harvest.
export interface WordInstanceItemIn {
  kind: 'word' | 'pair';
  specimen_id: string;
  word: string;
  slots: string[];
  strokes: Array<Array<[number, number]>>;
  provenance: 'traced' | 'authored';
  measurements?: WordInstanceMeasurements;
}

// The writer a batch of occurrences belongs to (get-or-create). Mirrors HandIn.
// The server upserts the row wholesale, so a caller editing ONE occurrence
// echoes the hand back as read (getHand) instead of sending id + label only —
// otherwise era/note would be wiped as a side effect of saving a trace.
export interface HandIn {
  id: string;
  label: string;
  era?: string | null;
  note?: string | null;
}

export interface HandOut {
  id: string;
  style_id: string | null;
  label: string;
  era: string | null;
  note: string | null;
}

// Body of the word-instance batch PUT. `replace: true` is the harvest's wipe —
// the word editor sends a single item without it.
export interface WordInstanceBatchIn {
  hand: HandIn;
  replace?: boolean;
  items: WordInstanceItemIn[];
}

// Result of an occurrence batch write (BatchStoreOut). `skipped` counts the
// items the authored-overwrite protection refused.
export interface BatchStoreOut {
  hand_id: string;
  stored: number;
  deleted: number;
  skipped: number;
}

// Fit context of ONE stored letter occurrence (tools/laufform/harvest.py).
// `specimen_id` + `slot` tie the row back to its word sample and the slot
// index inside it; `geo_rmse_px` is that fit's residual — the Werkbank's
// worst-first ranking per letter.
export interface InstanceMeasurements {
  specimen_id?: string;
  slot?: number;
  prev_key?: string | null;
  next_key?: string | null;
  shift_xh?: [number, number];
  registration_px?: [number, number];
  geo_rmse_px?: number;
  xh_px?: number;
}

// One stored letter occurrence (handmodell H1). Mirrors InstanceOut in
// api/schemas.py. The box (y0/y1/x0/x1) is in PAGE pixels of the specimen
// plate — subtract the word sample's `rect` origin for crop-local coords.
export interface InstanceOut {
  glyph_key: string;
  glyph: string;
  position: string;
  variant: number;
  hand_id: string | null;
  y0: number;
  y1: number;
  x0: number;
  x1: number;
  anchors: Array<[number, number]>;
  half_widths: number[];
  measurements: InstanceMeasurements;
}

// Dissection QC of one observed join (tools/pairlab/harvest.py): `gen_chamfer`
// is how far the GENERATED Übergang sits from the specimen ink (xh units,
// lower better), `fit_ok` whether both letters fitted cleanly enough for the
// dissection to be trusted.
export interface PairInstanceMeasurements {
  fit_ok?: boolean;
  gen_chamfer?: number;
  harvest_chamfer?: number;
  a_resid?: number;
  b_resid?: number;
}

// One stored join occurrence (handmodell H2). Mirrors PairInstanceOut in
// api/schemas.py — `geometry` shares the glyph_pairs frame (connector +
// placement offset relative to the left glyph's exit), so an occurrence
// compares directly with the override the pair editor writes.
export interface PairInstanceOut {
  left_key: string;
  right_key: string;
  kind: 'word' | 'pair';
  specimen_id: string;
  slot: number;
  hand_id: string | null;
  geometry: PairGeometry;
  measurements: PairInstanceMeasurements;
}

// Pooled layer-1 statistics of ONE glyph aggregate (core/aggregate.py::
// _mean_stats). Every sub-key is optional by design: a measurement missing
// across the whole group is omitted rather than written as a null — an absent
// measurement is not a measured zero.
export interface AggregateMeanStats {
  geo_rmse_px?: { mean: number; max: number };
  xh_px_mean?: number;
  // Histogram of the occurrence positions (initial/medial/final/…).
  positions?: Record<string, number>;
  n_specimens?: number;
}

// Per-anchor, per-axis median absolute deviation — same order and length as
// `cluster_center`, in the same template units.
export interface AggregateHull {
  anchor_mad?: Array<[number, number]>;
}

// One per-hand glyph aggregate (Stufenplan H1). Mirrors AggregateOut in
// api/schemas.py: `cluster_center` is the per-anchor median of the hand's
// occurrences — the Laufform in normalised template coordinates (baseline = 0,
// midband = 1, y up) — and `hull.anchor_mad` its spread. Admin-gated read:
// an aggregate is learned geometry (quellen-und-rechte.md §5).
export interface AggregateOut {
  glyph_key: string;
  glyph: string;
  variant: number;
  cluster_center: Array<[number, number]>;
  hull: AggregateHull;
  mean_stats: AggregateMeanStats;
  n_instances: number;
  // What the engine CURRENTLY writes for this glyph in a flowing run (the
  // stored template variant 100) and how far it sits from the median above, in
  // x-height units. Both null where the comparison has no meaning: a non-base
  // variant, no stored running form yet, or a differing anchor count. This is
  // the freshness read the deliberate apply step is judged by.
  laufform_anchors: Array<[number, number]> | null;
  laufform_dev_xh: number | null;
}

// One rebuilt key in the rebuild report. `laufform_dev_xh` is the H1 Prüfstein
// (mean anchor distance between the recomputed median and the stored Laufform
// row, x-height units); null when there is no such row or its anchor count
// differs.
export interface AggregateKeySummary {
  glyph_key: string;
  variant: number;
  n_instances: number;
  laufform_dev_xh: number | null;
}

// Result of POST /hands/{hand_id}/aggregates/rebuild. `deleted` counts the
// hand's previous rows (the rebuild replaces wholesale), `skipped` the
// occurrences left out per reason ('anchor_shape', 'below_min_n').
export interface AggregateRebuildOut {
  hand_id: string;
  stored: number;
  deleted: number;
  skipped: Record<string, number>;
  keys: AggregateKeySummary[];
}

// One glyph whose Laufform row the apply step derived from the stored
// aggregate. `laufform_dev_xh` is measured BEFORE the write — the distance the
// apply just closed (null when no running form existed yet or its anchor count
// differed); `created` separates a first write from an update.
export interface AggregateApplyKeySummary {
  glyph_key: string;
  variant: number;
  n_instances: number;
  laufform_dev_xh: number | null;
  created: boolean;
}

// One aggregate the apply left alone. Reasons: 'laufform_variant' /
// 'non_base_variant' (only base-variant aggregates may feed the derived row —
// never itself), 'no_base_template' (the chart ductus prior is missing) and
// 'anchor_count' (aggregate and chart row disagree, so the topology would not
// carry over).
export interface AggregateApplySkip {
  glyph_key: string;
  variant: number;
  reason: string;
}

// Result of POST /hands/{hand_id}/aggregates/apply-laufform — the ONE step that
// promotes learned statistics into what the engine actually writes.
// `excluded` names the glyph keys the request's own `glyph_keys` selection left
// out — the caller's decision, kept apart from `skipped` (which stays the
// endpoint's "could not" report). Empty when the request named no selection.
export interface AggregateApplyOut {
  hand_id: string;
  style_id: string;
  applied: AggregateApplyKeySummary[];
  skipped: AggregateApplySkip[];
  excluded: string[];
}

// Pooled dissection QC of ONE pair aggregate (core/aggregate.py::
// _pair_mean_stats), same optional-key convention as AggregateMeanStats.
// `gen_chamfer` is the audit number this layer exists for: how far the
// GENERATED Übergang sits from the specimen skeleton (x-height units).
export interface PairAggregateMeanStats {
  gen_chamfer?: { mean: number; max: number };
  harvest_chamfer?: { mean: number; max: number };
  resid?: { mean: number; max: number };
  gap_ink_share?: number;
  // Histogram over the word plates vs. the pair drills.
  kinds?: Record<string, number>;
  n_specimens?: number;
}

export interface PairAggregateHull {
  offset_mad?: [number, number];
  connector_mad?: Array<[number, number]>;
}

// One per-hand pair aggregate (Stufenplan H2). Mirrors PairAggregateOut in
// api/schemas.py — the median transition in the SAME frame as a glyph_pairs
// override and as every PairInstanceOut.geometry (template units relative to
// the left glyph's exit, baseline-locked, y up), so occurrences, median and
// override all draw in one sketch. `connector_center` is the per-point median
// of the arc-length-resampled centerlines and ends at `offset_center`.
// Read-only by design: no `apply` counterpart exists, the §4 generator stays
// the writing path's default.
export interface PairAggregateOut {
  left_key: string;
  right_key: string;
  offset_center: [number, number];
  connector_center: Array<[number, number]>;
  hull: PairAggregateHull;
  mean_stats: PairAggregateMeanStats;
  n_instances: number;
}

export interface PairAggregateKeySummary {
  left_key: string;
  right_key: string;
  n_instances: number;
  gen_chamfer_mean: number | null;
}

// Result of POST /hands/{hand_id}/pair-aggregates/rebuild; `skipped` reasons
// are 'fit_bad', 'geometry', 'below_min_n'.
export interface PairAggregateRebuildOut {
  hand_id: string;
  stored: number;
  deleted: number;
  skipped: Record<string, number>;
  pairs: PairAggregateKeySummary[];
}

// One filed Auftragskorb task (Werkbank W1). Mirrors WorkItemIn/WorkItemOut in
// api/schemas.py: `kind` decides which target fields are required ('letter' →
// glyph_key, 'pair' → left_key + right_key, 'word' → word or specimen_id), and
// specimen_kind/specimen_id must be sent TOGETHER or not at all (422 otherwise
// — an id without its namespace may point at nothing). 'note' is the
// target-less fourth kind: a general small thing whose whole content is the
// `note` text, so that is the field IT requires. Fully admin-gated.
export interface WorkItemIn {
  kind: WorkItemKind;
  glyph_key?: string | null;
  left_key?: string | null;
  right_key?: string | null;
  word?: string | null;
  specimen_kind?: 'word' | 'pair' | null;
  specimen_id?: string | null;
  note?: string;
}

// The marked level. The three doctrine levels plus 'note', which has no target
// and no writing-path stage — it closes on its resolution alone.
export type WorkItemKind = 'letter' | 'pair' | 'word' | 'note';

// The stages of the writing path a complaint can be traced to
// (optimierungs-werkbank.md §3), in the triage order §5 prescribes. Mirrors
// WORK_ITEM_STAGES in api/schemas.py.
export type WorkItemStage =
  | 'chart_ductus'
  | 'laufform'
  | 'join_rule'
  | 'composition'
  | 'pair_override'
  | 'word_trace'
  | 'not_reproducible';

// filed -> understood -> closed, plus the two exits: 'open' is also where a
// rejected restatement lands again, 'returned' means the author has to supply
// ground truth before anything can be fixed.
export type WorkItemStatus = 'open' | 'ack' | 'done' | 'returned';

export interface WorkItemOut {
  id: number;
  source_id: string;
  kind: WorkItemKind;
  glyph_key: string | null;
  left_key: string | null;
  right_key: string | null;
  word: string | null;
  specimen_kind: string | null;
  specimen_id: string | null;
  note: string;
  status: WorkItemStatus;
  // The working session's protocol (§5, Werkbank W4): what it understood the
  // task to be and whether it reproduced the complaint, written BEFORE it
  // changes anything; then the diagnosed stage and what changed.
  understanding: string | null;
  reproduced: 'yes' | 'no' | 'partly' | null;
  stage: WorkItemStage | null;
  resolution: string | null;
  acked_at: string | null;
  closed_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

// Partial update. The API enforces the protocol: 'ack' needs understanding +
// reproduced, 'done'/'returned' need a stored understanding, a stage and a
// resolution (422 otherwise). The UI only ever sends the way back to 'open' —
// the admin rejecting a restatement, which is always allowed.
export interface WorkItemUpdate {
  note?: string;
  status?: WorkItemStatus;
  understanding?: string;
  reproduced?: 'yes' | 'no' | 'partly';
  stage?: WorkItemStage;
  resolution?: string;
}

// Per-segment attribution row of a scored specimen (redesign R1b Stufe 2) —
// a connector row names the join (`pair`), a glyph row the letter; `penalty`
// is the row's headline component on the metric's saturation scale.
export interface WordSampleScoreSegment {
  kind: 'connector' | 'glyph';
  penalty: number;
  pair?: [string | null, string | null] | null;
  glyph_key?: string | null;
}

// Admin-only score of one specimen: the frozen wordbench ruler run on the
// SAME composition /write/word serves (loss = 0.45·transition +
// 0.35·coverage + 0.20·width, lower better; failed = a template hole scores
// 1.0). Mirrors the /word-samples/{id}/score response.
export interface WordSampleScoreOut {
  id: string;
  word: string;
  loss: number;
  failed: boolean;
  transition?: number;
  coverage?: number;
  width?: number;
  missing: string[];
  segments: WordSampleScoreSegment[];
}

// One letter-pair override (redesign R3). Mirrors GlyphPairOut/PairGeometry in
// api/schemas.py: `offset` is where the right glyph's entry lands relative to
// the LEFT glyph's exit (template units; the composer applies the horizontal
// part), `connector` is the join's centerline relative to the left glyph's
// exit, drawn verbatim instead of the generated Übergang. Only `approved`
// rows ever render; `provenance` = harvested (M4-fitted from a specimen,
// citing specimen_id) | authored (freehand in the pair editor).
export interface PairGeometry {
  offset: number[];
  connector: Array<[number, number]>;
}

export interface GlyphPairOut {
  left_key: string;
  right_key: string;
  variant: number;
  geometry: PairGeometry;
  provenance: 'harvested' | 'authored';
  provenance_source_id: string | null;
  specimen_id: string | null;
  approved: boolean;
}

export interface GlyphPairIn {
  geometry: PairGeometry;
  provenance: 'harvested' | 'authored';
  specimen_id?: string | null;
  approved: boolean;
  variant?: number;
}

// Practice-sheet-style guide lines (Hilfslinien) drawn over a glyph crop —
// same vocabulary as the worksheet rulers in lib/lineatur.ts. baseline + waist
// come from the bbox calibration; ascender/descender are toggleable; slant is
// one or more positionable, angled main lines. slant_deg is measured from the
// horizontal baseline (90° = upright; Kurrent um 1900 ~60-70°, the Loth 1866
// chart measures ~50°), matching source.slant_deg. slant_xs lists the baseline crossing of each slant line
// (all share slant_deg) — individually draggable for letters like m/n/u;
// slant_x is the single-line fallback. Mirrors GuideConfig in api/schemas.py.
export interface GuideConfig {
  slant_deg?: number | null;
  slant_x?: number | null;
  slant_xs?: number[] | null;
  show_ascender?: boolean;
  show_descender?: boolean;
}

// Item of GET /sources/{id}/bboxes/status — flags + layout scalars only. The
// public quiz gates its vocabulary on locked, the public Tafel lays its
// sheet out from the crop rect + baseline; the full BboxOut list would drag
// every mask/ink/patch blob over the wire for those few scalars.
export interface BboxStatusOut {
  glyph_key: string;
  locked: boolean;
  x0: number;
  x1: number;
  y0: number;
  y1: number;
  baseline_y: number;
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
  // Optional so an omitted value preserves the stored count (mirrors the API's
  // BboxIn): the server keeps bbox.n_anchors truthful to the derived canonical
  // after trace/resample, so routine bbox saves must not echo a stale value back.
  n_anchors?: number | null;
  guides?: GuideConfig;
  // Optional so an omitted value preserves the stored flag (mirrors guides).
  locked?: boolean;
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
  raw_path: StrokePoint[];
  n_anchors?: number | null;
  variant?: number;
  // A locked glyph (Bbox.locked) rejects writes (423) unless this is set —
  // overriding the lock is an explicit, deliberate decision.
  force?: boolean;
}

// One end of a stroke: where the pen lands/leaves and in which direction.
// Mirrors EndPointOut in api/schemas.py. Rows authored before the coupling
// label was dropped still carry a `coupling` key in their stored JSON; nothing
// reads it (the coupling height is the composer's class rule).
export interface EndPointOut {
  xy: [number, number];
  tangent_deg: number;
}

export interface GlyphSummary {
  glyph_key: string;
  glyph: string | null;
  variant: number;
  advance: number | null;
  has_data: boolean;
}

export interface GlyphOut {
  glyph_key: string;
  glyph: string;
  variant: number;
  advance: number;
  entry: EndPointOut;
  exit_pt: EndPointOut;
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
  entry?: EndPointOut;
  exit_pt?: EndPointOut;
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
// connector carries a constant `stroke_width` — except under a broad-nib
// style, where generated strokes ship their swept-nib silhouette as `rings`
// too (rings win: an item with rings is filled, never stroked). Both carry
// the `centerline` the renderer sweeps its reveal mask along (`mask_width`
// wide). `lift` = a pen lift precedes this item (short pause); `diacritic`
// marks the deferred floating marks (i-dot, u-bow, umlaut) flushed after the
// word body.
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

// Item of GET /sources/{id}/templates/quality — the score the derivation
// stamped onto the row (trace_meta.quality), i.e. the quality AT AUTHORING
// TIME, not a re-score with today's metric. Cheap for a whole alphabet exactly
// because nothing is recomputed; the per-glyph QualityComparison below is the
// one that re-derives. Null for rows traced before the metric existed.
// The list covers EVERY variant of the style. A derived Laufform row (variant
// 100) inherits the chart row's trace_meta, so it repeats the chart form's
// score — filter to variant 0 unless you mean exactly that.
export interface TemplateQualityOut {
  glyph_key: string;
  variant: number;
  quality: QualityData | null;
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
  advance: number;
  anchors: Array<[number, number]>;
  half_widths: number[];
  entry: EndPointOut;
  exit_pt: EndPointOut;
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
