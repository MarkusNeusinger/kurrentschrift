// Thin endpoint wrappers over the FastAPI backend. All paths embed the v1
// source hardcode from CONFIG.sourceId.

import { CONFIG } from '@/global-config';
import { apiFetch, asJson, type RetryOptions } from '@/lib/api/client';
import type {
  BboxIn,
  BboxOut,
  DiagnosticData,
  FitData,
  GlyphOut,
  GlyphSummary,
  SourceOut,
  StyleOut,
  TraceRequest,
} from '@/lib/api/types';

const API = CONFIG.apiBase;

const src = (path: string) => `${API}/sources/${CONFIG.sourceId}${path}`;

export const getStyles = (retry?: RetryOptions): Promise<StyleOut[]> =>
  apiFetch(`${API}/styles`, {}, retry).then(asJson<StyleOut[]>);

export const getSource = (retry?: RetryOptions): Promise<SourceOut> =>
  apiFetch(src(''), {}, retry).then(asJson<SourceOut>);

export const chartUrl = (): string => src('/chart');
export const cropUrl = (glyphKey: string, cacheBust?: number): string =>
  src(`/bboxes/${encodeURIComponent(glyphKey)}/crop${cacheBust ? `?t=${cacheBust}` : ''}`);

export const getBboxes = (retry?: RetryOptions): Promise<BboxOut[]> =>
  apiFetch(src('/bboxes'), {}, retry).then(asJson<BboxOut[]>);

export const putBbox = (glyphKey: string, bbox: BboxIn): Promise<BboxOut> =>
  apiFetch(src(`/bboxes/${encodeURIComponent(glyphKey)}`), {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(bbox),
  }).then(asJson<BboxOut>);

export const deleteBbox = (glyphKey: string): Promise<void> =>
  apiFetch(src(`/bboxes/${encodeURIComponent(glyphKey)}`), { method: 'DELETE' }).then(asJson<void>);

export const getGlyphs = (retry?: RetryOptions): Promise<GlyphSummary[]> =>
  apiFetch(src('/templates'), {}, retry).then(asJson<GlyphSummary[]>);

export const getGlyph = (glyphKey: string): Promise<GlyphOut> =>
  apiFetch(src(`/templates/${encodeURIComponent(glyphKey)}`)).then(asJson<GlyphOut>);

export const postTrace = (glyphKey: string, body: TraceRequest): Promise<GlyphOut> =>
  apiFetch(src(`/templates/${encodeURIComponent(glyphKey)}/trace`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(asJson<GlyphOut>);

export const postResample = (glyphKey: string, nAnchors: number): Promise<GlyphOut> =>
  apiFetch(src(`/templates/${encodeURIComponent(glyphKey)}/resample`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ n_anchors: nAnchors }),
  }).then(asJson<GlyphOut>);

export const getDiagnostic = (glyphKey: string): Promise<DiagnosticData> =>
  apiFetch(src(`/templates/${encodeURIComponent(glyphKey)}/diagnostic`)).then(asJson<DiagnosticData>);

export const getFit = (glyphKey: string, lambdaReg?: number, widthWeight?: number): Promise<FitData> => {
  const q = new URLSearchParams();
  if (lambdaReg != null) q.set('lambda_reg', String(lambdaReg));
  if (widthWeight != null) q.set('width_weight', String(widthWeight));
  const qs = q.toString();
  return apiFetch(src(`/templates/${encodeURIComponent(glyphKey)}/fit${qs ? `?${qs}` : ''}`)).then(asJson<FitData>);
};

export const deleteGlyph = (glyphKey: string): Promise<void> =>
  apiFetch(src(`/templates/${encodeURIComponent(glyphKey)}`), { method: 'DELETE' }).then(asJson<void>);
