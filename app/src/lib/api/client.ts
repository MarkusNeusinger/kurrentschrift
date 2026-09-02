// HTTP client for the FastAPI backend: same-origin fetch with the CF-Access
// cookie (prod) or X-Admin-Token header (local dev), a per-attempt timeout,
// cold-start retry, and a typed ApiError so callers can branch on status
// instead of string-sniffing.
//
// The Vite dev proxy (vite.config.ts) forwards `/api/*` to :8000; in production
// the Cloudflare Worker on kurrentschrift.ink/api/* does the same so the CF
// Access cookie set on kurrentschrift.ink (host-only) travels with the request —
// that's what gates the admin write endpoints. `credentials: 'include'` is set
// on every call so the cookie always travels.

import { CONFIG } from '@/global-config';

// Typed HTTP error. `name` stays the default "Error" on purpose: every snack/
// error surface renders `String(err)` and must keep reading
// "Error: 404 Not Found: …" exactly as before.
export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function asJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = `${detail}: ${typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)}`;
    } catch {
      /* not JSON */
    }
    throw new ApiError(res.status, detail);
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

// …but a cold start can also just go quiet: a stalled TCP connection, a Cloud
// Run boot past a minute, an edge holding the connection open. Then no status
// arrives and no `TypeError` is thrown, so neither branch above fires — the
// spinner in BootStatus or WrittenWord spun forever and the retry button never
// appeared (audit 2026-09-02: zero AbortController/AbortSignal hits in app/).
// Every attempt therefore gets its own deadline.
const DEFAULT_TIMEOUT_MS = 20_000;

// …except the one route that composes server-side. A long line is real work
// (measured 0.80 s at 155 characters, and that is on a warm instance), and a
// cold start rides on top of it.
const COMPOSE_TIMEOUT_MS = 30_000;

const defaultTimeoutFor = (input: string): number =>
  input.includes('/write/word') ? COMPOSE_TIMEOUT_MS : DEFAULT_TIMEOUT_MS;

// A DOMException from AbortSignal.timeout — the name is what identifies it;
// `instanceof DOMException` is not reliable across every runtime the tests run in.
const isTimeout = (err: unknown): boolean => (err as { name?: string })?.name === 'TimeoutError';

export interface RetryOptions {
  // How many extra attempts after the first (0 = no retry).
  retries: number;
  // Called before each wait so callers can surface "API startet…" feedback.
  onRetry?: (attempt: number, waitMs: number) => void;
  // Deadline PER ATTEMPT, not for the whole call. Defaults to 20 s, or 30 s
  // for /write/word.
  timeoutMs?: number;
}

const backoffMs = (attempt: number): number => Math.min(1000 * 2 ** attempt, 8000);

const wait = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

export function apiFetch(input: string, init: RequestInit = {}, retry?: RetryOptions): Promise<Response> {
  const retries = retry?.retries ?? 0;
  const timeoutMs = retry?.timeoutMs ?? defaultTimeoutFor(input);
  const attemptFetch = async (attempt: number): Promise<Response> => {
    try {
      const headers = {
        ...(init.headers as Record<string, string> | undefined),
        ...(CONFIG.adminToken ? { 'X-Admin-Token': CONFIG.adminToken } : {}),
      };
      // A fresh deadline per attempt — a retry that inherited the first
      // attempt's signal would be aborted before it started. A caller-supplied
      // signal is kept alongside rather than overwritten by the spread below.
      const deadline = AbortSignal.timeout(timeoutMs);
      const signal = init.signal ? AbortSignal.any([init.signal, deadline]) : deadline;
      const res = await fetch(input, { credentials: 'include', ...init, headers, signal });
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
      // Network-level failure or our own deadline (cold start / transient):
      // a timeout counts exactly like a dropped connection, so it retries on
      // the same backoff.
      if (attempt < retries) {
        const ms = backoffMs(attempt);
        retry?.onRetry?.(attempt + 1, ms);
        await wait(ms);
        return attemptFetch(attempt + 1);
      }
      // Out of attempts. A raw `TimeoutError: signal timed out` would reach
      // the error surfaces (which render `String(err)`) as noise; 408 says the
      // same thing in the shape every other failure already has, and lets a
      // caller branch on `.status` like it does on 404.
      if (isTimeout(err)) {
        throw new ApiError(408, `408 Request Timeout: the API did not answer within ${timeoutMs / 1000} s`);
      }
      throw err;
    }
  };
  return attemptFetch(0);
}
