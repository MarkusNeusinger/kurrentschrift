// Thin endpoint wrappers over the FastAPI backend. Every source-scoped path
// takes the source id explicitly: the public pages stay pinned to the
// site-wide CONFIG.sourceId, while the admin passes its runtime-switchable
// active source (see AdminContext) — a hidden global here would let the
// admin's selection leak into the public surfaces.

import { CONFIG } from '@/global-config';
import { apiFetch, asJson, type RetryOptions } from '@/lib/api/client';
import type {
  AggregateOut,
  AggregateApplyOut,
  AggregateRebuildOut,
  BatchStoreOut,
  BboxIn,
  BboxOut,
  BboxStatusOut,
  ComposedWordOut,
  DiagnosticData,
  FitData,
  GlyphOut,
  GlyphSummary,
  HandOut,
  InstanceOut,
  PairAggregateOut,
  PairAggregateRebuildOut,
  PairInstanceOut,
  QualityComparison,
  QuizWordOut,
  SourceOut,
  StyleOut,
  GlyphPairIn,
  GlyphPairOut,
  TracePreviewOut,
  TraceRequest,
  WordInstanceBatchIn,
  WordInstanceOut,
  WordSampleOut,
  WordSampleScoreOut,
  WorkItemIn,
  WorkItemOut,
  WorkItemStatus,
  WorkItemUpdate,
  WriteGlyphsOut,
} from '@/lib/api/types';

// Where to reach the API. The apex `/api/*` is gated by Cloudflare Access — it
// 302-redirects anonymous visitors to the CF login, and following that
// cross-origin redirect trips the browser's CORS check, so PUBLIC pages can't
// read it. They go straight to the open `api.` subdomain (CONFIG.publicApiBase)
// instead: same data, no auth gate. The ADMIN (`/admin/*`) keeps the apex so
// its CF-Access cookie still authorizes writes — Access injects the verifying
// JWT only on that path. Dev has neither gate; the Vite proxy serves `/api`
// same-origin, so we stay on apiBase there. Resolved per call (read at request
// time) so client-side navigation between public and admin routes is honoured.
const onAdminRoute = (): boolean =>
  typeof window !== 'undefined' && window.location.pathname.startsWith('/admin');
const apiRoot = (): string =>
  (import.meta.env.DEV || onAdminRoute()) ? CONFIG.apiBase : CONFIG.publicApiBase;

const src = (sourceId: string, path: string) => `${apiRoot()}/sources/${encodeURIComponent(sourceId)}${path}`;

export const getStyles = (retry?: RetryOptions): Promise<StyleOut[]> =>
  apiFetch(`${apiRoot()}/styles`, {}, retry).then(asJson<StyleOut[]>);

// The public reading-drill word bank (un-scoped, not source-specific).
export const getQuizWords = (retry?: RetryOptions): Promise<QuizWordOut[]> =>
  apiFetch(`${apiRoot()}/quiz-words`, {}, retry).then(asJson<QuizWordOut[]>);

export const getSources = (retry?: RetryOptions): Promise<SourceOut[]> =>
  apiFetch(`${apiRoot()}/sources`, {}, retry).then(asJson<SourceOut[]>);

export const getSource = (sourceId: string, retry?: RetryOptions): Promise<SourceOut> =>
  apiFetch(src(sourceId, ''), {}, retry).then(asJson<SourceOut>);

export const chartUrl = (sourceId: string): string => src(sourceId, '/chart');
// `view='mask'` returns the binarised mask the skeleton sees (auto-fill
// colour-coded) instead of the raw grayscale scan — the wizard's "Maske zeigen".
export const cropUrl = (sourceId: string, glyphKey: string, cacheBust?: number, view?: 'raw' | 'mask'): string => {
  const qs = new URLSearchParams();
  if (cacheBust) qs.set('t', String(cacheBust));
  if (view === 'mask') qs.set('view', 'mask');
  const s = qs.toString();
  return src(sourceId, `/bboxes/${encodeURIComponent(glyphKey)}/crop${s ? `?${s}` : ''}`);
};

