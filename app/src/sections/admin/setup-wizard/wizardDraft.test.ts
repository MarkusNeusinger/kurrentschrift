// The rescue copy is the last thing between the author and a lost Weg, so it
// has to survive a hostile shelf: sessionStorage is editable by hand and it
// outlives a deploy that changed the shape. A malformed entry must read as
// „no draft", never reach the canvas, and never throw on the way.

import { beforeEach, describe, expect, it, vi } from 'vitest';

import { draftKeyFor, isStrokeList, readDraft, writeDraft } from './wizardDraft';

const KEY = draftKeyFor('suetterlin-1922', 'a');
const STROKES = [
  [
    { x: 10, y: 20 },
    { x: 12, y: 26 },
  ],
];

// A minimal sessionStorage; jsdom is not configured for this suite.
function installStorage(): Map<string, string> {
  const store = new Map<string, string>();
  vi.stubGlobal('window', {
    sessionStorage: {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => void store.set(k, v),
      removeItem: (k: string) => void store.delete(k),
    },
  });
  return store;
}

describe('wizardDraft', () => {
  let store: Map<string, string>;
  beforeEach(() => {
    store = installStorage();
  });

  it('scopes the key by source AND glyph', () => {
    // One glyph's draft must never be offered on another — or on the same glyph
    // of a different Vorlage.
    expect(draftKeyFor('suetterlin-1922', 'a')).not.toBe(draftKeyFor('suetterlin-1922', 'longs'));
    expect(draftKeyFor('loth-1866', 'a')).not.toBe(KEY);
  });

  it('round-trips a drawn Weg', () => {
    writeDraft('suetterlin-1922', 'a', STROKES);
    expect(readDraft('suetterlin-1922', 'a')).toEqual(STROKES);
  });

  it('clears the entry on an empty stroke list rather than storing []', () => {
    writeDraft('suetterlin-1922', 'a', STROKES);
    writeDraft('suetterlin-1922', 'a', []);
    expect(store.has(KEY)).toBe(false);
    expect(readDraft('suetterlin-1922', 'a')).toBeNull();
  });

  it('reads anything malformed as absent instead of handing it on', () => {
    // Every one of these used to pass the old top-level-array check and would
    // have reached the canvas as a cast (Copilot review, PR #487).
    const bad = [
      'not json at all',
      'null',
      '[]',
      '{"strokes":[]}',
      '["nope"]',
      '[[{"x":"10","y":20}]]',
      '[[{"y":20}]]',
      '[[null]]',
      '[[{"x":null,"y":null}]]',
      // NaN/Infinity survive a hand edit as strings and must not slip through.
      '[[{"x":1e999,"y":0}]]',
    ];
    for (const raw of bad) {
      store.set(KEY, raw);
      expect(readDraft('suetterlin-1922', 'a'), raw).toBeNull();
    }
  });

  it('accepts the optional per-point fields the wire type allows', () => {
    const rich = [[{ x: 1, y: 2, pressure: 0.4, t: 12, pen_up: true }]];
    expect(isStrokeList(rich)).toBe(true);
  });

  it('never throws when the shelf itself refuses', () => {
    vi.stubGlobal('window', {
      sessionStorage: {
        getItem: () => {
          throw new Error('SecurityError: private mode');
        },
        setItem: () => {
          throw new Error('QuotaExceededError');
        },
        removeItem: () => {},
      },
    });
    expect(readDraft('suetterlin-1922', 'a')).toBeNull();
    expect(() => writeDraft('suetterlin-1922', 'a', STROKES)).not.toThrow();
  });
});
