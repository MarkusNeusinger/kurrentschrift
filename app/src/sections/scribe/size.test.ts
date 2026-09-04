import { afterEach, describe, expect, it, vi } from 'vitest';

import { MIN_XHEIGHT_PX } from '@/lib/lineWrap';
import {
  DEFAULT_SCRIBE_SIZE,
  SCRIBE_SIZE_PX,
  SCRIBE_SIZE_STORAGE_KEY,
  initialScribeSize,
  parseScribeSize,
  readStoredScribeSize,
  storeScribeSize,
  type ScribeSize,
} from './size';

/** A working store, since these tests run without a DOM (the suite has no
 * jsdom): the module reaches storage through `globalThis`, which is exactly
 * what makes it stubbable here and safe outside a browser. */
function fakeStorage(): Storage {
  const map = new Map<string, string>();
  return {
    getItem: (k: string) => map.get(k) ?? null,
    setItem: (k: string, v: string) => void map.set(k, v),
    removeItem: (k: string) => void map.delete(k),
    clear: () => map.clear(),
    key: (i: number) => [...map.keys()][i] ?? null,
    get length() {
      return map.size;
    },
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('the size ladder', () => {
  it('rises in √2 steps above the Tintenboden', () => {
    expect(SCRIBE_SIZE_PX).toEqual({ klein: 20, mittel: 28, gross: 40 });
    // Every step clears the floor, and `mittel` is exactly twice it.
    for (const px of Object.values(SCRIBE_SIZE_PX)) expect(px).toBeGreaterThan(MIN_XHEIGHT_PX);
    expect(SCRIBE_SIZE_PX.mittel).toBe(2 * MIN_XHEIGHT_PX);
  });

  it('defaults to the middle step, and it is larger than the page wrote before', () => {
    expect(DEFAULT_SCRIBE_SIZE).toBe('mittel');
    // 20.8 px per unit is what a full desktop line measured on 2026-09-04,
    // before the control existed; `mittel` has to be visibly above it.
    expect(SCRIBE_SIZE_PX[DEFAULT_SCRIBE_SIZE]).toBeGreaterThan(20.8);
  });

  it('grows strictly from step to step', () => {
    const px = (['klein', 'mittel', 'gross'] as ScribeSize[]).map((s) => SCRIBE_SIZE_PX[s]);
    expect(px).toEqual([...px].sort((a, b) => a - b));
    expect(new Set(px).size).toBe(px.length);
  });
});

describe('parseScribeSize', () => {
  it('accepts the three step names and nothing else', () => {
    expect(parseScribeSize('klein')).toBe('klein');
    expect(parseScribeSize('gross')).toBe('gross');
    for (const junk of ['groß', 'GROSS', 'riesig', '', null, undefined, 'toString'])
      expect(parseScribeSize(junk)).toBeNull();
  });
});

describe('initialScribeSize', () => {
  it('lets the link win, so a shared look is the sender’s look', () => {
    expect(initialScribeSize('gross', 'klein')).toBe('gross');
  });

  it('falls back to the remembered choice when the link says nothing', () => {
    expect(initialScribeSize(null, 'klein')).toBe('klein');
    expect(initialScribeSize('', 'klein')).toBe('klein');
  });

  it('ignores a link value that names no step rather than resetting the reader', () => {
    expect(initialScribeSize('riesig', 'klein')).toBe('klein');
  });

  it('is the default when neither says anything', () => {
    expect(initialScribeSize(null, null)).toBe(DEFAULT_SCRIBE_SIZE);
    expect(initialScribeSize('riesig', 'winzig')).toBe(DEFAULT_SCRIBE_SIZE);
  });
});

describe('the remembered choice', () => {
  it('round-trips through localStorage', () => {
    const store = fakeStorage();
    vi.stubGlobal('localStorage', store);
    storeScribeSize('gross');
    expect(store.getItem(SCRIBE_SIZE_STORAGE_KEY)).toBe('gross');
    expect(readStoredScribeSize()).toBe('gross');
  });

  it('reads nothing back from a store that holds junk', () => {
    const store = fakeStorage();
    store.setItem(SCRIBE_SIZE_STORAGE_KEY, 'riesig');
    vi.stubGlobal('localStorage', store);
    expect(readStoredScribeSize()).toBeNull();
  });

  it('survives a browser that refuses storage outright', () => {
    // Private mode and "block site data" throw on ACCESS, not on the call, so
    // the page has to render correctly with no stored value at all.
    vi.stubGlobal('localStorage', {
      get getItem(): never {
        throw new Error('SecurityError');
      },
      get setItem(): never {
        throw new Error('SecurityError');
      },
    });
    expect(readStoredScribeSize()).toBeNull();
    expect(() => storeScribeSize('klein')).not.toThrow();
    expect(initialScribeSize(null, readStoredScribeSize())).toBe(DEFAULT_SCRIBE_SIZE);
  });

  it('survives an environment with no storage at all', () => {
    vi.stubGlobal('localStorage', undefined);
    expect(readStoredScribeSize()).toBeNull();
    expect(() => storeScribeSize('gross')).not.toThrow();
  });
});
