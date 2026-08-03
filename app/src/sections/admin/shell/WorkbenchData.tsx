// The workbench's shared data layer: everything the three views (Buchstaben ·
// Übergänge · Wörter) ask about the SAME source and the SAME hand, loaded once
// for the whole admin instead of once per page.
//
// That is the point of the redesign — the three views are lenses on one body of
// evidence, and walking from a letter to one of its joins to a word it appears
// in must not re-fetch the same few hundred rows three times. The occurrence
// lists are public reads; the two statistics layers (Stufenplan H1/H2) are
// admin-gated and strictly secondary: a 401 there leaves every view fully
// usable and only mutes the statistics blocks.
//
// The hand is DERIVED from the loaded occurrences, never hardcoded
// (optimierungs-werkbank.md §6 "genau eine Quelle/Hand"), and `handsMixed` is
// the honesty flag for the day a second writer is harvested.

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

import { useAdmin } from '@/context/AdminContext';
import {
  getWordSamples,
  listAggregates,
  listInstances,
  listPairAggregates,
  listPairInstances,
  listWordInstances,
  rebuildAggregates,
  rebuildPairAggregates,
} from '@/lib/api';
import type {
  AggregateOut,
  InstanceOut,
  PairAggregateOut,
  PairInstanceOut,
  WordInstanceOut,
  WordSampleOut,
} from '@/lib/api';
import { de, fmt } from '@/locales/admin';

import type { StatsContext, StatsStatus } from './LensStats';
import { pairKeyOf } from './model';

// One loaded statistics layer, tagged with the hand it was loaded FOR. Tagging
// instead of resetting is what makes the two behaviours coexist: a hand switch
// invalidates the rows implicitly (they are simply not this hand's), while a
// refetch after a rebuild leaves them mounted until the fresh ones arrive —
// stale-while-revalidate, so the rebuild's caption stays readable.
interface StatsLayer<T> {
  handId: string | null;
  rows: T[] | null;
  error: boolean;
}

const rowsFor = <T,>(layer: StatsLayer<T>, handId: string | null): T[] | null =>
  handId !== null && layer.handId === handId ? layer.rows : null;

function statsContextOf<T>(
  layer: StatsLayer<T>,
  rows: T[] | null,
  handId: string | null,
  handsMixed: boolean,
): StatsContext {
  const status: StatsStatus = !handId
    ? 'no-hand'
    : layer.handId === handId && layer.error
      ? 'unavailable'
      : rows === null
        ? 'loading'
        : 'ready';
  return { status, handId, handsMixed, layerEmpty: rows !== null && rows.length === 0 };
}

interface WorkbenchState {
  loading: boolean;
  error: boolean;
  // The stored occurrences of the active source.
  wordRows: WordInstanceOut[];
  samples: WordSampleOut[];
  sampleById: Map<string, WordSampleOut>;
  // Letter occurrences grouped by glyph_key, worst fit residual first.
  instancesByKey: Map<string, InstanceOut[]>;
  // Letter occurrences grouped by specimen, ascending by composer slot.
  boxesBySpecimen: Map<string, InstanceOut[]>;
  // Join occurrences grouped by "left→right".
  pairsByKey: Map<string, PairInstanceOut[]>;
  // The hand's statistics, one row per key (lowest variant wins for letters).
  aggregatesByKey: Map<string, AggregateOut>;
  pairAggregateByKey: Map<string, PairAggregateOut>;
  handId: string | null;
  letterStats: StatsContext;
  pairStats: StatsContext;
  // Recompute ONE statistics layer and report the outcome as a caption;
  // undefined without a hand to rebuild for.
  rebuildLetterStats?: () => Promise<string>;
  rebuildPairStats?: () => Promise<string>;
}

const Ctx = createContext<WorkbenchState | null>(null);

