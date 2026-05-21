// Thin fetch wrappers over the FastAPI backend. All paths embed `SOURCE_ID`
// (the v1 hardcode). Vite's dev proxy (vite.config.ts) forwards `/api/*` to
// :8000.

import { SOURCE_ID } from './constants';
import type {
  BboxIn,
  BboxOut,
  DiagnosticData,
  GlyphOut,
  GlyphSummary,
  SourceOut,
  TraceRequest,
} from './types';

const API = '/api';

async function asJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = `${detail}: ${typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)}`;
    } catch {
      /* not JSON */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

const src = (path: string) => `${API}/sources/${SOURCE_ID}${path}`;

export const getSource = (): Promise<SourceOut> => fetch(src('')).then(asJson<SourceOut>);

export const chartUrl = (): string => src('/chart');
export const cropUrl = (glyphKey: string, cacheBust?: number): string =>
  src(`/bboxes/${encodeURIComponent(glyphKey)}/crop${cacheBust ? `?t=${cacheBust}` : ''}`);

export const getBboxes = (): Promise<BboxOut[]> => fetch(src('/bboxes')).then(asJson<BboxOut[]>);

export const putBbox = (glyphKey: string, bbox: BboxIn): Promise<BboxOut> =>
  fetch(src(`/bboxes/${encodeURIComponent(glyphKey)}`), {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(bbox),
  }).then(asJson<BboxOut>);

export const deleteBbox = (glyphKey: string): Promise<void> =>
  fetch(src(`/bboxes/${encodeURIComponent(glyphKey)}`), { method: 'DELETE' }).then(asJson<void>);

export const getGlyphs = (): Promise<GlyphSummary[]> => fetch(src('/glyphs')).then(asJson<GlyphSummary[]>);

export const getGlyph = (glyphKey: string): Promise<GlyphOut> =>
  fetch(src(`/glyphs/${encodeURIComponent(glyphKey)}`)).then(asJson<GlyphOut>);

export const postTrace = (glyphKey: string, body: TraceRequest): Promise<GlyphOut> =>
  fetch(src(`/glyphs/${encodeURIComponent(glyphKey)}/trace`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(asJson<GlyphOut>);

export const postResample = (glyphKey: string, nAnchors: number): Promise<GlyphOut> =>
  fetch(src(`/glyphs/${encodeURIComponent(glyphKey)}/resample`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ n_anchors: nAnchors }),
  }).then(asJson<GlyphOut>);

export const getDiagnostic = (glyphKey: string): Promise<DiagnosticData> =>
  fetch(src(`/glyphs/${encodeURIComponent(glyphKey)}/diagnostic`)).then(asJson<DiagnosticData>);

export const deleteGlyph = (glyphKey: string): Promise<void> =>
  fetch(src(`/glyphs/${encodeURIComponent(glyphKey)}`), { method: 'DELETE' }).then(asJson<void>);
