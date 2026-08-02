// The measured side of the Vergleich page's Verbindungen tab (Handmodell H2,
// „gemessen vs. komponiert", handmodell-stufenplan.md §4): every pair card
// already shows the specimen next to the composed pair — this adds what the
// occurrence and the aggregate layers KNOW about that same join, so the visual
// impression can be read against a number instead of replacing it.
//
// Loading is per source and happens ONCE for the whole tab, never per card:
// the public `pair-instances` list of the source, and — for the hand those
// occurrences name — the admin-gated `pair-aggregates` of that hand. The hand
// is derived (modal non-null `hand_id`), never hardcoded, exactly as in the
// Werkbank: one source, one hand, but WHICH one is data.
//
// Pure grouping/derivation helpers stay exported and free of React so they can
// be unit-tested without a DOM or a fetch.

import { useEffect, useMemo, useState } from 'react';

import { listPairAggregates, listPairInstances } from '@/lib/api';
import type { PairAggregateOut, PairInstanceOut } from '@/lib/api';
import type { StatsStatus } from '@/sections/admin/werkbank/LensStats';
import { pairKeyOf } from '@/sections/admin/werkbank/model';

// Why a card can show nothing: the tab does not ask for measurements at all
// ('idle' — words/Fremdhand), the occurrence list is in flight, it failed, or
// the numbers are there.
export type PairMeasurementStatus = 'idle' | 'loading' | 'ready' | 'error';

// The aggregate layer's own state, in the Werkbank's vocabulary (the type is
// imported rather than restated, so the two surfaces can never drift into two
// different answers to "why is there no median here?"): still in flight, the
// occurrences name no hand, the admin-gated read failed, or the rows are there.
// `layerEmpty` separates "this hand was never rebuilt" from "this join stayed
// below the minimum" once the rows ARE there.
export interface AggregateLayerState {
  status: StatsStatus;
  layerEmpty: boolean;
}

export interface PairMeasurements {
  status: PairMeasurementStatus;
  // The writer the aggregate numbers belong to — null when no occurrence names
  // a hand (then there is no statistics layer to show, which is not an error).
  handId: string | null;
  // The occurrences name more than one hand: the aggregates shown are the
  // modal hand's, which must be said rather than mixed silently.
  handsMixed: boolean;
  // The statistics layer's state, so a card can say WHY it has no median
  // instead of blaming every case on the join's occurrence count.
  aggregates: AggregateLayerState;
  occurrencesByKey: Map<string, PairInstanceOut[]>;
  aggregateByKey: Map<string, PairAggregateOut>;
}

const EMPTY: PairMeasurements = {
  status: 'idle',
  handId: null,
  handsMixed: false,
  // Nothing was ever asked for on this tab; the cards render no measured half
  // at all, so this state is never read.
  aggregates: { status: 'loading', layerEmpty: false },
  occurrencesByKey: new Map(),
  aggregateByKey: new Map(),
};

export function groupPairOccurrences(rows: PairInstanceOut[]): Map<string, PairInstanceOut[]> {
  const map = new Map<string, PairInstanceOut[]>();
  for (const occ of rows) {
    const key = pairKeyOf(occ.left_key, occ.right_key);
    const list = map.get(key);
    if (list) list.push(occ);
    else map.set(key, [occ]);
  }
  return map;
}

export function indexPairAggregates(rows: PairAggregateOut[]): Map<string, PairAggregateOut> {
  return new Map(rows.map((agg) => [pairKeyOf(agg.left_key, agg.right_key), agg]));
}

// The most frequent non-null `hand_id` over the loaded occurrences, plus the
// flag that they do not all name the same one. Rows may predate the hands
// wiring and carry none — if none names a hand, there is simply no layer.
export function modalHandId(rows: PairInstanceOut[]): { handId: string | null; handsMixed: boolean } {
  const counts = new Map<string, number>();
  for (const occ of rows) {
    if (occ.hand_id) counts.set(occ.hand_id, (counts.get(occ.hand_id) ?? 0) + 1);
  }
  let handId: string | null = null;
  let best = 0;
  for (const [id, count] of counts) {
    if (count > best) {
      handId = id;
      best = count;
    }
  }
  return { handId, handsMixed: counts.size > 1 };
}

// Does THIS card's own join carry a bad fit? Only the occurrence dissected on
// exactly this specimen counts — another plate's shaky fit says nothing about
// the pixels on screen. `fit_ok` is checked against false explicitly: an absent
// flag is unknown, not a failure.
export function pairFitUncertain(occurrences: PairInstanceOut[], specimenId: string): boolean {
  return occurrences.some(
    (occ) => occ.kind === 'pair' && occ.specimen_id === specimenId && occ.measurements.fit_ok === false,
  );
}

// Every loaded list is kept together with the key it was read for — the source
// for the occurrences, the hand for the aggregates. A layer whose key no longer
// matches simply does not count as loaded, so a source switch can never show
// the previous plate's occurrences or the previous hand's medians for one
// render, and nothing has to be reset from inside an effect.
export interface Layer<T, K> {
  key: K;
  rows: T[] | null;
  error: boolean;
}

