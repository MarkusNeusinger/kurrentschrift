// One shared render-data cache for every "as written" surface (WrittenWord,
// WrittenGlyph, WrittenSheet). The same glyph rendered by the quiz letter and
// inside a written word must cost ONE request per session, not one per
// component — there used to be three separate module-level caches with
// diverging keys. All misses of one call go out as a single batch
// GET /write/glyphs round trip, with the cold-start retry these fetches never
// had (they carry the entire public writing experience on a min-instances=0
// backend). `null` records "no canonical" — cached, since only an admin write
// changes that, and the write endpoint reports it in `missing` instead of a 404.

import { getWriteGlyphs, getWriteWord } from '@/lib/api/endpoints';
import type { ComposedWordOut, GlyphRenderData } from '@/lib/api/types';

const COLD_START_RETRY = { retries: 3 };

interface Entry {
  // Canonical version stamp the payload was fetched under: a versioned caller
  // (the admin dialog after a re-trace) requires its exact version and forces a
  // refetch on mismatch; versionless callers accept whatever is cached.
  bust: number | null;
  promise: Promise<GlyphRenderData | null>;
  // Resolved value, once settled — lets a component render synchronously on
  // mount instead of flashing a spinner for one microtask.
  settled?: GlyphRenderData | null;
}

const cache = new Map<string, Entry>();
const id = (sourceId: string, key: string) => `${sourceId}|${key}`;

function put(sourceId: string, key: string, bust: number | null, promise: Promise<GlyphRenderData | null>): Entry {
  const entry: Entry = { bust, promise };
  promise
    .then((d) => {
      entry.settled = d;
    })
    .catch(() => {
      // A transient error must not stick — evict so a retry can succeed. Guard
      // against evicting a NEWER entry that already replaced this one.
      if (cache.get(id(sourceId, key)) === entry) cache.delete(id(sourceId, key));
    });
  cache.set(id(sourceId, key), entry);
  return entry;
}

// Synchronous peek: the resolved payload if this glyph already settled under an
// acceptable version, `undefined` while unknown/in flight.
export function peekRenderGlyph(sourceId: string, key: string, bust?: number): GlyphRenderData | null | undefined {
  const entry = cache.get(id(sourceId, key));
  if (!entry || (bust != null && entry.bust !== bust)) return undefined;
  return 'settled' in entry ? entry.settled : undefined;
}

// Fetch (or reuse) one glyph's render payload; resolves to null when no
// canonical exists yet.
export function fetchRenderGlyph(sourceId: string, key: string, bust?: number): Promise<GlyphRenderData | null> {
  const entry = cache.get(id(sourceId, key));
  if (entry && (bust == null || entry.bust === bust)) return entry.promise;
  const promise = getWriteGlyphs(sourceId, [key], COLD_START_RETRY).then(
    (out) => out.glyphs.find((g) => g.glyph_key === key) ?? null,
  );
  return put(sourceId, key, bust ?? null, promise).promise;
}

// Fetch (or reuse) the render payloads for a set of glyph keys — all keys not
// already cached go out as ONE batch request.
export function fetchRenderGlyphs(sourceId: string, keys: string[]): Promise<Map<string, GlyphRenderData | null>> {
  const wanted = [...new Set(keys)];
  const misses = wanted.filter((k) => !cache.has(id(sourceId, k)));
  if (misses.length) {
    const byKey = getWriteGlyphs(sourceId, misses, COLD_START_RETRY).then(
      (out) => new Map(out.glyphs.map((g) => [g.glyph_key, g] as const)),
    );
    for (const k of misses) {
      put(sourceId, k, null, byKey.then((m) => m.get(k) ?? null));
    }
  }
  return Promise.all(wanted.map((k) => cache.get(id(sourceId, k))!.promise.then((d) => [k, d] as const))).then(
    (entries) => new Map(entries),
  );
}

// Record an externally supplied payload (the admin Diagnose dialog shares one
// diagnostic payload across its stages) so every other consumer sees the
// freshest canonical without refetching.
export function seedRenderGlyph(sourceId: string, key: string, data: GlyphRenderData | null, bust?: number): void {
  const entry: Entry = { bust: bust ?? null, promise: Promise.resolve(data), settled: data };
  cache.set(id(sourceId, key), entry);
}

// ── Composed-word cache (GET /write/word) ──────────────────────────────────
// Composing a whole word/line is a backend compute; cache the in-flight/resolved
// promise per (source, text) so a replay, a re-mount or a second WrittenWord on
// the page never refetches. This lives here — with the glyph cache — so the
// "ONE shared render cache" invariant holds (there used to be a private
// module-level cache inside WrittenWord with its own key scheme). Transient
// errors evict so a retry can succeed; the server also sets Cache-Control, so
// even a fresh page load hits the browser cache. Live typing on /federprobe
// produces many distinct intermediate texts, so the cache is FIFO-capped —
// evicted entries just refetch (usually straight from the browser cache).
const WORD_CACHE_MAX = 64;
const wordCache = new Map<string, Promise<ComposedWordOut>>();

// Drop one composed word so the next fetch recomposes it — an approved pair
// override changes what /write/word returns for exactly this text, and a
// surface that just saved one must not keep showing the pre-override join.
export function invalidateRenderWord(sourceId: string, text: string): void {
  wordCache.delete(id(sourceId, text));
}

export function fetchRenderWord(sourceId: string, text: string): Promise<ComposedWordOut> {
  const key = id(sourceId, text);
  let p = wordCache.get(key);
  if (!p) {
    p = getWriteWord(sourceId, text, COLD_START_RETRY).catch((e) => {
      // Identity guard (same as the glyph cache): after a FIFO eviction and
      // re-fetch under the same key, the OLD promise's late rejection must not
      // delete the new, valid entry.
      if (wordCache.get(key) === p) wordCache.delete(key);
      throw e;
    });
    if (wordCache.size >= WORD_CACHE_MAX) {
      wordCache.delete(wordCache.keys().next().value as string); // FIFO: drop the oldest entry
    }
    wordCache.set(key, p);
  }
  return p;
}