// Letter-pair overrides (redesign R3). Public callers see approved rows only;
// `all: true` (the admin matrix/editor) additionally returns unreviewed rows
// and rides the admin auth the client already sends on /admin routes.
export const getPairs = (sourceId: string, opts?: { all?: boolean }, retry?: RetryOptions): Promise<GlyphPairOut[]> =>
  apiFetch(src(sourceId, `/pairs${opts?.all ? '?all=true' : ''}`), {}, retry).then(asJson<GlyphPairOut[]>);

export const getPair = (sourceId: string, leftKey: string, rightKey: string): Promise<GlyphPairOut> =>
  apiFetch(src(sourceId, `/pairs/${encodeURIComponent(leftKey)}/${encodeURIComponent(rightKey)}`)).then(
    asJson<GlyphPairOut>,
  );

export const putPair = (
  sourceId: string,
  leftKey: string,
  rightKey: string,
  body: GlyphPairIn,
): Promise<GlyphPairOut> =>
  apiFetch(src(sourceId, `/pairs/${encodeURIComponent(leftKey)}/${encodeURIComponent(rightKey)}`), {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(asJson<GlyphPairOut>);

export const deletePair = (sourceId: string, leftKey: string, rightKey: string): Promise<void> =>
  apiFetch(src(sourceId, `/pairs/${encodeURIComponent(leftKey)}/${encodeURIComponent(rightKey)}`), {
    method: 'DELETE',
  }).then(asJson<void>);

// The connected-writing specimens of a source (words.json sidecar) — empty for
// sources without plates. The crop is an <img>-loadable public URL like cropUrl.
// `v` is a cache-buster, bumped when the response schema grows a field the UI
// depends on (v=2: `rect`): the endpoint is cached with a days-long
// stale-while-revalidate window, so without it browsers/CDNs keep serving the
// old shape long after a deploy.
export const getWordSamples = (sourceId: string, retry?: RetryOptions): Promise<WordSampleOut[]> =>
  apiFetch(src(sourceId, '/word-samples?v=2'), {}, retry).then(asJson<WordSampleOut[]>);

export const wordSampleCropUrl = (sourceId: string, sampleId: string): string =>
  src(sourceId, `/word-samples/${encodeURIComponent(sampleId)}/crop`);

// The stored word-occurrence traces of a source (handmodell H1/H2). Public
// GET; a row's crop is wordSampleCropUrl(sourceId, row.specimen_id). `word`
// lists every occurrence of one word TEXT ("wenn" matches wenn + wenn-2).
// `bust` re-fetches past any intermediate cache after a write (the word
// editor's save) — the endpoint itself is uncached.
export const listWordInstances = (
  sourceId: string,
  opts?: { specimenId?: string; word?: string; bust?: number },
  retry?: RetryOptions,
): Promise<WordInstanceOut[]> => {
  const qs = new URLSearchParams();
  if (opts?.specimenId) qs.set('specimen_id', opts.specimenId);
  if (opts?.word) qs.set('word', opts.word);
  if (opts?.bust) qs.set('t', String(opts.bust));
  const s = qs.toString();
  return apiFetch(src(sourceId, `/word-instances${s ? `?${s}` : ''}`), {}, retry).then(asJson<WordInstanceOut[]>);
};

// Admin-gated batch write of word traces (handmodell H1/H2). The word editor
// sends exactly ONE item with provenance 'authored' and without `replace` — the
// server's overwrite protection then replaces that occurrence and leaves every
// other row (and every other authored trace) untouched.
export const putWordInstances = (sourceId: string, body: WordInstanceBatchIn): Promise<BatchStoreOut> =>
  apiFetch(src(sourceId, '/word-instances'), {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(asJson<BatchStoreOut>);

// Hand-scoped paths — statistics belong to the WRITER, not to the plate
// (architektur.md §12), so these are not source-scoped.
const hnd = (handId: string, path: string) => `${apiRoot()}/hands/${encodeURIComponent(handId)}${path}`;

// One writer. Public read; the word editor uses it to echo the occurrence's
// hand back into its batch (id + label + era + note) instead of re-inventing it.
export const getHand = (handId: string, retry?: RetryOptions): Promise<HandOut> =>
  apiFetch(hnd(handId, ''), {}, retry).then(asJson<HandOut>);

// The per-hand statistics over the occurrence layer (Stufenplan H1/H2) —
// FULLY admin-gated, reads included: an aggregate is learned geometry
// (quellen-und-rechte.md §5). Read and rebuild affect no rendering, which is
// why the Werkbank may show and refresh them; the rendering-CHANGING step
// `POST …/aggregates/apply-laufform` is deliberately not wrapped here
// (optimierungs-werkbank.md §3: generated stages are displayed, not edited).
export const listAggregates = (handId: string, retry?: RetryOptions): Promise<AggregateOut[]> =>
  apiFetch(hnd(handId, '/aggregates'), {}, retry).then(asJson<AggregateOut[]>);

// `leftKey`/`rightKey` narrow the listing to one letter's joins or to exactly
// one transition; without them the hand's whole matrix comes back.
export const listPairAggregates = (
  handId: string,
  opts?: { leftKey?: string; rightKey?: string },
  retry?: RetryOptions,
): Promise<PairAggregateOut[]> => {
  const qs = new URLSearchParams();
  if (opts?.leftKey) qs.set('left_key', opts.leftKey);
  if (opts?.rightKey) qs.set('right_key', opts.rightKey);
  const s = qs.toString();
  return apiFetch(hnd(handId, `/pair-aggregates${s ? `?${s}` : ''}`), {}, retry).then(asJson<PairAggregateOut[]>);
};

// Recompute a hand's aggregates from its stored occurrences, replacing the
// previous rows wholesale. Each route keeps its OWN `min_n` default (4 for
// glyphs, 1 for the sparse pairs) — the UI does not second-guess it.
export const rebuildAggregates = (handId: string): Promise<AggregateRebuildOut> =>
  apiFetch(hnd(handId, '/aggregates/rebuild'), { method: 'POST' }).then(asJson<AggregateRebuildOut>);

export const rebuildPairAggregates = (handId: string): Promise<PairAggregateRebuildOut> =>
  apiFetch(hnd(handId, '/pair-aggregates/rebuild'), { method: 'POST' }).then(asJson<PairAggregateRebuildOut>);

// Write the hand's STORED aggregates into the style's Laufform rows (template
// variant 100) — the one step of the whole hand model that changes what the
// engine writes. Everything else here measures; this one renders, which is why
// the UI puts a confirmation in front of it (docs/proposals/
// optimierungs-werkbank.md §3, issue #270) and why it is deliberately NOT a
// side effect of the rebuild above.
export const applyLaufform = (handId: string): Promise<AggregateApplyOut> =>
  apiFetch(hnd(handId, '/aggregates/apply-laufform'), { method: 'POST' }).then(asJson<AggregateApplyOut>);

// The stored LETTER occurrences of a source (handmodell H1). Public GET; the
// boxes are page pixels of the specimen plate, so a crop-local box needs the
// word sample's `rect` origin. The Werkbank loads the whole source once (a few
// hundred rows) and groups client-side; `glyphKey` narrows to one letter.
export const listInstances = (
  sourceId: string,
  opts?: { glyphKey?: string },
  retry?: RetryOptions,
): Promise<InstanceOut[]> => {
  const qs = opts?.glyphKey ? `?glyph_key=${encodeURIComponent(opts.glyphKey)}` : '';
  return apiFetch(src(sourceId, `/instances${qs}`), {}, retry).then(asJson<InstanceOut[]>);
};

// The stored JOIN occurrences of a source (handmodell H2). Public GET, same
// load-once-and-group pattern as listInstances; `leftKey`/`rightKey` narrow to
// one pair.
export const listPairInstances = (
  sourceId: string,
  opts?: { leftKey?: string; rightKey?: string },
  retry?: RetryOptions,
): Promise<PairInstanceOut[]> => {
  const qs = new URLSearchParams();
  if (opts?.leftKey) qs.set('left_key', opts.leftKey);
  if (opts?.rightKey) qs.set('right_key', opts.rightKey);
  const s = qs.toString();
  return apiFetch(src(sourceId, `/pair-instances${s ? `?${s}` : ''}`), {}, retry).then(asJson<PairInstanceOut[]>);
};

// The Auftragskorb (Werkbank W1) — FULLY admin-gated, reads included: these
// are internal work notes, not measurement. `status` splits the round's queue
// ('open') from the archive ('done'); without it both come back, oldest first.
export const listWorkItems = (
  sourceId: string,
  opts?: { status?: WorkItemStatus },
  retry?: RetryOptions,
): Promise<WorkItemOut[]> => {
  const qs = opts?.status ? `?status=${opts.status}` : '';
  return apiFetch(src(sourceId, `/work-items${qs}`), {}, retry).then(asJson<WorkItemOut[]>);
};

export const createWorkItem = (sourceId: string, body: WorkItemIn): Promise<WorkItemOut> =>
  apiFetch(src(sourceId, '/work-items'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(asJson<WorkItemOut>);

// Partial update. The UI's one use is the admin REJECTING a session's
// restatement: back to 'open' with the correction appended to the note. Acking
// and closing belong to the working session and are gated by the API's
// protocol check (§5) — the UI cannot and should not fake them.
export const patchWorkItem = (sourceId: string, itemId: number, body: WorkItemUpdate): Promise<WorkItemOut> =>
  apiFetch(src(sourceId, `/work-items/${itemId}`), {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(asJson<WorkItemOut>);

// Drops a misfiling. A WORKED item is closed with status 'done' + a resolution
// note instead, so the archive stays readable.
export const deleteWorkItem = (sourceId: string, itemId: number): Promise<void> =>
  apiFetch(src(sourceId, `/work-items/${itemId}`), { method: 'DELETE' }).then(asJson<void>);

// Admin-only: the frozen wordbench ruler on one specimen vs the CURRENT
// composition (redesign R1b Stufe 2). CPU-bound server-side — callers fetch
// sequentially, not in a fan-out.
export const getWordSampleScore = (sourceId: string, sampleId: string): Promise<WordSampleScoreOut> =>
  apiFetch(src(sourceId, `/word-samples/${encodeURIComponent(sampleId)}/score`)).then(asJson<WordSampleScoreOut>);

export const getBboxes = (sourceId: string, retry?: RetryOptions): Promise<BboxOut[]> =>
  apiFetch(src(sourceId, '/bboxes'), {}, retry).then(asJson<BboxOut[]>);

// Slim public read for the quiz's availability gating — flags only, none of
// the heavy crop-editing fields.
export const getBboxStatuses = (sourceId: string, retry?: RetryOptions): Promise<BboxStatusOut[]> =>
  apiFetch(src(sourceId, '/bboxes/status'), {}, retry).then(asJson<BboxStatusOut[]>);

export const putBbox = (sourceId: string, glyphKey: string, bbox: BboxIn): Promise<BboxOut> =>
  apiFetch(src(sourceId, `/bboxes/${encodeURIComponent(glyphKey)}`), {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(bbox),
  }).then(asJson<BboxOut>);

export const deleteBbox = (sourceId: string, glyphKey: string): Promise<void> =>
  apiFetch(src(sourceId, `/bboxes/${encodeURIComponent(glyphKey)}`), { method: 'DELETE' }).then(asJson<void>);

export const getGlyphs = (sourceId: string, retry?: RetryOptions): Promise<GlyphSummary[]> =>
  apiFetch(src(sourceId, '/templates'), {}, retry).then(asJson<GlyphSummary[]>);

export const getGlyph = (sourceId: string, glyphKey: string): Promise<GlyphOut> =>
  apiFetch(src(sourceId, `/templates/${encodeURIComponent(glyphKey)}`)).then(asJson<GlyphOut>);

export const postTrace = (sourceId: string, glyphKey: string, body: TraceRequest): Promise<GlyphOut> =>
  apiFetch(src(sourceId, `/templates/${encodeURIComponent(glyphKey)}/trace`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(asJson<GlyphOut>);

// Dry run of /trace: derives the raw and the optimized variant for the
// wizard's before/after comparison — nothing is written.
export const postTracePreview = (
  sourceId: string,
  glyphKey: string,
  body: TraceRequest,
): Promise<TracePreviewOut> =>
  apiFetch(src(sourceId, `/templates/${encodeURIComponent(glyphKey)}/trace-preview`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(asJson<TracePreviewOut>);

// nAnchors omitted => re-derive with the current pipeline code AND its current
// recommended anchor density (server DEFAULT_N_ANCHORS); force overrides the
// server-side lock guard (423 otherwise).
export const postResample = (
  sourceId: string,
  glyphKey: string,
  opts: { nAnchors?: number; force?: boolean } = {},
): Promise<GlyphOut> =>
  apiFetch(src(sourceId, `/templates/${encodeURIComponent(glyphKey)}/resample`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ n_anchors: opts.nAnchors ?? null, force: opts.force ?? false }),
  }).then(asJson<GlyphOut>);

export const getQuality = (sourceId: string, glyphKey: string): Promise<QualityComparison> =>
  apiFetch(src(sourceId, `/templates/${encodeURIComponent(glyphKey)}/quality`)).then(asJson<QualityComparison>);

export const getDiagnostic = (sourceId: string, glyphKey: string): Promise<DiagnosticData> =>
  apiFetch(src(sourceId, `/templates/${encodeURIComponent(glyphKey)}/diagnostic`)).then(asJson<DiagnosticData>);

// Batch render payloads for the public writer (one round trip per word/Tafel).
// Keys are sorted so the same letter set always yields the same URL — the
// response carries Cache-Control, so a stable URL turns repeat visits into
// browser/edge cache hits.
// `variant` selects which stored form is rendered — 0 (the default, and the
// only one the public surfaces ask for) is the authored chart ductus, 100 the
// derived Laufform the admin letter view shows beside it. It is omitted from
// the URL at 0 so the public cache entries keep their existing shape.
export const getWriteGlyphs = (
  sourceId: string,
  keys: string[],
  retry?: RetryOptions,
  variant = 0,
): Promise<WriteGlyphsOut> =>
  apiFetch(
    src(
      sourceId,
      `/write/glyphs?keys=${encodeURIComponent([...keys].sort().join(','))}${variant ? `&variant=${variant}` : ''}`,
    ),
    {},
    retry,
  ).then(asJson<WriteGlyphsOut>);

// A whole word/line composed server-side (shaping + placement + Übergänge in
// core/shaping.py + core/compose.py) — one cacheable request per text. The
// text is NFC-normalised + trimmed HERE (mirroring the server) so semantically
// equal inputs always share one URL and one browser/edge cache entry.
export const getWriteWord = (
  sourceId: string,
  text: string,
  retry?: RetryOptions,
  bust?: number,
): Promise<ComposedWordOut> =>
  apiFetch(
    src(
      sourceId,
      `/write/word?text=${encodeURIComponent(text.normalize('NFC').trim())}${bust ? `&t=${bust}` : ''}`,
    ),
    {},
    retry,
  ).then(asJson<ComposedWordOut>);

export const getFit = (
  sourceId: string,
  glyphKey: string,
  lambdaReg?: number,
  widthWeight?: number,
): Promise<FitData> => {
  const q = new URLSearchParams();
  if (lambdaReg != null) q.set('lambda_reg', String(lambdaReg));
  if (widthWeight != null) q.set('width_weight', String(widthWeight));
  const qs = q.toString();
  return apiFetch(src(sourceId, `/templates/${encodeURIComponent(glyphKey)}/fit${qs ? `?${qs}` : ''}`)).then(
    asJson<FitData>,
  );
};

export const deleteGlyph = (sourceId: string, glyphKey: string): Promise<void> =>
  apiFetch(src(sourceId, `/templates/${encodeURIComponent(glyphKey)}`), { method: 'DELETE' }).then(asJson<void>);
