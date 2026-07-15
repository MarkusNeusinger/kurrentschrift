// The quiz's own slim boot load — the data the reading drill actually gates
// on, WITHOUT mounting the AdminProvider. The quiz used to ride the pinned
// admin context and thereby fetch every bbox's mask/ink/patch JSONB blobs (the
// crop-editing payload) just to read `locked`/`split`; this hook fetches the
// pinned public source, the template summaries (`has_data`) and the flag-only
// `/bboxes/status` list instead. Same cold-start retry + boot states as
// useGrundtafeln.

import { useEffect, useState } from 'react';

import { CONFIG } from '@/global-config';
import { getBboxStatuses, getGlyphs, getSource } from '@/lib/api';
import type { BboxStatusOut, GlyphSummary, SourceOut } from '@/lib/api';
import { de } from '@/locales';

export interface QuizSourceData {
  source: SourceOut | null;
  bboxesByKey: Record<string, BboxStatusOut>;
  glyphsByKey: Record<string, GlyphSummary>;
  loadError: string | null;
  // True while the boot load is retrying through a Cloud Run cold start.
  waking: boolean;
}

export function useQuizSource(): QuizSourceData {
  const [source, setSource] = useState<SourceOut | null>(null);
  const [bboxesByKey, setBboxesByKey] = useState<Record<string, BboxStatusOut>>({});
  const [glyphsByKey, setGlyphsByKey] = useState<Record<string, GlyphSummary>>({});
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
        const [src, statuses, glyphs] = await Promise.all([
          getSource(CONFIG.sourceId, retry),
          getBboxStatuses(CONFIG.sourceId, retry),
          getGlyphs(CONFIG.sourceId, retry),
        ]);
        if (cancelled) return;
        setWaking(false);
        setBboxesByKey(Object.fromEntries(statuses.map((s) => [s.glyph_key, s])));
        setGlyphsByKey(Object.fromEntries(glyphs.map((g) => [g.glyph_key, g])));
        setSource(src);
      } catch (e) {
        if (cancelled) return;
        setWaking(false);
        // Fixed German copy for the public page; raw exception → console.
        console.error('quiz source boot load failed', e);
        setLoadError(de.common.boot.sourceUnreachableDetail);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return { source, bboxesByKey, glyphsByKey, loadError, waking };
}
