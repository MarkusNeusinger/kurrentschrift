// Shared admin state — source metadata, bboxes-by-key, traced-glyph-status.
//
// The list of known glyph_keys is in `constants.ts` (the MVP target set), so
// the sidebar can show all expected glyphs even before any bboxes exist. The
// DB only stores rows for glyphs that have actually been bbox'd or traced.

import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { getBboxes, getGlyphs, getSource } from '@/lib/api';
import { KNOWN_GLYPHS } from './constants';
import type { BboxOut, GlyphSummary, SourceOut } from '@/lib/api';

interface AdminState {
  source: SourceOut | null;
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

const Ctx = createContext<AdminState | null>(null);

export function AdminProvider({ children }: { children: ReactNode }) {
  const [source, setSource] = useState<SourceOut | null>(null);
  const [bboxesByKey, setBboxesByKey] = useState<Record<string, BboxOut>>({});
  const [glyphsByKey, setGlyphsByKey] = useState<Record<string, GlyphSummary>>({});
  const [loadError, setLoadError] = useState<string | null>(null);
  const [waking, setWaking] = useState<boolean>(false);
  const [activeGlyph, setActiveGlyph] = useState<string | null>(null);
  const [visibleGlyphs, setVisibleGlyphs] = useState<Set<string>>(new Set());
  const [cropCacheBust, setCropCacheBust] = useState<number>(0);
  const [wizardGlyph, setWizardGlyph] = useState<string | null>(null);
  const [diagnoseGlyph, setDiagnoseGlyph] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      // Cloud Run cold start: retry the boot load with backoff (~47s budget)
      // and flag `waking` on the first retry so the UI can say "API startet…".
      const onRetry = () => {
        if (!cancelled) setWaking(true);
      };
      const retry = { retries: 8, onRetry };
      try {
        const [s, bboxes, glyphs] = await Promise.all([
          getSource(retry),
          getBboxes(retry),
          getGlyphs(retry),
        ]);
        if (cancelled) return;
        setWaking(false);
        setSource(s);
        const bm: Record<string, BboxOut> = {};
        for (const b of bboxes) bm[b.glyph_key] = b;
        setBboxesByKey(bm);
        const gm: Record<string, GlyphSummary> = {};
        for (const g of glyphs) gm[g.glyph_key] = g;
        setGlyphsByKey(gm);
        setVisibleGlyphs(new Set(bboxes.map((b) => b.glyph_key)));
      } catch (e) {
        if (!cancelled) {
          setWaking(false);
          setLoadError(String(e));
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const toggleVisible = useCallback((key: string) => {
    setVisibleGlyphs((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }, []);

  const setOnlyVisible = useCallback((keys: string[]) => {
    setVisibleGlyphs(new Set(keys));
  }, []);

  const upsertBbox = useCallback((key: string, bbox: BboxOut) => {
    setBboxesByKey((prev) => ({ ...prev, [key]: bbox }));
    setCropCacheBust(Date.now());
    setVisibleGlyphs((prev) => {
      if (prev.has(key)) return prev;
      const next = new Set(prev);
      next.add(key);
      return next;
    });
  }, []);

  const removeBbox = useCallback((key: string) => {
    setBboxesByKey((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }, []);

  const markGlyphTraced = useCallback((key: string, summary: GlyphSummary) => {
    setGlyphsByKey((prev) => ({ ...prev, [key]: summary }));
  }, []);

  const removeGlyph = useCallback((key: string) => {
    setGlyphsByKey((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }, []);

  const refreshCrop = useCallback(() => setCropCacheBust(Date.now()), []);

  // Opening either modal also activates the glyph, so the sidebar/chart stay in
  // sync with whatever is being authored or inspected.
  const openWizard = useCallback((key: string) => {
    setActiveGlyph(key);
    setWizardGlyph(key);
  }, []);
  const closeWizard = useCallback(() => setWizardGlyph(null), []);
  const openDiagnose = useCallback((key: string) => {
    setActiveGlyph(key);
    setDiagnoseGlyph(key);
  }, []);
  const closeDiagnose = useCallback(() => setDiagnoseGlyph(null), []);

  const value = useMemo<AdminState>(
    () => ({
      source,
      bboxesByKey,
      glyphsByKey,
      loadError,
      waking,
      activeGlyph,
      visibleGlyphs,
      cropCacheBust,
      setActiveGlyph,
      toggleVisible,
      setOnlyVisible,
      upsertBbox,
      removeBbox,
      markGlyphTraced,
      removeGlyph,
      refreshCrop,
      wizardGlyph,
      openWizard,
      closeWizard,
      diagnoseGlyph,
      openDiagnose,
      closeDiagnose,
    }),
    [
      source,
      bboxesByKey,
      glyphsByKey,
      loadError,
      waking,
      activeGlyph,
      visibleGlyphs,
      cropCacheBust,
      toggleVisible,
      setOnlyVisible,
      upsertBbox,
      removeBbox,
      markGlyphTraced,
      removeGlyph,
      refreshCrop,
      wizardGlyph,
      openWizard,
      closeWizard,
      diagnoseGlyph,
      openDiagnose,
      closeDiagnose,
    ],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAdmin(): AdminState {
  const v = useContext(Ctx);
  if (!v) throw new Error('useAdmin must be used inside <AdminProvider>');
  return v;
}

export { KNOWN_GLYPHS };
