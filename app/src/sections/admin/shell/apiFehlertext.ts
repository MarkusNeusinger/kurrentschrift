// The German error layer for the workbench: an HTTP failure turned into one
// sentence the author can act on, with the raw English line kept beside it.
//
// Every admin surface used to render `String(err)` — literally
// "Error: 423 Locked: glyph 'longs' is locked; pass force=true to overwrite" —
// which says nothing about what to DO and reads as an internals leak on the one
// page that is entirely in German. But the raw line is also the only diagnostic
// the author has when something unexpected happens, so it is never dropped: the
// sentence is the answer, the detail is the evidence, and `FehlerText` renders
// the detail inside a collapsed <details>.
//
// It lives HERE and not beside the client in `lib/api/` because it reads the
// admin message catalog, and `no-restricted-imports` keeps those ~66 kB out of
// anything the public bundle can reach. It is a layer over the client, not part
// of it: `lib/api` stays language-free and shared, this is the workbench's own
// reading of what the client throws.

import { ApiError } from '@/lib/api/client';
import { de } from '@/locales/admin';

export interface ApiFehler {
  // The HTTP status, or null when the call never reached a response (offline,
  // DNS, a cold start that outlasted the retries). Call sites that branch on a
  // specific case — a 404 that means "not authored yet", not "broken" — read
  // this instead of sniffing the message for "404".
  status: number | null;
  // The German sentence: what happened and what to do about it.
  satz: string;
  // The raw line as the server (or the browser) phrased it, unchanged.
  detail: string;
}

// Status → sentence. Only the statuses this API actually raises get their own
// wording; everything else falls back to the class (4xx = the request, 5xx =
// the server), so a status added later is still explained, just less sharply.
function satzFor(status: number | null): string {
  const t = de.admin.fehler;
  switch (status) {
    case null:
      return t.offline;
    case 400:
      return t.badRequest;
    case 401:
    case 403:
      return t.noAdmin;
    case 404:
      return t.notFound;
    case 409:
      return t.conflict;
    case 413:
      return t.tooLarge;
    case 422:
      return t.invalid;
    case 423:
      return t.locked;
    case 429:
      return t.tooMany;
    default:
      return status >= 500 ? t.server : t.badRequest;
  }
}

export function apiFehlertext(err: unknown): ApiFehler {
  const status = err instanceof ApiError ? err.status : null;
  return { status, satz: satzFor(status), detail: String(err) };
}
