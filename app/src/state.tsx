// Shared admin state: bboxes/canonical status/active glyph/visible glyphs.
// Loaded once at app start; mutations go through these setters so both
// the chart page and the editor page see consistent data without prop
// drilling. Cache-bust ints force <img src="/api/chart/crop/..."> to
// reload after a bbox change.

import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { getBboxes, getCanonical } from './api';
import type { BboxesResponse, Canonical, GlyphBbox } from './types';

interface AdminState {
  bboxes: BboxesResponse | null;
  loadError: string | null;
  activeGlyph: string | null;
  visibleGlyphs: Set<string>;
  canonStatus: Record<string, boolean>;
  cropCacheBust: number;
  setActiveGlyph: (key: string | null) => void;
  toggleVisible: (key: string) => void;
  setOnlyVisible: (keys: string[]) => void;
  updateBbox: (key: string, next: GlyphBbox | null) => void;
  markCanonical: (key: string, canon: Canonical) => void;
  refreshCrop: () => void;
}

const Ctx = createContext<AdminState | null>(null);

export function AdminProvider({ children }: { children: ReactNode }) {
  const [bboxes, setBboxes] = useState<BboxesResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [activeGlyph, setActiveGlyph] = useState<string | null>(null);
  const [visibleGlyphs, setVisibleGlyphs] = useState<Set<string>>(new Set());
  const [canonStatus, setCanonStatus] = useState<Record<string, boolean>>({});
  const [cropCacheBust, setCropCacheBust] = useState<number>(0);

  useEffect(() => {
    getBboxes()
      .then((res) => {
        setBboxes(res);
        // Default visibility: any glyph that has a bbox is shown.
        const initiallyVisible = new Set<string>();
        for (const [k, v] of Object.entries(res.bboxes)) {
          if (v !== null) initiallyVisible.add(k);
        }
        setVisibleGlyphs(initiallyVisible);
      })
      .catch((e) => setLoadError(String(e)));
  }, []);

  useEffect(() => {
    if (!bboxes) return;
    let cancelled = false;
    (async () => {
      const next: Record<string, boolean> = {};
      for (const k of Object.keys(bboxes.bboxes)) {
        try {
          const c = await getCanonical(k);
          next[k] = c !== null;
        } catch {
          next[k] = false;
        }
        if (cancelled) return;
      }
      if (!cancelled) setCanonStatus(next);
    })();
    return () => {
      cancelled = true;
    };
  }, [bboxes]);

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

  const updateBbox = useCallback((key: string, next: GlyphBbox | null) => {
    setBboxes((prev) => {
      if (!prev) return prev;
      return { ...prev, bboxes: { ...prev.bboxes, [key]: next } };
    });
    setCropCacheBust(Date.now());
    if (next !== null) {
      setVisibleGlyphs((prev) => {
        if (prev.has(key)) return prev;
        const cp = new Set(prev);
        cp.add(key);
        return cp;
      });
    }
  }, []);

  const markCanonical = useCallback((key: string, _canon: Canonical) => {
    setCanonStatus((s) => ({ ...s, [key]: true }));
  }, []);

  const refreshCrop = useCallback(() => setCropCacheBust(Date.now()), []);

  const value = useMemo<AdminState>(
    () => ({
      bboxes,
      loadError,
      activeGlyph,
      visibleGlyphs,
      canonStatus,
      cropCacheBust,
      setActiveGlyph,
      toggleVisible,
      setOnlyVisible,
      updateBbox,
      markCanonical,
      refreshCrop,
    }),
    [
      bboxes,
      loadError,
      activeGlyph,
      visibleGlyphs,
      canonStatus,
      cropCacheBust,
      toggleVisible,
      setOnlyVisible,
      updateBbox,
      markCanonical,
      refreshCrop,
    ],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAdmin(): AdminState {
  const v = useContext(Ctx);
  if (!v) throw new Error('useAdmin must be used inside <AdminProvider>');
  return v;
}
