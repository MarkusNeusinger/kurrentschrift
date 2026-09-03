// Shared admin state — active source, source metadata, bboxes-by-key,
// traced-glyph-status.
//
// The list of known glyph_keys is in `domain/glyphs.ts` (the MVP target set), so
// the sidebar can show all expected glyphs even before any bboxes exist. The
// DB only stores rows for glyphs that have actually been bbox'd or traced.
//
// The active source is admin-only runtime state (persisted per browser); the
// public pages stay pinned to CONFIG.sourceId. Switching remounts the whole
// per-source subtree via the React key below, so bboxes, glyph status,
// visibility, viewport and open modals reset without hand-written cleanup.

import { ReactNode, useCallback, useEffect, useMemo, useState } from 'react';

import { AdminCtx, type AdminState } from '@/context/adminState';
import { CONFIG } from '@/global-config';
import { ApiError, getBboxes, getGlyphs, getSource, getSources } from '@/lib/api';
import { de } from '@/locales';
import type { BboxOut, GlyphSummary, SourceOut } from '@/lib/api';

const SOURCE_STORAGE_KEY = 'kurrentschrift.admin.sourceId';

export function AdminProvider({
  children,
  pinnedSourceId,
}: {
  children: ReactNode;
  // Pin the provider to one source and ignore the persisted admin selection —
  // for public mounts (the quiz) that must always show the site-wide source.
  pinnedSourceId?: string;
}) {
  const [sourceId, setSourceId] = useState<string>(() => {
    if (pinnedSourceId) return pinnedSourceId;
    try {
      const stored = localStorage.getItem(SOURCE_STORAGE_KEY);
      // A persisted id that is no longer offered would strand the admin on a
      // Vorlage with no card to switch away from — the picker is the only way
      // out. Fall back to the build default instead (same reasoning as the
      // 404 recovery below, one step earlier).
      if (stored && !CONFIG.hiddenSourceIds.includes(stored)) return stored;
      return CONFIG.sourceId;
    } catch {
      return CONFIG.sourceId;
    }
  });

  const switchSource = useCallback(
    (id: string) => {
      if (pinnedSourceId) return;
      try {
        localStorage.setItem(SOURCE_STORAGE_KEY, id);
      } catch {
        /* private mode — the switch still holds for this session */
      }
      setSourceId(id);
    },
    [pinnedSourceId],
  );

  return (
    <SourceScopedProvider key={sourceId} sourceId={sourceId} switchSource={switchSource}>
      {children}
    </SourceScopedProvider>
  );
}

function SourceScopedProvider({
  sourceId,
  switchSource,
  children,
}: {
  sourceId: string;
  switchSource: (id: string) => void;
  children: ReactNode;
}) {
  const [source, setSource] = useState<SourceOut | null>(null);
  const [sources, setSources] = useState<SourceOut[]>([]);
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
        const [s, allSources, bboxes, glyphs] = await Promise.all([
          getSource(sourceId, retry),
          getSources(retry),
          getBboxes(sourceId, retry),
          getGlyphs(sourceId, retry),
        ]);
        if (cancelled) return;
        setWaking(false);
        setSource(s);
        // The ONE narrowing of the source list: chart sources only, minus the
        // ones the workbench does not currently offer (CONFIG.hiddenSourceIds
        // — a presentation choice, nothing is deleted server-side).
        setSources(
          allSources.filter((x) => x.kind === 'chart' && !CONFIG.hiddenSourceIds.includes(x.id)),
        );
        const bm: Record<string, BboxOut> = {};
        for (const b of bboxes) bm[b.glyph_key] = b;
        setBboxesByKey(bm);
        const gm: Record<string, GlyphSummary> = {};
        for (const g of glyphs) gm[g.glyph_key] = g;
        setGlyphsByKey(gm);
        setVisibleGlyphs(new Set(bboxes.map((b) => b.glyph_key)));
      } catch (e) {
        if (cancelled) return;
        setWaking(false);
        // A stale persisted source id (renamed/removed in the DB) must not
        // brick the admin — fall back to the build default instead.
        if (e instanceof ApiError && e.status === 404 && sourceId !== CONFIG.sourceId) {
          switchSource(CONFIG.sourceId);
          return;
        }
        // Fixed German copy for the user (this state renders on the public
        // /quiz too); the raw exception goes to the console for diagnosis.
        console.error('source boot load failed', e);
        setLoadError(de.common.boot.sourceUnreachableDetail);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [sourceId, switchSource]);

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
    // A trace/resample changes the canonical, so every diagnostic-derived
    // render (Diagnose stages, WrittenGlyph cache) must refetch — the crop
    // bytes are unchanged, but the bust doubles as the "canonical version".
    setCropCacheBust(Date.now());
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
      sourceId,
      source,
      sources,
      switchSource,
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
      sourceId,
      source,
      sources,
      switchSource,
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

  return <AdminCtx.Provider value={value}>{children}</AdminCtx.Provider>;
}
