// The Buchstaben overview — the work list, its toolbar and the gallery behind
// the switch, with ONE place deciding which letters are on screen.
//
// It sits between the view (`LetterView`, which owns the subject) and the two
// bodies: the compact list is the default (V14), the card wall the opt-in. The
// toolbar, the stored-score read and „Neu laden" live here rather than inside
// the gallery, because the list needs the same numbers and a control that
// disappears when the reader switches view would be a trap.
//
// Ansicht, Filter, Sortierung and Seite live in the URL (`shell/listState.ts`)
// and nowhere else: a link out of the Auftragskorb has to open the same view on
// another device, which `localStorage` cannot do.

import RefreshIcon from '@mui/icons-material/Refresh';
import { Box, Button, FormControlLabel, Switch, Typography } from '@mui/material';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { useAdmin } from '@/context/adminState';
import { getTemplateQuality } from '@/lib/api';
import type { QualityData } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { GlyphComparison } from '@/sections/admin/compare/GlyphComparison';
import { LetterList } from '@/sections/admin/letters/LetterList';
import {
  LETTER_LIST_SPEC,
  buildLetterRows,
  letterFilterCounts,
  lettersRankable,
  matchesLetterFilters,
  sortLetterRows,
  type LetterFilter,
  type LetterSort,
} from '@/sections/admin/letters/letterRows';
import { FilterChipRow, ListEmpty, ListPager, ListSortSwitch, ListViewSwitch } from '@/sections/admin/shell/WorkList';
import { useKorbItems } from '@/sections/admin/shell/korbState';
import { korbCountsOf } from '@/sections/admin/shell/korbTargets';
import { clampPage, pageSlice, readListState, writeListState, type ListState } from '@/sections/admin/shell/listState';
import { useWorkbench } from '@/sections/admin/shell/workbenchState';
import { TOUCH_TARGET } from '@/styles/hitArea';

