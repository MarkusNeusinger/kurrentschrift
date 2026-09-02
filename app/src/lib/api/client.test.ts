// Unit tests for `apiFetch`'s per-attempt deadline and how it feeds the
// cold-start retry. The gap this closes: before the timeout, a request that
// simply never answered — stalled TCP, a Cloud Run boot past a minute, an edge
// holding the connection — threw nothing and returned nothing, so neither the
// 502/503/504 branch nor the `catch` fired and the spinner spun forever.
//
// Two clocks on purpose. `AbortSignal.timeout` is native and is NOT faked by
// `vi.useFakeTimers()` (verified against this vitest), so the tests that prove
// the signal really aborts a hanging request run on the real clock with a
// millisecond deadline; the retry/backoff tests, which only need the abort's
// SHAPE, hand the client a `TimeoutError` directly and drive `wait()` on the
// fake clock.

import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from 'vitest';

import { ApiError, apiFetch } from '@/lib/api/client';

/** What `AbortSignal.timeout` throws once the deadline passes. */
const timeoutError = (): Error => {
  const err = new Error('signal timed out');
  err.name = 'TimeoutError';
  return err;
};

/** A fetch that never answers but honours its signal — a real one does too. */
const hangingFetch = (): Mock =>
  vi.fn(
    (_input: string, init: RequestInit) =>
      new Promise<Response>((_resolve, reject) => {
        init.signal?.addEventListener('abort', () => reject(init.signal?.reason));
      }),
  );

describe('apiFetch', () => {
  let fetchMock: Mock;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('gives up on a request that never answers', async () => {
    fetchMock.mockImplementation(hangingFetch());

    await expect(apiFetch('/api/styles', {}, { retries: 0, timeoutMs: 20 })).rejects.toThrow(ApiError);
    // 408 rather than the raw `TimeoutError: signal timed out`: the error
    // surfaces render `String(err)`, and a caller can branch on `.status`.
    await expect(apiFetch('/api/styles', {}, { retries: 0, timeoutMs: 20 })).rejects.toMatchObject({ status: 408 });
  });

  it('passes a fresh signal on every attempt', async () => {
    // A retry that inherited the first attempt's signal would be aborted
    // before it ever started.
    fetchMock.mockImplementation(hangingFetch());

    await expect(apiFetch('/api/styles', {}, { retries: 1, timeoutMs: 5 })).rejects.toMatchObject({ status: 408 });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    const [first, second] = fetchMock.mock.calls.map((call) => call[1].signal as AbortSignal);
    expect(first).toBeInstanceOf(AbortSignal);
    expect(second).not.toBe(first);
  }, 20_000);

  it('uses 20 s by default and 30 s for the composed word', async () => {
    const spy = vi.spyOn(AbortSignal, 'timeout');
    fetchMock.mockResolvedValue(new Response('{}', { status: 200 }));

    await apiFetch('/api/styles');
    await apiFetch('/api/sources/suetterlin-1922/write/glyphs?keys=n');
    await apiFetch('/api/sources/suetterlin-1922/write/word?text=lesen');
    await apiFetch('/api/styles', {}, { retries: 0, timeoutMs: 1234 });

    expect(spy.mock.calls.map(([ms]) => ms)).toEqual([20_000, 20_000, 30_000, 1234]);
  });

  it('treats a timeout like a network error for the retry logic', async () => {
    vi.useFakeTimers();
    const onRetry = vi.fn();
    fetchMock
      .mockRejectedValueOnce(timeoutError())
      .mockRejectedValueOnce(new TypeError('Failed to fetch'))
      .mockResolvedValueOnce(new Response('[]', { status: 200 }));

    const pending = apiFetch('/api/styles', {}, { retries: 2, onRetry });
    await vi.advanceTimersByTimeAsync(5_000); // covers the 1 s + 2 s backoff

    await expect(pending).resolves.toMatchObject({ status: 200 });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    // Same backoff for both, and the caller hears about both — that is what
    // drives the "API startet…" line.
    expect(onRetry.mock.calls).toEqual([
      [1, 1000],
      [2, 2000],
    ]);
  });

  it('still retries a cold-start status and keeps the last response', async () => {
    vi.useFakeTimers();
    fetchMock
      .mockResolvedValueOnce(new Response(null, { status: 503 }))
      .mockResolvedValueOnce(new Response('[]', { status: 200 }));

    const pending = apiFetch('/api/styles', {}, { retries: 1 });
    await vi.advanceTimersByTimeAsync(2_000);

    await expect(pending).resolves.toMatchObject({ status: 200 });
  });

  it('keeps a caller-supplied signal alongside the deadline', async () => {
    fetchMock.mockImplementation(hangingFetch());
    const controller = new AbortController();

    const pending = apiFetch('/api/styles', { signal: controller.signal }, { retries: 0, timeoutMs: 10_000 });
    controller.abort(new Error('the view unmounted'));

    // The caller's reason, not a 408: the deadline did not fire.
    await expect(pending).rejects.toThrow('the view unmounted');
  });
});
