// The pure derivations behind the Vergleich page's „Gemessen" readout: which
// hand the numbers belong to, which occurrences belong to which join, when a
// card may flag its own fit as unsure, what the aggregate layer may claim about
// itself and how many occurrences a card may credit to the named hand. They all
// decide what a reader is told about a measurement, so they are pinned here
// rather than eyeballed in the browser.

import { describe, expect, it } from 'vitest';

import type { PairAggregateOut, PairInstanceOut } from '@/lib/api';

import {
  aggregateLayerState,
  countForHand,
  groupPairOccurrences,
  indexPairAggregates,
  modalHandId,
  pairFitUncertain,
  type Layer,
} from './pairMeasurement';

const occ = (over: Partial<PairInstanceOut>): PairInstanceOut => ({
  left_key: 'a',
  right_key: 'b',
  kind: 'pair',
  specimen_id: 'p-ab',
  slot: 0,
  hand_id: 'suetterlin-1922-norm',
  geometry: { offset: [0.2, 0], connector: [[0, 0]] },
  measurements: {},
  ...over,
});

const agg = (over: Partial<PairAggregateOut>): PairAggregateOut => ({
  left_key: 'a',
  right_key: 'b',
  offset_center: [0.2, 0],
  connector_center: [[0, 0]],
  hull: {},
  mean_stats: {},
  n_instances: 3,
  ...over,
});

describe('modalHandId', () => {
  it('returns the most frequent non-null hand and flags a mix', () => {
    const rows = [occ({}), occ({ slot: 1 }), occ({ slot: 2, hand_id: 'abb22-schueler' })];
    expect(modalHandId(rows)).toEqual({ handId: 'suetterlin-1922-norm', handsMixed: true });
  });

  it('ignores rows without a hand and reports none when nobody names one', () => {
    expect(modalHandId([occ({ hand_id: null })])).toEqual({ handId: null, handsMixed: false });
    expect(modalHandId([])).toEqual({ handId: null, handsMixed: false });
  });
});

describe('grouping', () => {
  it('groups occurrences and indexes aggregates by the same pair key', () => {
    const rows = [occ({}), occ({ slot: 1 }), occ({ left_key: 'e', right_key: 'n', specimen_id: 'p-en' })];
    const grouped = groupPairOccurrences(rows);
    expect(grouped.get('a→b')).toHaveLength(2);
    expect(grouped.get('e→n')).toHaveLength(1);

    const indexed = indexPairAggregates([agg({}), agg({ left_key: 'e', right_key: 'n' })]);
    expect(indexed.get('a→b')?.n_instances).toBe(3);
    expect([...grouped.keys()].every((key) => indexed.has(key))).toBe(true);
  });
});

describe('pairFitUncertain', () => {
  it('only counts a bad fit measured on THIS specimen', () => {
    const here = occ({ measurements: { fit_ok: false } });
    const elsewhere = occ({ specimen_id: 'w-abend', kind: 'word', measurements: { fit_ok: false } });
    expect(pairFitUncertain([here], 'p-ab')).toBe(true);
    expect(pairFitUncertain([elsewhere], 'p-ab')).toBe(false);
    expect(pairFitUncertain([here], 'p-cd')).toBe(false);
  });

  it('treats an absent flag as unknown, not as a failure', () => {
    expect(pairFitUncertain([occ({}), occ({ slot: 1, measurements: { fit_ok: true } })], 'p-ab')).toBe(false);
  });
});

describe('aggregateLayerState', () => {
  const layer = (over: Partial<Layer<PairAggregateOut, string | null>>): Layer<PairAggregateOut, string | null> => ({
    key: 'suetterlin-1922-norm',
    rows: [agg({})],
    error: false,
    ...over,
  });

  it('stays „loading" until the occurrences that name the hand are there', () => {
    // The hand is derived FROM the occurrences: before they land, „no hand" and
    // „no measurement" would both be guesses.
    expect(aggregateLayerState(layer({ key: null, rows: null }), null, false)).toEqual({
      status: 'loading',
      layerEmpty: false,
    });
  });

  it('reports no hand only once the occurrences are loaded and name none', () => {
    expect(aggregateLayerState(layer({ key: null, rows: null }), null, true)).toEqual({
      status: 'no-hand',
      layerEmpty: false,
    });
  });

  it('separates „no occurrences at all" from „occurrences that name no hand"', () => {
    // With zero occurrences nothing COULD have named a hand, so „keine Hand"
    // would blame a cause that cannot exist yet — the first-run state gets its
    // own sentence, naming the harvest as the next step (audit 2026-09-02).
    expect(aggregateLayerState(layer({ key: null, rows: null }), null, true, true)).toEqual({
      status: 'no-occurrences',
      layerEmpty: false,
    });
    // …and it never wins over „still loading": an empty list that has not
    // arrived is not an empty list.
    expect(aggregateLayerState(layer({ key: null, rows: null }), null, false, true)).toEqual({
      status: 'loading',
      layerEmpty: false,
    });
  });

  it('counts rows of a previous hand as still loading, never as the current one`s', () => {
    expect(aggregateLayerState(layer({ key: 'abb22-schueler' }), 'suetterlin-1922-norm', true)).toEqual({
      status: 'loading',
      layerEmpty: false,
    });
  });

  it('reports the failed admin-gated read as unavailable', () => {
    expect(aggregateLayerState(layer({ rows: null, error: true }), 'suetterlin-1922-norm', true)).toEqual({
      status: 'unavailable',
      layerEmpty: false,
    });
  });

  it('separates a never-rebuilt hand from a loaded, non-empty layer', () => {
    expect(aggregateLayerState(layer({ rows: [] }), 'suetterlin-1922-norm', true)).toEqual({
      status: 'ready',
      layerEmpty: true,
    });
    expect(aggregateLayerState(layer({}), 'suetterlin-1922-norm', true)).toEqual({
      status: 'ready',
      layerEmpty: false,
    });
  });
});

describe('countForHand', () => {
  it('counts only the occurrences of the named hand', () => {
    const rows = [
      occ({}),
      occ({ slot: 1 }),
      occ({ slot: 2, hand_id: 'abb22-schueler' }),
      occ({ slot: 3, hand_id: null }),
    ];
    expect(countForHand(rows, 'suetterlin-1922-norm')).toBe(2);
    expect(countForHand(rows, 'abb22-schueler')).toBe(1);
  });

  it('counts everything when no hand is named — there is nobody to credit', () => {
    expect(countForHand([occ({ hand_id: null }), occ({ slot: 1, hand_id: null })], null)).toBe(2);
  });
});
