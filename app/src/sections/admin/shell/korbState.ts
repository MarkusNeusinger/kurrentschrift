// The Auftragskorb context object and the three hooks that read it — beside
// `KorbContext.tsx`, which holds the provider and the drawer it mounts.
//
// Split out because a module that exports a provider AND its hooks takes no
// Fast-Refresh update (react-refresh/only-export-components): editing the
// basket's own UI reloaded the whole workbench.
import { createContext, useContext } from 'react';

import type { WorkItemOut } from '@/lib/api';

import type { Mark } from './model';

export interface KorbState {
  // Open + returned items of the active source; null while unknown or when the
  // admin-gated read failed.
  openCount: number | null;
  // The rows behind that count. They were always fetched and always thrown
  // away; keeping them lets a work list say „dieser Buchstabe hat 2 offene
  // Aufträge" without a second read (`korbTargets.ts`). Same quiet absence:
  // null while unknown, never an invented empty list.
  items: WorkItemOut[] | null;
  fileMark: (mark: Mark) => void;
  openKorb: () => void;
}

export const KorbCtx = createContext<KorbState | null>(null);

export function useKorb(): KorbState {
  const value = useContext(KorbCtx);
  if (!value) throw new Error('useKorb must be used inside <KorbProvider>');
  return value;
}

// The ⚑ affordance every view files with, so the wording and the icon stay the
// same wherever a complaint is raised.
export function useFileMark(): (mark: Mark) => void {
  return useKorb().fileMark;
}

export const useOpenCount = (): number | null => useKorb().openCount;

// The basket's rows for the surfaces that count them per subject.
export const useKorbItems = (): WorkItemOut[] | null => useKorb().items;
