import { describe, expect, it } from 'vitest';

import { latestRequestGate } from './latestRequest';

describe('latestRequestGate', () => {
  it('lets a lone request write', () => {
    const begin = latestRequestGate();
    expect(begin()()).toBe(true);
  });

  it('silences an older request once a newer one has begun', () => {
    const begin = latestRequestGate();
    const first = begin();
    const second = begin();
    expect(first()).toBe(false);
    expect(second()).toBe(true);
  });

  it('keeps the newest one valid however late the older ones resolve', async () => {
    // The case this exists for: a hand switch while the previous Bestand is
    // still in flight. The SLOW response is the older one, so it must not win
    // by arriving last.
    const begin = latestRequestGate();
    const written: string[] = [];
    const load = (label: string, ms: number) => {
      const isCurrent = begin();
      return new Promise<void>((resolve) =>
        setTimeout(() => {
          if (isCurrent()) written.push(label);
          resolve();
        }, ms),
      );
    };
    const slowOld = load('hand-A', 30);
    const fastNew = load('hand-B', 1);
    await Promise.all([slowOld, fastNew]);
    expect(written).toEqual(['hand-B']);
  });

  it('gives every panel its own counter', () => {
    const a = latestRequestGate();
    const b = latestRequestGate();
    const aFirst = a();
    b();
    b();
    expect(aFirst()).toBe(true);
  });
});