export function WorkbenchDataProvider({ children }: { children: ReactNode }) {
  const { sourceId } = useAdmin();
  const t = de.admin.werkbank;

  const [wordRows, setWordRows] = useState<WordInstanceOut[] | null>(null);
  const [samples, setSamples] = useState<WordSampleOut[] | null>(null);
  const [instances, setInstances] = useState<InstanceOut[] | null>(null);
  const [pairInstances, setPairInstances] = useState<PairInstanceOut[] | null>(null);
  const [error, setError] = useState(false);
  const [letterLayer, setLetterLayer] = useState<StatsLayer<AggregateOut>>({
    handId: null,
    rows: null,
    error: false,
  });
  const [pairLayer, setPairLayer] = useState<StatsLayer<PairAggregateOut>>({ handId: null, rows: null, error: false });
  // Bumped by a rebuild so THAT layer refetches (a rebuild replaces wholesale).
  const [letterTick, setLetterTick] = useState(0);
  const [pairTick, setPairTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setWordRows(null);
    setSamples(null);
    setInstances(null);
    setPairInstances(null);
    setError(false);
    Promise.all([
      listWordInstances(sourceId, undefined, { retries: 2 }),
      getWordSamples(sourceId, { retries: 2 }),
      listInstances(sourceId, undefined, { retries: 2 }),
      listPairInstances(sourceId, undefined, { retries: 2 }),
    ])
      .then(([words, wordSamples, letterRows, joinRows]) => {
        if (cancelled) return;
        setWordRows(words);
        setSamples(wordSamples);
        setInstances(letterRows);
        setPairInstances(joinRows);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [sourceId]);

  // WHICH hand comes from the loaded rows: the most frequent non-null hand_id
  // across all three occurrence levels. Rows may predate the hands wiring and
  // carry none — if no row names a hand at all, there is no statistics layer.
  const { handId, handsMixed } = useMemo(() => {
    const counts = new Map<string, number>();
    const tally = (id: string | null | undefined) => {
      if (id) counts.set(id, (counts.get(id) ?? 0) + 1);
    };
    for (const inst of instances ?? []) tally(inst.hand_id);
    for (const occ of pairInstances ?? []) tally(occ.hand_id);
    for (const row of wordRows ?? []) tally(row.hand_id);
    let best: string | null = null;
    let bestCount = 0;
    for (const [id, count] of counts) {
      if (count > bestCount) {
        best = id;
        bestCount = count;
      }
    }
    return { handId: best, handsMixed: counts.size > 1 };
  }, [instances, pairInstances, wordRows]);

  // Deliberately NOT part of the occurrence Promise.all, and one effect per
  // layer: these reads are admin-gated and secondary, and a per-layer rebuild
  // refetches only its own list.
  useEffect(() => {
    if (!handId) return;
    let cancelled = false;
    listAggregates(handId, { retries: 1 })
      .then((rows) => {
        if (!cancelled) setLetterLayer({ handId, rows, error: false });
      })
      .catch(() => {
        if (!cancelled) setLetterLayer({ handId, rows: null, error: true });
      });
    return () => {
      cancelled = true;
    };
  }, [handId, letterTick]);

  useEffect(() => {
    if (!handId) return;
    let cancelled = false;
    listPairAggregates(handId, undefined, { retries: 1 })
      .then((rows) => {
        if (!cancelled) setPairLayer({ handId, rows, error: false });
      })
      .catch(() => {
        if (!cancelled) setPairLayer({ handId, rows: null, error: true });
      });
    return () => {
      cancelled = true;
    };
  }, [handId, pairTick]);

  const aggregates = rowsFor(letterLayer, handId);
  const pairAggregates = rowsFor(pairLayer, handId);

  const sampleById = useMemo(() => new Map((samples ?? []).map((s) => [s.id, s])), [samples]);

  const boxesBySpecimen = useMemo(() => {
    const map = new Map<string, InstanceOut[]>();
    for (const inst of instances ?? []) {
      const id = inst.measurements.specimen_id;
      if (!id) continue;
      const list = map.get(id);
      if (list) list.push(inst);
      else map.set(id, [inst]);
    }
    for (const list of map.values()) list.sort((a, b) => (a.measurements.slot ?? 0) - (b.measurements.slot ?? 0));
    return map;
  }, [instances]);

  // Worst first — the letter lens is a work list, so the occurrence whose fit
  // struggled most is the one to look at.
  const instancesByKey = useMemo(() => {
    const map = new Map<string, InstanceOut[]>();
    for (const inst of instances ?? []) {
      const list = map.get(inst.glyph_key);
      if (list) list.push(inst);
      else map.set(inst.glyph_key, [inst]);
    }
    for (const list of map.values()) {
      list.sort((a, b) => (b.measurements.geo_rmse_px ?? 0) - (a.measurements.geo_rmse_px ?? 0));
    }
    return map;
  }, [instances]);

  const pairsByKey = useMemo(() => {
    const map = new Map<string, PairInstanceOut[]>();
    for (const occ of pairInstances ?? []) {
      const key = pairKeyOf(occ.left_key, occ.right_key);
      const list = map.get(key);
      if (list) list.push(occ);
      else map.set(key, [occ]);
    }
    return map;
  }, [pairInstances]);

  // One row per glyph key, lowest variant wins: the lens asks about the LETTER,
  // and the base variant is the row the Laufform is derived from.
  const aggregatesByKey = useMemo(() => {
    const map = new Map<string, AggregateOut>();
    for (const agg of aggregates ?? []) {
      const prev = map.get(agg.glyph_key);
      if (!prev || agg.variant < prev.variant) map.set(agg.glyph_key, agg);
    }
    return map;
  }, [aggregates]);

  const pairAggregateByKey = useMemo(
    () => new Map((pairAggregates ?? []).map((agg) => [pairKeyOf(agg.left_key, agg.right_key), agg])),
    [pairAggregates],
  );

  const rebuildLetterStats = useCallback(async () => {
    if (!handId) throw new Error('no hand');
    const out = await rebuildAggregates(handId);
    setLetterTick((n) => n + 1);
    return fmt(t.statsRebuiltLetters, {
      stored: out.stored,
      count: out.keys.reduce((n, key) => n + key.n_instances, 0),
      skipped: Object.values(out.skipped).reduce((n, value) => n + value, 0),
    });
  }, [handId, t.statsRebuiltLetters]);

  const rebuildPairStats = useCallback(async () => {
    if (!handId) throw new Error('no hand');
    const out = await rebuildPairAggregates(handId);
    setPairTick((n) => n + 1);
    return fmt(t.statsRebuiltPairs, {
      stored: out.stored,
      count: out.pairs.reduce((n, pair) => n + pair.n_instances, 0),
      skipped: Object.values(out.skipped).reduce((n, value) => n + value, 0),
    });
  }, [handId, t.statsRebuiltPairs]);

  const value = useMemo<WorkbenchState>(
    () => ({
      // A failed load ENDS the loading state — otherwise the lists stay null,
      // `loading` stays true forever and every occurrence panel sits on a
      // spinner that will never resolve. Callers show `error` instead.
      loading: !error && (wordRows === null || samples === null || instances === null || pairInstances === null),
      error,
      wordRows: wordRows ?? [],
      samples: samples ?? [],
      sampleById,
      instancesByKey,
      boxesBySpecimen,
      pairsByKey,
      aggregatesByKey,
      pairAggregateByKey,
      handId,
      letterStats: statsContextOf(letterLayer, aggregates, handId, handsMixed),
      pairStats: statsContextOf(pairLayer, pairAggregates, handId, handsMixed),
      rebuildLetterStats: handId ? rebuildLetterStats : undefined,
      rebuildPairStats: handId ? rebuildPairStats : undefined,
    }),
    [
      wordRows,
      samples,
      instances,
      pairInstances,
      error,
      sampleById,
      instancesByKey,
      boxesBySpecimen,
      pairsByKey,
      aggregatesByKey,
      pairAggregateByKey,
      handId,
      handsMixed,
      letterLayer,
      pairLayer,
      aggregates,
      pairAggregates,
      rebuildLetterStats,
      rebuildPairStats,
    ],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useWorkbench(): WorkbenchState {
  const value = useContext(Ctx);
  if (!value) throw new Error('useWorkbench must be used inside <WorkbenchDataProvider>');
  return value;
}