// A layer is settled for a key once its read came back — with rows OR with a
// failure. Both effects skip a settled layer, and that is what makes the
// „loaded once per source" claim above true: `enabled` flips false→true on
// every return to the Verbindungen tab (CompareTabs keeps the view mounted),
// which without the guard refetched both lists each time. Counting a failure as
// settled also keeps a persistently failing read from retrying in a loop, now
// that the effects depend on the very layer they write.
const settled = <T, K>(layer: Layer<T, K>, key: K): boolean =>
  layer.key === key && (layer.rows !== null || layer.error);

/**
 * What the aggregate layer can honestly say about itself, given the layer, the
 * hand it should hold and whether the occurrences (which NAME that hand) are
 * loaded at all. Deliberately mirrors the Werkbank's `statsContextOf`: while
 * anything is still in flight the answer is 'loading' — an in-flight read must
 * never be reported as "no hand" or as a missing measurement.
 */
export function aggregateLayerState(
  layer: Layer<PairAggregateOut, string | null>,
  handId: string | null,
  occurrencesLoaded: boolean,
): AggregateLayerState {
  if (!occurrencesLoaded) return { status: 'loading', layerEmpty: false };
  if (!handId) return { status: 'no-hand', layerEmpty: false };
  // Rows of a previous hand are not this hand's: the read is still pending.
  if (layer.key !== handId) return { status: 'loading', layerEmpty: false };
  if (layer.error) return { status: 'unavailable', layerEmpty: false };
  if (layer.rows === null) return { status: 'loading', layerEmpty: false };
  return { status: 'ready', layerEmpty: layer.rows.length === 0 };
}

/**
 * Fallback occurrence count for a join without an aggregate row — counted for
 * the named hand only. The tooltip attributes the number to one writer, so a
 * second hand harvested on the same source must not be able to inflate it.
 * Without a named hand there is nothing to attribute it to, and all matched
 * occurrences count.
 */
export function countForHand(occurrences: PairInstanceOut[], handId: string | null): number {
  if (!handId) return occurrences.length;
  return occurrences.filter((occ) => occ.hand_id === handId).length;
}

/**
 * Load the measured layers of one source's joins. `enabled` is the tab scope:
 * only the Verbindungen tab asks for them (words are composed from many joins,
 * the Fremdhand tab is view-only context and never measured against).
 */
export function usePairMeasurements(sourceId: string, enabled: boolean): PairMeasurements {
  const [occLayer, setOccLayer] = useState<Layer<PairInstanceOut, string>>({
    key: sourceId,
    rows: null,
    error: false,
  });
  const [aggLayer, setAggLayer] = useState<Layer<PairAggregateOut, string | null>>({
    key: null,
    rows: null,
    error: false,
  });

  useEffect(() => {
    if (!enabled || settled(occLayer, sourceId)) return;
    let cancelled = false;
    listPairInstances(sourceId, undefined, { retries: 2 })
      .then((rows) => {
        if (!cancelled) setOccLayer({ key: sourceId, rows, error: false });
      })
      .catch(() => {
        if (!cancelled) setOccLayer({ key: sourceId, rows: null, error: true });
      });
    return () => {
      cancelled = true;
    };
  }, [sourceId, enabled, occLayer]);

  const loadedOccurrences = occLayer.key === sourceId ? occLayer : null;
  const occurrences = loadedOccurrences?.rows ?? null;
  const { handId, handsMixed } = useMemo(() => modalHandId(occurrences ?? []), [occurrences]);

  // Deliberately a second, dependent effect rather than one Promise.all: this
  // read is admin-gated and secondary — a 401 must leave the cards (and their
  // occurrence counts) fully usable.
  useEffect(() => {
    if (!enabled || !handId || settled(aggLayer, handId)) return;
    let cancelled = false;
    listPairAggregates(handId, undefined, { retries: 1 })
      .then((rows) => {
        if (!cancelled) setAggLayer({ key: handId, rows, error: false });
      })
      .catch(() => {
        if (!cancelled) setAggLayer({ key: handId, rows: null, error: true });
      });
    return () => {
      cancelled = true;
    };
  }, [handId, enabled, aggLayer]);

  const occurrencesByKey = useMemo(() => groupPairOccurrences(occurrences ?? []), [occurrences]);

  // Only the layer that belongs to the CURRENT hand counts as loaded.
  const loadedAggregates = aggLayer.key === handId ? aggLayer : null;
  const aggregateRows = loadedAggregates?.rows;
  const aggregateByKey = useMemo(() => indexPairAggregates(aggregateRows ?? []), [aggregateRows]);

  if (!enabled) return EMPTY;
  return {
    status: loadedOccurrences?.error ? 'error' : occurrences === null ? 'loading' : 'ready',
    handId,
    handsMixed,
    aggregates: aggregateLayerState(aggLayer, handId, occurrences !== null),
    occurrencesByKey,
    aggregateByKey,
  };
}
