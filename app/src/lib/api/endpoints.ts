// Thin endpoint wrappers over the FastAPI backend. Every source-scoped path
// takes the source id explicitly: the public pages stay pinned to the
// site-wide CONFIG.sourceId, while the admin passes its runtime-switchable
// active source (see AdminContext) — a hidden global here would let the
// admin's selection leak into the public surfaces.

import { CONFIG } from '@/global-config';
import { apiFetch, asJson, type RetryOptions } from '@/lib/api/client';
import type {
  BboxIn,
  BboxOut,
  DiagnosticData,
  FitData,
  GlyphOut,
  GlyphSummary,
  QualityComparison,
  SourceOut,
  StyleOut,
  TracePreviewOut,
  TraceRequest,
} from '@/lib/api/types';

const API = CONFIG.apiBase;

const src = (sourceId: string, path: string) => `${API}/sources/${encodeURIComponent(sourceId)}${path}`;

export const getStyles = (retry?: RetryOptions): Promise<StyleOut[]> =>
  apiFetch(`${API}/styles`, {}, retry).then(asJson<StyleOut[]>);

export const getSources = (retry?: RetryOptions): Promise<SourceOut[]> =>
  apiFetch(`${API}/sources`, {}, retry).then(asJson<SourceOut[]>);

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

export const getBboxes = (sourceId: string, retry?: RetryOptions): Promise<BboxOut[]> =>
  apiFetch(src(sourceId, '/bboxes'), {}, retry).then(asJson<BboxOut[]>);

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
