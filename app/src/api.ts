// Thin fetch wrappers over the FastAPI backend. All paths are prefixed
// with /api/ — Vite's dev proxy (vite.config.ts) forwards to :8000.

import type { BboxesResponse, Canonical, GlyphBbox, TraceRequest } from './types';

const API = '/api';

async function asJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = `${detail}: ${body.detail}`;
    } catch {
      /* not JSON */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const chartUrl = (): string => `${API}/chart`;
export const cropUrl = (glyphKey: string, cacheBust?: number): string =>
  `${API}/chart/crop/${encodeURIComponent(glyphKey)}${cacheBust ? `?t=${cacheBust}` : ''}`;

export const getBboxes = (): Promise<BboxesResponse> => fetch(`${API}/bboxes`).then(asJson<BboxesResponse>);

export const putBbox = (glyphKey: string, bbox: GlyphBbox): Promise<GlyphBbox> =>
  fetch(`${API}/bboxes/${encodeURIComponent(glyphKey)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(bbox),
  }).then(asJson<GlyphBbox>);

export const getCanonical = (glyphKey: string): Promise<Canonical | null> =>
  fetch(`${API}/canonical/${encodeURIComponent(glyphKey)}`).then(asJson<Canonical | null>);

export const postTrace = (glyphKey: string, body: TraceRequest): Promise<Canonical> =>
  fetch(`${API}/canonical/${encodeURIComponent(glyphKey)}/trace`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(asJson<Canonical>);
