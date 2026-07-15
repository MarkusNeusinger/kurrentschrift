// useGrundtafeln — read-only loader for the public Schreibtafel: the three
// Ausgangsschriften (Kurrent · Sütterlin · Offenbacher) side by side, each with
// whatever exists in the DB today. Unlike the quiz / the old single-source Tafel
// it does NOT use the pinned AdminProvider (which scopes to one source): it
// fetches the style registry + all chart sources directly and groups them by
// style, so all three Grundtafeln render from one mount. Cold-start retry mirrors
// AdminContext's boot load (~47s budget, `waking` flag on the first retry).
//
// State per script:
//   - 'written'  — the chart source IS the site-wide source (CONFIG.sourceId):
//                  Original scan + the "as written" grid. WrittenGlyph renders
//                  CONFIG.sourceId, so only this script can be written today.
//   - 'original' — a chart source exists but is not the written source yet
//                  (Kurrent / Loth 1866): only the Original scan, "in Arbeit".
//   - 'pending'  — no chart source at all: a placeholder (no scan to show).

import { useEffect, useState } from 'react';

import { LETTERS, glyphKeyFor, type Position } from '@/domain/glyphs';
import { CONFIG } from '@/global-config';
import { getBboxes, getGlyphs, getSources, getStyles } from '@/lib/api';
import type { BboxOut, GlyphSummary, SourceOut, StyleOut } from '@/lib/api';
import { de } from '@/locales';
import { styleLabel } from '@/locales/de/common';

// Canonical teaching order (oldest → newest), matching the landing + Schriftkunde.
const STYLE_ORDER = ['kurrent', 'suetterlin', 'offenbacher'] as const;

// One representative position per letter: prefer the medial (body) form, falling
// back to initial then final — the same rule the old single-source Tafel used.
const PREFERRED_POSITIONS: Position[] = ['medial', 'initial', 'final'];

// One marked-letter slot on the Schreibtafel sheet, in the chart's own layout.
// `key` is set only when the letter has a locked canonical (it renders); a
// marked-but-untraced letter keeps its slot with `key: null` so it reads as a
// gap. `x`/`baseline` are chart-pixel coords used to order + row-cluster slots.
export interface MarkedSlot {
  glyph: string;
  key: string | null;
  x: number;
  baseline: number;
}

export type GrundtafelState = 'written' | 'original' | 'pending';

export interface Grundtafel {
  styleId: string;
  name: string;
  state: GrundtafelState;
  source: SourceOut | null;
  // Populated only for state === 'written': the marked letters grouped into the
  // chart's own rows (left-to-right, top-to-bottom), gaps for untraced letters.
  rows: MarkedSlot[][];
}

export interface GrundtafelnResult {
  tafeln: Grundtafel[] | null;
  loadError: string | null;
  // True while the boot load is retrying through a Cloud Run cold start.
  waking: boolean;
}

function median(xs: number[]): number {
  if (!xs.length) return 0;
  const s = [...xs].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

// The marked letters grouped into the chart's own rows. Each letter's three
// sibling bboxes share one chart location, so we dedupe to a single slot;
// `key` is the representative glyph_key only when a locked canonical exists
// (else the slot is a gap). Slots are clustered into rows by their baseline
// (so a letter lands in the same row it occupies on the tafel) and ordered
// left-to-right; rows run top-to-bottom. Letters never marked on the chart are
// not slots. Locking is the same public-readiness gate the quiz uses.
function markedRowsOf(bboxes: BboxOut[], glyphs: GlyphSummary[]): MarkedSlot[][] {
  const bm: Record<string, BboxOut> = {};
  for (const b of bboxes) bm[b.glyph_key] = b;
  const gm: Record<string, GlyphSummary> = {};
  for (const g of glyphs) gm[g.glyph_key] = g;

  const slots: MarkedSlot[] = [];
  const heights: number[] = [];
  for (const letter of LETTERS) {
    let rep: BboxOut | null = null;
    let writtenKey: string | null = null;
    for (const position of PREFERRED_POSITIONS) {
      const key = glyphKeyFor(letter, position);
      const b = bm[key];
      if (!b) continue;
      if (!rep) rep = b;
      if (gm[key]?.has_data && b.locked && !writtenKey) writtenKey = key;
    }
    if (!rep) continue;
    heights.push(rep.y1 - rep.y0);
    slots.push({ glyph: letter.glyph, key: writtenKey, x: (rep.x0 + rep.x1) / 2, baseline: rep.baseline_y });
  }
  if (!slots.length) return [];

  // Cluster by baseline: a gap bigger than half a typical letter height starts a
  // new chart row (within a row the baselines are ~equal).
  const threshold = Math.max(1, median(heights) * 0.5);
  slots.sort((a, b) => a.baseline - b.baseline);
  const rows: MarkedSlot[][] = [];
  let row: MarkedSlot[] = [];
  let last: number | null = null;
  for (const s of slots) {
    if (last !== null && s.baseline - last > threshold) {
      rows.push(row);
      row = [];
    }
    row.push(s);
    last = s.baseline;
  }
  if (row.length) rows.push(row);
  for (const r of rows) r.sort((a, b) => a.x - b.x);
  return rows;
}

export function useGrundtafeln(): GrundtafelnResult {
  const [tafeln, setTafeln] = useState<Grundtafel[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [waking, setWaking] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const onRetry = () => {
        if (!cancelled) setWaking(true);
      };
      const retry = { retries: 8, onRetry };
      try {
        // Only the site-wide source can be written today, so its bboxes/glyphs
        // are the only per-source detail we need beyond the registry.
        const [styles, sources, bboxes, glyphs] = await Promise.all([
          getStyles(retry),
          getSources(retry),
          getBboxes(CONFIG.sourceId, retry),
          getGlyphs(CONFIG.sourceId, retry),
        ]);
        if (cancelled) return;
        setWaking(false);

        const styleById: Record<string, StyleOut> = {};
        for (const s of styles) styleById[s.id] = s;
        const charts = sources.filter((s) => s.kind === 'chart');
        const writtenRows = markedRowsOf(bboxes, glyphs);

        const built: Grundtafel[] = STYLE_ORDER.filter((id) => styleById[id]).map((styleId) => {
          const ownCharts = charts.filter((c) => c.style_id === styleId);
          // Prefer the site-wide source for this style, else any chart source.
          const source = ownCharts.find((c) => c.id === CONFIG.sourceId) ?? ownCharts[0] ?? null;
          let state: GrundtafelState;
          if (source?.id === CONFIG.sourceId) state = 'written';
          else if (source) state = 'original';
          else state = 'pending';
          return {
            styleId,
            name: styleLabel(styleId),
            state,
            source,
            rows: state === 'written' ? writtenRows : [],
          };
        });
        setTafeln(built);
      } catch (e) {
        if (cancelled) return;
        setWaking(false);
        // Fixed German copy for the public /tafel; raw exception → console.
        console.error('grundtafeln boot load failed', e);
        setLoadError(de.common.boot.sourceUnreachableDetail);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return { tafeln, loadError, waking };
}
