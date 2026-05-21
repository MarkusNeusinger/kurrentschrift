// App is the state owner: it loads the bboxes/canonical state from the API
// once, and propagates updates down. Child components are presentational +
// fire callbacks; we keep the data flow shallow because the v1 UI is small.

import { useCallback, useEffect, useMemo, useState } from 'react';
import { getBboxes, getCanonical } from './api';
import type { BboxesResponse, Canonical, GlyphBbox } from './types';
import { GlyphSidebar } from './components/GlyphSidebar';
import { ChartCanvas } from './components/ChartCanvas';
import { RightPanel } from './components/RightPanel';

export function App() {
  const [bboxes, setBboxes] = useState<BboxesResponse | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [canonStatus, setCanonStatus] = useState<Record<string, boolean>>({});
  const [cropCacheBust, setCropCacheBust] = useState<number>(0);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    getBboxes()
      .then((res) => {
        setBboxes(res);
        const keys = Object.keys(res.bboxes);
        if (keys.length && !selected) setSelected(keys[0]);
      })
      .catch((e) => setLoadError(String(e)));
    // selected is intentionally not in deps — first-load only
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Lazy probe of canonical existence per glyph (just to drive sidebar ☑).
  useEffect(() => {
    if (!bboxes) return;
    const keys = Object.keys(bboxes.bboxes);
    let cancelled = false;
    (async () => {
      const next: Record<string, boolean> = {};
      for (const k of keys) {
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

  const currentBbox: GlyphBbox | null = useMemo(() => {
    if (!bboxes || !selected) return null;
    return bboxes.bboxes[selected] ?? null;
  }, [bboxes, selected]);

  const updateBboxLocal = useCallback(
    (key: string, next: GlyphBbox | null) => {
      setBboxes((prev) => {
        if (!prev) return prev;
        return { ...prev, bboxes: { ...prev.bboxes, [key]: next } };
      });
      setCropCacheBust(Date.now());
    },
    [],
  );

  const markCanonical = useCallback((key: string, _canon: Canonical) => {
    setCanonStatus((s) => ({ ...s, [key]: true }));
  }, []);

  if (loadError) {
    return (
      <div style={{ padding: 24 }}>
        <h2>Failed to load /bboxes</h2>
        <p>{loadError}</p>
        <p>Is the API running? <code>uv run uvicorn api.main:app --port 8000</code></p>
      </div>
    );
  }

  if (!bboxes) return <div style={{ padding: 24 }}>loading…</div>;

  return (
    <div className="app">
      <GlyphSidebar
        keys={Object.keys(bboxes.bboxes)}
        bboxes={bboxes.bboxes}
        selected={selected}
        canonStatus={canonStatus}
        onSelect={setSelected}
      />
      <ChartCanvas
        chartSize={bboxes.image_size}
        bboxes={bboxes.bboxes}
        selected={selected}
        onChange={updateBboxLocal}
      />
      <RightPanel
        glyphKey={selected}
        bbox={currentBbox}
        cropCacheBust={cropCacheBust}
        onBboxChange={updateBboxLocal}
        onCanonicalSaved={markCanonical}
      />
    </div>
  );
}
