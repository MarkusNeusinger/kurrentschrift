// A Skip-Eintrag is an entry of the same list, and every surface that draws a
// path has to take it out first. Pinned here rather than left to a screenshot:
// a skip reaching `PfadLayer` is not a wrong picture but a crash — it has no
// `registration_px` to read a `tx` off.

import { describe, expect, it } from 'vitest';

import type { EigenhandPfad } from '@/lib/api';
import { bahnenOf } from './pfadBahnen';

function bahn(overrides: Partial<EigenhandPfad> = {}): EigenhandPfad {
  return {
    box_index: 0,
    word: 'lesen',
    status: null,
    grund: null,
    detail: null,
    strokes: [[[0, 0]]],
    letter_spans: null,
    registration_px: { tx: 0, ty: 0, baseline_row: 0 },
    xh_px: 100,
    verfahren: 'tintenpfad',
    konfiguration: {},
    meta: {},
    erzeugt_am: '2026-09-20',
    flecken_n: null,
    ...overrides,
  };
}

function skip(overrides: Partial<EigenhandPfad> = {}): EigenhandPfad {
  return bahn({
    status: 'skipped',
    grund: 'unauthored',
    strokes: [],
    registration_px: null,
    xh_px: null,
    ...overrides,
  });
}

describe('bahnenOf', () => {
  it('keeps a stored path and drops the box that only says why there is none', () => {
    const drawn = bahnenOf([bahn(), skip({ box_index: 1, word: 'das' })]);
    expect(drawn.map((pfad) => pfad.box_index)).toEqual([0]);
    // The narrowing is the point: this line does not compile without it.
    expect(drawn[0].registration_px.tx).toBe(0);
  });

  it('reads a row written under format 1, where the status is simply absent', () => {
    expect(bahnenOf([bahn({ status: null })])).toHaveLength(1);
  });

  it('decides on the status, never on an empty stroke list', () => {
    // A skip that still brought its frame is a skip; a path with no strokes is
    // a malformed path the server would not have stored. Neither is inferred
    // from `strokes`, which is the guessing format 2 exists to end.
    expect(bahnenOf([skip({ registration_px: { tx: 1, ty: 0, baseline_row: 2 }, xh_px: 40 })])).toEqual([]);
  });

  it('survives the two empty answers the read can give', () => {
    expect(bahnenOf(null)).toEqual([]);
    expect(bahnenOf([])).toEqual([]);
  });
});