export function LetterOverview({ onPick }: { onPick: (glyphKey: string) => void }) {
  const [params, setParams] = useSearchParams();
  const { source, sourceId, glyphsByKey, bboxesByKey, laufformKeys, cropCacheBust, refreshCrop } = useAdmin();
  const workbench = useWorkbench();
  const korbItems = useKorbItems();
  const t = de.admin.liste;

  // Where a page change scrolls back to.
  const topRef = useRef<HTMLDivElement | null>(null);

  const [reloadKey, setReloadKey] = useState(0);
  // „Überlagern" is a rendering mode of the tile, not work-list state — it
  // stays component state and out of the URL (a Korb link that reopened an
  // overlay would be answering a question nobody asked).
  const [overlay, setOverlay] = useState(false);
  const [quality, setQuality] = useState<Map<string, QualityData | null> | null>(null);

  // „Neu laden" has to move the version the render cache is keyed on, or the
  // written faces answer from the entries they already hold — the button would
  // refetch the scores and remount the cards while showing the same geometry.
  // `refreshCrop` is that version (the admin-wide crop/canonical stamp), so the
  // whole workbench reloads consistently rather than this view alone.
  const reload = useCallback(() => {
    refreshCrop();
    setReloadKey((k) => k + 1);
  }, [refreshCrop]);

  // Drop the previous source's scores DURING RENDER instead of in the effect
  // below — React's "adjusting state when a prop changes"
  // (react-hooks/set-state-in-effect). The guard carries the effect's inputs, so
  // no row shows another source's score chip for a frame.
  const scoreKey = `${sourceId} ${cropCacheBust} ${reloadKey}`;
  const [scoresShownFor, setScoresShownFor] = useState(scoreKey);
  if (scoresShownFor !== scoreKey) {
    setScoresShownFor(scoreKey);
    setQuality(null);
  }

  // The stored score of every template in ONE admin read. Only variant 0 is
  // kept: a Laufform row inherits the chart row's trace_meta, so its stamped
  // score is a COPY of the chart form's — never a measurement of the median
  // geometry, and showing it as one would be a lie.
  useEffect(() => {
    let cancelled = false;
    getTemplateQuality(sourceId, { retries: 1 })
      .then((rows) => {
        if (cancelled) return;
        setQuality(new Map(rows.filter((r) => r.variant === 0).map((r) => [r.glyph_key, r.quality])));
      })
      // Admin-gated: a 401 (or a source without scores) simply means no score
      // chips — the overview itself keeps working.
      .catch(() => {
        if (!cancelled) setQuality(new Map());
      });
    return () => {
      cancelled = true;
    };
  }, [sourceId, cropCacheBust, reloadKey]);

  // Memoised on the params object, which `useSearchParams` keeps stable per
  // location: `readListState` builds a fresh `filters` array, and an unmemoised
  // one would make every memo below it recompute on every render — and with
  // them the `tiles` array the gallery's batch prefetch is keyed on.
  const state = useMemo(() => readListState<LetterFilter, LetterSort>(params, LETTER_LIST_SPEC), [params]);
  // List state REPLACES, so the back button keeps walking the inspection
  // history `focus.ts` promises instead of a log of every filter click. The
  // subject still pushes — that is a different question and a different hop.
  const update = (next: Partial<ListState<LetterFilter, LetterSort>>) =>
    setParams(writeListState(params, next, LETTER_LIST_SPEC), { replace: true });

  // Both evidence layers must be able to say „I do not know yet" instead of
  // answering with a zero. The OCCURRENCE layer is public and loads with the
  // view; until it has answered, a row has no count to print — and after a
  // failed read it has none either, which is not the same as „none exist".
  const occurrencesKnown = !workbench.loading && !workbench.error;

  const authoredKeys = useMemo(
    () => Object.keys(glyphsByKey).filter((key) => glyphsByKey[key]?.has_data === true),
    [glyphsByKey],
  );
  const korbByGlyph = useMemo(() => korbCountsOf(korbItems)?.byGlyph ?? null, [korbItems]);

  const rows = useMemo(
    () =>
      buildLetterRows({
        authoredKeys,
        bboxesByKey,
        laufformKeys,
        instancesByKey: workbench.instancesByKey,
        quality,
        korbByGlyph,
        occurrencesKnown,
      }),
    [authoredKeys, bboxesByKey, laufformKeys, workbench.instancesByKey, quality, korbByGlyph, occurrencesKnown],
  );

  const counts = useMemo(() => letterFilterCounts(rows), [rows]);
  const selected = useMemo(
    () => sortLetterRows(rows.filter((row) => matchesLetterFilters(row, state.filters)), state.sort),
    [rows, state.filters, state.sort],
  );
  const page = clampPage(state.page, selected.length);
  const shown = useMemo(() => pageSlice(selected, state.page), [selected, state.page]);
  // Memoised because the gallery's batch prefetch lists it in its effect deps —
  // a fresh array per render would re-run the effect on every overlay toggle.
  const tiles = useMemo(
    () => shown.map((row) => ({ key: row.glyphKey, letterGlyph: row.letterGlyph, quality: row.quality })),
    [shown],
  );

  // A page the selection cannot fill is corrected at render time — and the URL
  // is corrected with it, or a shared link would describe a page the view is
  // not on. Only once the selection HAS rows: before the first read it is empty
  // for everyone, and rewriting then would eat a deep link's `seite=`.
  useEffect(() => {
    if (selected.length > 0 && page !== state.page) {
      setParams(writeListState(params, { page }, LETTER_LIST_SPEC), { replace: true });
    }
  }, [selected.length, page, state.page, params, setParams]);

  // The statistics layer on top of the occurrences is admin-gated and loads on
  // its own: while it is in flight, has no hand to key on or came back 401, an
  // empty sketch face must not claim „noch keine Statistik" — that would report
  // a missing measurement where there is only a missing READ. The occurrence
  // layer is checked FIRST: the hand is derived from those rows, so „no hand"
  // is only meaningful once they are in.
  const statsHint = workbench.error
    ? de.admin.shell.evidenceError
    : !occurrencesKnown || workbench.letterStats.status === 'loading'
      ? de.admin.werkbank.statsLoading
      : workbench.letterStats.status === 'no-occurrences'
        ? de.admin.werkbank.statsNoOccurrences
        : workbench.letterStats.status === 'no-hand'
          ? de.admin.werkbank.statsNoHand
          : workbench.letterStats.status === 'unavailable'
            ? de.admin.werkbank.statsUnavailable
            : workbench.letterStats.layerEmpty
              ? de.admin.compare.noAggregateLayer
              : de.admin.compare.noAggregateShort;

  // The hand the numbers belong to — an overview that pools occurrences across
  // two writers and shows ONE hand's median has to say so (the lens blocks name
  // their hand for the same reason).
  const handNote = workbench.handId ? fmt(de.admin.werkbank.statsHand, { hand: workbench.handId }) : null;
  // `handsMixed` is not on the context itself — it travels with the stats
  // context, which is where the derivation lives.
  const mixedNote =
    workbench.letterStats.handsMixed && workbench.handId
      ? fmt(de.admin.werkbank.statsMixedHands, { hand: workbench.handId })
      : null;

  if (!source) return null;

  const filterChips = LETTER_LIST_SPEC.filters.map((token) => ({
    token,
    label: de.admin.letters.filters[token],
    count: counts[token],
    active: state.filters.includes(token),
  }));
  const toggleFilter = (token: string) => {
    const filter = token as LetterFilter;
    update({
      filters: state.filters.includes(filter)
        ? state.filters.filter((f) => f !== filter)
        : [...state.filters, filter],
    });
  };
  const rankable = lettersRankable(rows);

  return (
    // No own page padding/scroll container: since the redesign this block sits
    // inside the Buchstaben view, which owns both.
    <Box ref={topRef}>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mb: 2 }}>
        <FilterChipRow chips={filterChips} onToggle={toggleFilter} label={t.filterLabel} />
        <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <ListSortSwitch
            sort={state.sort}
            label={de.admin.compare.sortLabel}
            options={[
              { token: 'alphabet', label: de.admin.compare.sortAlpha },
              {
                token: 'schlechteste',
                label: de.admin.compare.sortWorst,
                disabled: !rankable,
                disabledHint: de.admin.compare.sortWorstUnavailable,
              },
            ]}
            onChange={(token) => update({ sort: token as LetterSort })}
          />
          <ListViewSwitch view={state.view} onChange={(view) => update({ view })} />
          <Typography variant="caption" color="text.secondary">
            {/* With a filter on, the page size is the wrong number: „24 von 63"
                says nothing about how many rows the chips actually selected,
                and the per-chip counts deliberately cannot answer it either. */}
            {state.filters.length > 0
              ? fmt(t.counterFiltered, { shown: shown.length, selected: selected.length, total: rows.length })
              : fmt(t.counter, { shown: shown.length, total: rows.length })}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: { sm: 'auto' } }}>
            <FormControlLabel
              control={<Switch size="small" checked={overlay} onChange={(e) => setOverlay(e.target.checked)} />}
              label={<Typography variant="caption">{de.admin.compare.overlayToggle}</Typography>}
            />
            {/* The one control that came up from the gallery's own toolbar —
                and the sweep's first look at this route found it 32.5 px tall
                (design-system.md §9.3 wants 44). */}
            <Button
              size="small"
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={reload}
              sx={{ minHeight: TOUCH_TARGET }}
            >
              {de.admin.compare.reload}
            </Button>
          </Box>
        </Box>
        {(handNote || mixedNote) && (
          <Box sx={{ minWidth: 0 }}>
            {handNote && (
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                {handNote}
              </Typography>
            )}
            {mixedNote && (
              <Typography variant="caption" color="warning.main" sx={{ display: 'block' }}>
                {mixedNote}
              </Typography>
            )}
          </Box>
        )}
      </Box>

      {shown.length === 0 ? (
        // Two different silences: a source with no authored letter at all, and
        // a filter that happens to match none of them.
        <ListEmpty
          filtered={rows.length > 0}
          emptyText={de.admin.compare.empty}
          onReset={() => update({ filters: [] })}
        />
      ) : state.view === 'liste' ? (
        <LetterList
          rows={shown}
          sourceId={sourceId}
          cropCacheBust={cropCacheBust}
          reloadKey={reloadKey}
          overlay={overlay}
          aggregatesByKey={workbench.aggregatesByKey}
          instancesByKey={workbench.instancesByKey}
          statsHint={statsHint}
          occurrencesKnown={occurrencesKnown}
          onPick={onPick}
        />
      ) : (
        <GlyphComparison
          tiles={tiles}
          sourceId={sourceId}
          cropCacheBust={cropCacheBust}
          reloadKey={reloadKey}
          overlay={overlay}
          quality={quality}
          aggregatesByKey={workbench.aggregatesByKey}
          instancesByKey={workbench.instancesByKey}
          statsHint={statsHint}
          occurrencesKnown={occurrencesKnown}
          pageKey={String(page)}
          onPick={onPick}
        />
      )}

      <Box sx={{ mt: 2 }}>
        {/* The pager sits under the list, so a page change has to take the
            reader back up with it: consecutive pages are near-identical in
            height, and `scrollTop` would survive the swap intact — page 2 would
            open at its LAST row. */}
        <ListPager
          page={page}
          total={selected.length}
          onChange={(next) => {
            update({ page: next });
            topRef.current?.scrollIntoView?.({ block: 'start' });
          }}
        />
      </Box>
    </Box>
  );
}
