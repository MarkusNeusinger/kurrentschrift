// The data half of SpecimenStrip: the page fetches the render payloads of ALL
// its specimens in one batch (renderCache → /write/glyphs?keys=…) as soon as
// the section comes near, and hands the map to every strip — no cell fetches
// on its own. Kept out of the component file so fast refresh keeps working
// (a file that exports a component must export nothing else).

import { useEffect, useMemo, useState } from 'react';

import { CONFIG } from '@/global-config';
import { fetchRenderGlyphs, type GlyphRenderData } from '@/lib/api';

/** One specimen: the public source's glyph_key + the Antiqua label under it. */
export interface Specimen {
  readonly key: string;
  readonly label: string;
}

/** Render payloads by glyph_key: a glyph maps to null when the source has no
 * canonical for it; every key is absent when the engine could not be reached. */
export type SpecimenPayloads = ReadonlyMap<string, GlyphRenderData | null>;

/** Fetch the payloads of `keys` in one batch once `near` turns true. `null`
 * while nothing has been fetched yet. Pass a memoised `keys` array — a fresh
 * array per render would refetch. */
export function useSpecimenPayloads(keys: readonly string[], near: boolean): SpecimenPayloads | null {
  const wanted = useMemo(() => [...new Set(keys)], [keys]);
  const [payloads, setPayloads] = useState<SpecimenPayloads | null>(null);
  useEffect(() => {
    if (!near || wanted.length === 0) return undefined;
    let cancelled = false;
    fetchRenderGlyphs(CONFIG.sourceId, wanted)
      .then((m) => {
        if (!cancelled) setPayloads(m);
      })
      .catch(() => {
        if (!cancelled) setPayloads(new Map()); // unreachable engine: the strips withdraw
      });
    return () => {
      cancelled = true;
    };
  }, [near, wanted]);
  return payloads;
}

/** Whether a strip of `specimens` can show anything: true while the batch is
 * still in flight (the frame holds its space), then true iff one of its
 * glyphs has a payload. Lets a caller drop a caption that says "written live"
 * when nothing is. */
export function anyWritable(specimens: readonly Specimen[], payloads: SpecimenPayloads | null): boolean {
  return !payloads || specimens.some((s) => payloads.get(s.key));
}
