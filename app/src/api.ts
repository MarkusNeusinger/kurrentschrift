// Thin fetch wrappers over the FastAPI backend. All paths embed `SOURCE_ID`
// (the v1 hardcode). Vite's dev proxy (vite.config.ts) forwards `/api/*` to
// :8000; in production the Cloudflare Worker on kurrentschrift.ink/api/* does
// the same thing so the CF Access cookie set on kurrentschrift.ink (host-only)
// is forwarded with the request — that's what gates the admin write
// endpoints. `credentials: 'include'` is set on every call so the cookie
// always travels.

import { SOURCE_ID } from './constants';
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
} from './types';

const API = '/api';

// Local-dev write auth: in production the admin write endpoints are gated by the
// Cloudflare Access cookie (forwarded by the CF Worker), so the browser sends
// nothing extra. For local dev there is no CF Access, so set VITE_ADMIN_TOKEN in
// app/.env (matching the API's ADMIN_TOKEN) and it's sent as X-Admin-Token. Unset
// in prod builds → no header, cookie-based auth as before.
const ADMIN_TOKEN = import.meta.env.VITE_ADMIN_TOKEN as string | undefined;

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

// Cloud Run scales the API to zero. The first request after an idle period can
// fail with a network error (`TypeError: Failed to fetch`) or a 502/503/504
// from the load balancer while the container cold-starts. Without this, the
// admin UI dropped straight to "API nicht erreichbar" and only recovered on a
// manual reload. Retry idempotent reads with exponential backoff so the UI
// rides out the cold start instead.
const COLD_START_STATUS = new Set([502, 503, 504]);

export interface RetryOptions {
  // How many extra attempts after the first (0 = no retry).
  retries: number;
  // Called before each wait so callers can surface "API startet…" feedback.
  onRetry?: (attempt: number, waitMs: number) => void;
}

const backoffMs = (attempt: number): number => Math.min(1000 * 2 ** attempt, 8000);

const wait = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

function apiFetch(input: string, init: RequestInit = {}, retry?: RetryOptions): Promise<Response> {
  const retries = retry?.retries ?? 0;
  const attemptFetch = async (attempt: number): Promise<Response> => {
    try {
      const headers = { ...(init.headers as Record<string, string> | undefined), ...(ADMIN_TOKEN ? { 'X-Admin-Token': ADMIN_TOKEN } : {}) };
      const res = await fetch(input, { credentials: 'include', ...init, headers });
      if (COLD_START_STATUS.has(res.status) && attempt < retries) {
        // Release the connection before backing off — we won't read this body.
        await res.body?.cancel().catch(() => {});
        const ms = backoffMs(attempt);
        retry?.onRetry?.(attempt + 1, ms);
        await wait(ms);
        return attemptFetch(attempt + 1);
      }
      return res;
    } catch (err) {
      // Network-level failure (cold start / transient): retry, otherwise rethrow.
      if (attempt < retries) {
        const ms = backoffMs(attempt);
        retry?.onRetry?.(attempt + 1, ms);
        await wait(ms);
        return attemptFetch(attempt + 1);
      }
      throw err;
    }
  };
  return attemptFetch(0);
}

const src = (path: string) => `${API}/sources/${SOURCE_ID}${path}`;

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
