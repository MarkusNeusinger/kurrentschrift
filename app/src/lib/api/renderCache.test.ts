// Unit tests for the shared render-data cache: batching, in-flight dedupe,
// cache hits, null ("no canonical") caching, error eviction and the cold-start
// retry. `fetch` is stubbed globally; the module is re-imported per test so the
// module-level caches start empty every time.

import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from 'vitest';

import type { ComposedWordOut, GlyphRenderData, WriteGlyphsOut } from '@/lib/api/types';

type RenderCacheModule = typeof import('@/lib/api/renderCache');

const glyph = (key: string): GlyphRenderData => ({
  glyph_key: key,
  anchors_template: [
    [0, 0],
    [0.2, 0.6],
  ],
  half_widths_template: [0.05, 0.05],
  template_guides: { baseline: 0, midband: 1, ascender: 2, descender: -1 },
});

const glyphsOut = (glyphs: GlyphRenderData[], missing: string[] = []): WriteGlyphsOut => ({ glyphs, missing });

const word = (text: string): ComposedWordOut => ({
  text,
  items: [],
  bounds: { min_x: 0, max_x: 1, min_y: 0, max_y: 1 },
  guides: null,
  missing: [],
});

const jsonRes = (body: unknown, status = 200): Response =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

describe('renderCache', () => {
  let fetchMock: Mock;
  let rc: RenderCacheModule;

  beforeEach(async () => {
    vi.resetModules();
    fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    rc = await import('@/lib/api/renderCache');
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  const requestedUrl = (call = 0): string => decodeURIComponent(String(fetchMock.mock.calls[call][0]));

  it('batches all misses of one call into a single /write/glyphs request', async () => {
    fetchMock.mockResolvedValueOnce(jsonRes(glyphsOut([glyph('a-medial'), glyph('b-medial')])));

    const map = await rc.fetchRenderGlyphs('src', ['b-medial', 'a-medial', 'b-medial']);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(requestedUrl()).toContain('/sources/src/write/glyphs');
    // Deduped and sorted into one stable batch URL.
    expect(requestedUrl()).toContain('keys=a-medial,b-medial');
    expect(map.get('a-medial')).toMatchObject({ glyph_key: 'a-medial' });
    expect(map.get('b-medial')).toMatchObject({ glyph_key: 'b-medial' });
  });

  it('only fetches the keys not already cached', async () => {
    fetchMock.mockResolvedValueOnce(jsonRes(glyphsOut([glyph('a-medial')])));
    await rc.fetchRenderGlyphs('src', ['a-medial']);

    fetchMock.mockResolvedValueOnce(jsonRes(glyphsOut([glyph('b-medial')])));
    const map = await rc.fetchRenderGlyphs('src', ['a-medial', 'b-medial']);

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(requestedUrl(1)).toContain('keys=b-medial');
    expect(requestedUrl(1)).not.toContain('a-medial');
    expect(map.get('a-medial')).toMatchObject({ glyph_key: 'a-medial' });
  });

  it('dedupes parallel requests for the same glyph into one fetch', async () => {
    let resolveFetch!: (value: Response) => void;
    fetchMock.mockReturnValueOnce(
      new Promise<Response>((resolve) => {
        resolveFetch = resolve;
      }),
    );

    const p1 = rc.fetchRenderGlyph('src', 'a-medial');
    const p2 = rc.fetchRenderGlyph('src', 'a-medial');
    expect(fetchMock).toHaveBeenCalledTimes(1);

    resolveFetch(jsonRes(glyphsOut([glyph('a-medial')])));
    const [d1, d2] = await Promise.all([p1, p2]);
    expect(d1).toMatchObject({ glyph_key: 'a-medial' });
    expect(d2).toEqual(d1);
  });

  it('serves repeat requests from the cache without a second fetch', async () => {
    fetchMock.mockResolvedValueOnce(jsonRes(glyphsOut([glyph('a-medial')])));
    await rc.fetchRenderGlyph('src', 'a-medial');

    const again = await rc.fetchRenderGlyph('src', 'a-medial');
    const viaBatch = await rc.fetchRenderGlyphs('src', ['a-medial']);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(again).toMatchObject({ glyph_key: 'a-medial' });
    expect(viaBatch.get('a-medial')).toEqual(again);
    expect(rc.peekRenderGlyph('src', 'a-medial')).toEqual(again);
  });

  it('caches "no canonical" (missing key) as null instead of refetching', async () => {
    fetchMock.mockResolvedValueOnce(jsonRes(glyphsOut([], ['a-medial'])));

    const map = await rc.fetchRenderGlyphs('src', ['a-medial']);
    expect(map.get('a-medial')).toBeNull();

    await expect(rc.fetchRenderGlyph('src', 'a-medial')).resolves.toBeNull();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('a version bust forces a refetch past the cached entry', async () => {
    // Fresh Response per call — a body can only be consumed once.
    fetchMock.mockImplementation(() => Promise.resolve(jsonRes(glyphsOut([glyph('a-medial')]))));
    await rc.fetchRenderGlyph('src', 'a-medial');

    await rc.fetchRenderGlyph('src', 'a-medial', 2);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    // The busted entry is cached under its version — same version hits again.
    await rc.fetchRenderGlyph('src', 'a-medial', 2);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('evicts a failed entry so a later request can retry', async () => {
    // A 5xx outside the cold-start set (500) fails without internal retries.
    fetchMock.mockResolvedValueOnce(jsonRes({ detail: 'boom' }, 500));
    await expect(rc.fetchRenderGlyph('src', 'a-medial')).rejects.toMatchObject({ status: 500 });

    fetchMock.mockResolvedValueOnce(jsonRes(glyphsOut([glyph('a-medial')])));
    await expect(rc.fetchRenderGlyph('src', 'a-medial')).resolves.toMatchObject({ glyph_key: 'a-medial' });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('rides out a cold start: 503 then success on the retry', async () => {
    vi.useFakeTimers();
    fetchMock
      .mockResolvedValueOnce(new Response(null, { status: 503 }))
      .mockResolvedValueOnce(jsonRes(glyphsOut([glyph('a-medial')])));

    const p = rc.fetchRenderGlyph('src', 'a-medial');
    await vi.advanceTimersByTimeAsync(1000); // first backoff step
    await expect(p).resolves.toMatchObject({ glyph_key: 'a-medial' });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('dedupes and caches composed words per (source, text)', async () => {
    fetchMock.mockResolvedValueOnce(jsonRes(word('nn')));

    const p1 = rc.fetchRenderWord('src', 'nn');
    const p2 = rc.fetchRenderWord('src', 'nn');
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await expect(p1).resolves.toMatchObject({ text: 'nn' });
    await expect(p2).resolves.toMatchObject({ text: 'nn' });

    await rc.fetchRenderWord('src', 'nn');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('evicts a failed word so a later request can retry', async () => {
    fetchMock.mockResolvedValueOnce(jsonRes({ detail: 'boom' }, 500));
    await expect(rc.fetchRenderWord('src', 'nn')).rejects.toMatchObject({ status: 500 });

    fetchMock.mockResolvedValueOnce(jsonRes(word('nn')));
    await expect(rc.fetchRenderWord('src', 'nn')).resolves.toMatchObject({ text: 'nn' });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
