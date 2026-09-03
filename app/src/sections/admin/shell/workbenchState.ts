// What the workbench's shared data layer hands its three views, the context
// that carries it and the hook that reads it — beside `WorkbenchData.tsx`,
// which holds the provider that fills it.
//
// Split out because a module exporting a provider AND its hook takes no
// Fast-Refresh update (react-refresh/only-export-components), and this
// provider owns the admin's whole evidence load: a reload here costs every
// occurrence fetch again.
import { createContext, useContext } from 'react';

import type {
  AggregateOut,
  InstanceOut,
  PairAggregateOut,
  PairInstanceOut,
  WordInstanceOut,
  WordSampleOut,
} from '@/lib/api';

import type { StatsContext } from './LensStats';

export interface WorkbenchState {
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
  // Every loaded letter aggregate, unfiltered — what the Laufform apply step
  // previews, since it acts on the hand as a whole rather than on one key.
  allAggregates: AggregateOut[];
  handId: string | null;
  letterStats: StatsContext;
  pairStats: StatsContext;
  // Recompute ONE statistics layer and report the outcome as a caption;
  // undefined without a hand to rebuild for.
  rebuildLetterStats?: () => Promise<string>;
  rebuildPairStats?: () => Promise<string>;
  // Refetch the letter statistics without recomputing them — after an apply,
  // which changed the rows' freshness numbers but not the aggregates.
  refreshLetterStats: () => void;
  // Refetch ONLY the word traces (uncached read) — the word editor's save
  // replaces one row, and the evidence views must show the stored state, not
  // the load-time snapshot.
  refreshWordTraces: () => void;
}

export const WorkbenchCtx = createContext<WorkbenchState | null>(null);

export function useWorkbench(): WorkbenchState {
  const value = useContext(WorkbenchCtx);
  if (!value) throw new Error('useWorkbench must be used inside <WorkbenchDataProvider>');
  return value;
}
