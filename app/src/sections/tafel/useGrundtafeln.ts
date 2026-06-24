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
import { styleLabel } from '@/locales/de/common';

// Canonical teaching order (oldest → newest), matching the landing + Schriftkunde.
const STYLE_ORDER = ['kurrent', 'suetterlin', 'offenbacher'] as const;

// One representative position per letter: prefer the medial (body) form, falling
// back to initial then final — the same rule the old single-source Tafel used.
const PREFERRED_POSITIONS: Position[] = ['medial', 'initial', 'final'];

export interface WrittenLetter {
  key: string; // representative glyph_key with a locked canonical
  glyph: string; // the rendered character (ſ, A, ch, …)
}

export type GrundtafelState = 'written' | 'original' | 'pending';

export interface Grundtafel {
  styleId: string;
  name: string;
  state: GrundtafelState;
  source: SourceOut | null;
  // Populated only for state === 'written' (one entry per finished letter).
  letters: WrittenLetter[];
}

export interface GrundtafelnResult {
  tafeln: Grundtafel[] | null;
  loadError: string | null;
  // True while the boot load is retrying through a Cloud Run cold start.
  waking: boolean;
}

// Every letter that is both locked (the admin's "finished" marker) AND owns a
// traced canonical, deduped to one entry per letter (its three positions usually
// share one authored form), ordered by the alphabet registry. Locking is the
// same public-readiness gate the quiz uses, so the Tafel never surfaces a
// half-calibrated form.
function writtenLetters(bboxes: BboxOut[], glyphs: GlyphSummary[]): WrittenLetter[] {
  const bm: Record<string, BboxOut> = {};
  for (const b of bboxes) bm[b.glyph_key] = b;
  const gm: Record<string, GlyphSummary> = {};
  for (const g of glyphs) gm[g.glyph_key] = g;
  const out: WrittenLetter[] = [];
  for (const letter of LETTERS) {
    for (const position of PREFERRED_POSITIONS) {
      const key = glyphKeyFor(letter, position);
      if (gm[key]?.has_data && bm[key]?.locked) {
        out.push({ key, glyph: letter.glyph });
        break;
      }
    }
  }
  return out;
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
        const written = writtenLetters(bboxes, glyphs);

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
            letters: state === 'written' ? written : [],
          };
        });
        setTafeln(built);
      } catch (e) {
        if (cancelled) return;
        setWaking(false);
        setLoadError(String(e));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return { tafeln, loadError, waking };
}
