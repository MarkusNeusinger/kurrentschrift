// The admin context object, the shape it carries and the hook that reads it —
// beside `AdminContext.tsx`, which holds the provider components.
//
// The split is not cosmetic: a module that exports both a component and a hook
// takes no Fast-Refresh update, so editing the provider used to force a full
// reload of the workbench (react-refresh/only-export-components). Consumers
// import `useAdmin` from here; the provider stays where its name says.
import { createContext, useContext } from 'react';

import type { BboxOut, GlyphSummary, SourceOut } from '@/lib/api';

export interface AdminState {
  sourceId: string;
  source: SourceOut | null;
  // All chart sources, for the sidebar switcher.
  sources: SourceOut[];
  switchSource: (id: string) => void;
  bboxesByKey: Record<string, BboxOut>;
  glyphsByKey: Record<string, GlyphSummary>;
  loadError: string | null;
  // True while the boot load is retrying through a Cloud Run cold start.
  waking: boolean;
  activeGlyph: string | null;
  visibleGlyphs: Set<string>;
  cropCacheBust: number;
  setActiveGlyph: (key: string | null) => void;
  toggleVisible: (key: string) => void;
  setOnlyVisible: (keys: string[]) => void;
  upsertBbox: (key: string, bbox: BboxOut) => void;
  removeBbox: (key: string) => void;
  markGlyphTraced: (key: string, summary: GlyphSummary) => void;
  removeGlyph: (key: string) => void;
  refreshCrop: () => void;
  // Glyph currently open in the Einrichtungs-Wizard / the Diagnose modal, or
  // null when closed. Both modals are mounted once in AppLayout and driven from
  // here so any surface (chart toolbar, sidebar) can open them by glyph key.
  wizardGlyph: string | null;
  openWizard: (key: string) => void;
  closeWizard: () => void;
  diagnoseGlyph: string | null;
  openDiagnose: (key: string) => void;
  closeDiagnose: () => void;
}

export const AdminCtx = createContext<AdminState | null>(null);

export function useAdmin(): AdminState {
  const v = useContext(AdminCtx);
  if (!v) throw new Error('useAdmin must be used inside <AdminProvider>');
  return v;
}
