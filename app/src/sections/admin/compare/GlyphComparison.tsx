// The GALLERY of the Buchstaben overview — every letter of the current page as
// four faces, one card under the other. Since V14 it is the opt-in
// (`?ansicht=galerie`); the default is the compact work list beside it
// (`letters/LetterList.tsx`), because a card wall of ten thousand pixels is a
// poor first answer to „welcher Buchstabe braucht Arbeit?".
//
// What a card shows and why: `CompareCard.tsx`. What this file still owns is
// exactly one thing the card cannot do for itself — the two BATCH render
// requests that warm both written faces of the whole page at once, instead of
// one request per face per card.
//
// Everything else moved up into the overview (`letters/LetterOverview.tsx`):
// the toolbar, the sort, the stored-score read and the reload. The grid is
// given its rows already filtered, sorted and paged — so „welche Karten" is one
// decision in one place, the same one the list obeys.

import { Box } from '@mui/material';
import { useEffect } from 'react';

import { fetchRenderGlyphs } from '@/lib/api';
import type { AggregateOut, InstanceOut, QualityData } from '@/lib/api';
import { CompareCard } from '@/sections/admin/compare/CompareCard';

// The Laufform is stored as this template variant (core/database LAUFFORM_VARIANT).
const LAUFFORM_VARIANT = 100;
// The write endpoint takes at most 80 keys per request (api/routers/write.py);
// stay clear of the limit so a fully authored source (letters + digits +
// punctuation + ligatures) still prefetches in whole batches.
const PREFETCH_CHUNK = 60;

export type CompareTile = {
  key: string;
  letterGlyph: string;
  quality: QualityData | null;
};

export function GlyphComparison({
  tiles,
  sourceId,
  cropCacheBust,
  reloadKey,
  overlay,
  quality,
  aggregatesByKey,
  instancesByKey,
  statsHint,
  occurrencesKnown,
  pageKey,
  onPick,
}: {
  // Already filtered, sorted and paged by the overview.
  tiles: CompareTile[];
  sourceId: string;
  cropCacheBust: number;
  reloadKey: number;
  overlay: boolean;
  // null while the stored-score read has not answered — a card must not claim
  // „kein Score" before it has.
  quality: Map<string, QualityData | null> | null;
  aggregatesByKey: Map<string, AggregateOut>;
  instancesByKey: Map<string, InstanceOut[]>;
  statsHint: string;
  occurrencesKnown: boolean;
  // Part of every card key, because `useInView` is one-shot: a letter that
  // moves between pages under a new sort would otherwise inherit the previous
  // page's „already seen" flag and paint without ever being scrolled to.
  pageKey: string;
  onPick?: (glyphKey: string) => void;
}) {
  // Both written faces of the whole PAGE in two batch requests instead of one
  // request per face per card. The components then read the same cache and
  // paint without a round trip of their own. Following the page rather than the
  // whole alphabet is the cheaper half of the pager: the render cache is shared
  // with the list's expanded rows, so nothing is fetched twice.
  useEffect(() => {
    if (tiles.length === 0) return;
    const keys = tiles.map((t) => t.key);
    for (let i = 0; i < keys.length; i += PREFETCH_CHUNK) {
      const chunk = keys.slice(i, i + PREFETCH_CHUNK);
      for (const variant of [0, LAUFFORM_VARIANT]) {
        // Fire and forget: every consumer awaits the same cache entry, and a
        // failed batch is retried by the component that needs it.
        void fetchRenderGlyphs(sourceId, chunk, variant, cropCacheBust).catch(() => {});
      }
    }
  }, [tiles, sourceId, cropCacheBust, reloadKey]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 1400 }}>
      {tiles.map((t) => (
        <CompareCard
          // Remount on a re-derive or „Neu laden": the per-card „this letter has
          // no Laufform" answer is a one-way flag, and an apply (or a fresh
          // trace) can make it wrong — a new key throws it away instead of
          // resetting state from an effect.
          key={`${t.key}:${cropCacheBust}:${reloadKey}:${pageKey}`}
          glyphKey={t.key}
          letterGlyph={t.letterGlyph}
          sourceId={sourceId}
          cropCacheBust={cropCacheBust}
          reloadKey={reloadKey}
          overlay={overlay}
          aggregate={aggregatesByKey.get(t.key)}
          occurrences={instancesByKey.get(t.key) ?? []}
          // undefined = the score read has not answered yet; null = it answered
          // and this row carries none.
          quality={quality === null ? undefined : t.quality}
          statsHint={statsHint}
          occurrencesKnown={occurrencesKnown}
          onPick={onPick}
        />
      ))}
    </Box>
  );
}
