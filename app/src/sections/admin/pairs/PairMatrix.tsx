// The Übergänge overview — every two-letter combination of one chosen letter,
// as an Arbeitsliste (V14). Since this PR the default cell is a COUNTER rather
// than a mini render: how often the plates wrote the combination, what the
// library stores for it, how many basket items point at it. `ansicht=galerie`
// brings the composed cells back, and the join detail keeps them as its
// collapsed cross-check.
//
// Two things moved in with the list. The anchor letter now lives in the URL
// (`l=`) instead of in component state, which fixes „Alle Kombinationen
// ansehen": that button navigated to `/admin/uebergaenge?l=a`, the half pair
// was read as no focus at all, and the matrix opened on whatever letter came
// first — the letter the reader had asked for was dropped between two lines of
// code. And the override list may now say „I do not know": it used to answer a
// failed admin read with an empty Map, which every cell then reported as
// „generiert".
//
// A read-only QA surface throughout: a cell click focuses the join, where the
// measurements, the statistics and — last — the pair editor live.

import { Alert, Box, ButtonBase, Typography } from '@mui/material';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { useAdmin } from '@/context/adminState';
import { glyphKeyFor, LETTERS } from '@/domain/glyphs';
import { getPairs } from '@/lib/api';
import type { GlyphPairOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { PairCellGrid } from '@/sections/admin/pairs/PairCells';
import { pairRowsByKeys } from '@/sections/admin/pairs/pairRow';
import {
  PAIR_LIST_SPEC,
  authoredLetters,
  buildPairRows,
  matchesPairFilters,
  pairFilterCounts,
  pairsRankable,
  sortPairRows,
  type PairFilter,
  type PairRow,
  type PairSort,
} from '@/sections/admin/pairs/pairRows';
import { FilterChipRow, ListEmpty, ListSortSwitch, ListViewSwitch } from '@/sections/admin/shell/WorkList';
import { FOCUS_PARAMS } from '@/sections/admin/shell/focus';
import { useKorbItems } from '@/sections/admin/shell/korbState';
import { korbCountsOf } from '@/sections/admin/shell/korbTargets';
import { readListState, writeListState, type ListState } from '@/sections/admin/shell/listState';
import { useWorkbench } from '@/sections/admin/shell/workbenchState';
import { TOUCH_TARGET } from '@/styles/hitArea';
import { garamond } from '@/styles/paper';

export function PairMatrix({
  // The letter the grid opens on. In the overview this is the URL's `l=`, in
  // the detail the focused join's left key.
  activeGlyphKey,
  onPickPair,
  // Bumped by the caller after a save in the pair editor, so the stored state
  // per cell refreshes without a reload.
  refreshKey = 0,
  // The collapsed copy under a focused join: its own anchor, the composed
  // cells, no toolbar — and nothing of it in the URL, because it is a
  // sub-block of another view's detail rather than an overview of its own.
  embedded = false,
}: {
  activeGlyphKey?: string | null;
  onPickPair: (leftKey: string, rightKey: string) => void;
  refreshKey?: number;
  embedded?: boolean;
}) {
  const [params, setParams] = useSearchParams();
  const { source, sourceId, glyphsByKey } = useAdmin();
  const workbench = useWorkbench();
  const korbItems = useKorbItems();
  const t = de.admin.pairs;

  const authored = useMemo(
    () => authoredLetters(LETTERS, (glyphKey) => glyphsByKey[glyphKey]?.has_data === true),
    [glyphsByKey],
  );
  const pickable = useMemo(() => [...authored.lower, ...authored.upper], [authored]);

  // The embedded copy keeps its own anchor; the overview's is the URL's.
  const [picked, setPicked] = useState<string | null>(null);
  const anchorKey = embedded ? (picked ?? activeGlyphKey ?? null) : (activeGlyphKey ?? null);
  const anchor = pickable.find((letter) => glyphKeyFor(letter) === anchorKey) ?? pickable[0];

  // Stored overrides incl. unapproved drafts (the admin fetch carries the auth
  // header). `null` until the read answers — and after a failed one: „kein
  // Override" is a claim about the library, and this read is admin-gated.
  const [overrideRows, setOverrideRows] = useState<Map<string, GlyphPairOut> | null>(null);
  // Retire the previous answer DURING RENDER rather than in the effect below —
  // React's "adjusting state when a prop changes"
  // (react-hooks/set-state-in-effect). The guard carries the effect's inputs,
  // so no cell reports the pre-save state for one frame after an override was
  // written, and none reports the previous source's at all.
  const overrideKey = `${sourceId} ${refreshKey}`;
  const [overridesFor, setOverridesFor] = useState(overrideKey);
  if (overridesFor !== overrideKey) {
    setOverridesFor(overrideKey);
    setOverrideRows(null);
  }
  useEffect(() => {
    let cancelled = false;
    getPairs(sourceId, { all: true }, { retries: 1 })
      .then((rows) => {
        if (!cancelled) setOverrideRows(pairRowsByKeys(rows));
      })
      .catch(() => {
        if (!cancelled) setOverrideRows(null);
      });
    return () => {
      cancelled = true;
    };
  }, [sourceId, refreshKey]);

  // Same quiet absence on the public layer: while the occurrence bundle is in
  // flight or has failed, no cell claims „keine Vorkommen".
  const occurrencesKnown = !workbench.loading && !workbench.error;
  const korbByPair = useMemo(() => korbCountsOf(korbItems)?.byPair ?? null, [korbItems]);

  const rows = useMemo(
    () =>
      anchor
        ? buildPairRows({
            anchor,
            lower: authored.lower,
            upper: authored.upper,
            pairsByKey: occurrencesKnown ? workbench.pairsByKey : null,
            overrideRows,
            korbByPair,
          })
        : { asFirst: [], asSecond: [] },
    [anchor, authored, occurrencesKnown, workbench.pairsByKey, overrideRows, korbByPair],
  );

  const urlState = useMemo(() => readListState<PairFilter, PairSort>(params, PAIR_LIST_SPEC), [params]);
  // The collapsed copy reads none of it — it is not the surface the URL
  // describes, and inheriting the overview's chips would silently hide cells
  // from a cross-check the reader opened to see everything.
  const state: ListState<PairFilter, PairSort> = embedded
    ? { view: 'galerie', filters: [], text: '', sort: 'alphabet', status: null, tab: null, page: 1 }
    : urlState;

  // No pager here (decided in this PR): the anchor letter already cuts the
  // matrix to ~60 cells, and a grid broken at 24 is harder to read, not
  // easier. So every write pins page 1 rather than carrying a `seite=` that
  // nothing on this surface can act on.
  const update = (next: Partial<ListState<PairFilter, PairSort>>) =>
    setParams(writeListState(params, { ...next, page: 1 }, PAIR_LIST_SPEC), { replace: true });

  // The anchor REPLACES too. It selects which slice of the grid is on screen,
  // which is list state in everything but its parameter name — pushing it
  // would make the back button walk 30 letters instead of the inspection
  // history `focus.ts` promises.
  const pickAnchor = (glyphKey: string) => {
    if (embedded) {
      setPicked(glyphKey);
      return;
    }
    const next = new URLSearchParams(params);
    next.set(FOCUS_PARAMS.left, glyphKey);
    // A new anchor is not a new join — the right half would otherwise pair the
    // fresh letter with the previous one's partner.
    next.delete(FOCUS_PARAMS.right);
    setParams(next, { replace: true });
  };

  const counts = useMemo(() => pairFilterCounts([...rows.asFirst, ...rows.asSecond]), [rows]);
  const pendingFilters = state.filters.some((token) => counts[token] === null);
  const select = useCallback(
    (list: PairRow[]) => sortPairRows(list.filter((row) => matchesPairFilters(row, state.filters)), state.sort),
    [state.filters, state.sort],
  );
  const asFirst = useMemo(() => select(rows.asFirst), [select, rows.asFirst]);
  const asSecond = useMemo(() => select(rows.asSecond), [select, rows.asSecond]);
  const shown = asFirst.length + asSecond.length;
  const total = rows.asFirst.length + rows.asSecond.length;

  if (!source) return null;
  if (pickable.length === 0) return <Alert severity="info">{t.empty}</Alert>;

  const filterChips = PAIR_LIST_SPEC.filters.map((token) => ({
    token,
    label: t.filters[token],
    count: counts[token],
    active: state.filters.includes(token),
  }));
  const toggleFilter = (token: string) => {
    const filter = token as PairFilter;
    update({
      filters: state.filters.includes(filter)
        ? state.filters.filter((f) => f !== filter)
        : [...state.filters, filter],
    });
  };

  return (
    // A block inside the Übergänge view: that view owns padding and scrolling.
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
        <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
          {t.pickLetter}
        </Typography>
        {pickable.map((letter) => {
          const key = glyphKeyFor(letter);
          const active = anchor ? glyphKeyFor(anchor) === key : false;
          return (
            <ButtonBase
              key={key}
              onClick={() => pickAnchor(key)}
              aria-pressed={active}
              aria-label={fmt(t.pickLetterFor, { key })}
              sx={{
                fontFamily: garamond,
                fontSize: 20,
                lineHeight: 1,
                // §9.3: the letter bar is the densest control row of the admin,
                // and a neighbour would win an invisible hit area's pixels.
                minWidth: TOUCH_TARGET,
                minHeight: TOUCH_TARGET,
                px: 1,
                borderRadius: 1,
                border: 1,
                borderColor: active ? 'primary.main' : 'divider',
                bgcolor: active ? 'action.selected' : 'transparent',
              }}
            >
              {letter.glyph}
            </ButtonBase>
          );
        })}
      </Box>

      {!embedded && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mb: 2 }}>
          <FilterChipRow chips={filterChips} onToggle={toggleFilter} label={de.admin.liste.filterLabel} />
          <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
            <ListSortSwitch
              sort={state.sort}
              label={de.admin.compare.sortLabel}
              options={[
                { token: 'alphabet', label: de.admin.compare.sortAlpha },
                {
                  token: 'vorkommen',
                  label: t.sortOccurrences,
                  disabled: !pairsRankable([...rows.asFirst, ...rows.asSecond]),
                  disabledHint: t.sortOccurrencesUnavailable,
                },
              ]}
              onChange={(token) => update({ sort: token as PairSort })}
            />
            <ListViewSwitch view={state.view} onChange={(view) => update({ view })} />
            <Typography variant="caption" color="text.secondary">
              {/* Two numbers, not the lists' three: this grid has no pager, so
                  „wieviel ist auf dem Schirm" and „wieviel ist gewählt" are the
                  same number by construction and printing both read as a
                  tautology. */}
              {pendingFilters
                ? null
                : state.filters.length > 0
                  ? fmt(de.admin.liste.counterSelected, { selected: shown, total })
                  : fmt(de.admin.liste.counter, { shown, total })}
            </Typography>
          </Box>
          {/* Said ONCE for the whole grid rather than in every cell: which
              counter is missing is the same answer 60 times over. */}
          {!occurrencesKnown && (
            <Typography variant="caption" color="text.disabled">
              {de.admin.compare.occurrencesUnknown}
            </Typography>
          )}
          {overrideRows === null && (
            <Typography variant="caption" color="text.disabled">
              {t.overridesUnknown}
            </Typography>
          )}
        </Box>
      )}

      {anchor && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {pendingFilters || shown === 0 ? (
            <ListEmpty
              filtered={total > 0}
              pending={pendingFilters}
              emptyText={t.empty}
              onReset={() => update({ filters: [] })}
            />
          ) : (
            <>
              {asFirst.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>
                    {fmt(t.asFirst, { glyph: anchor.glyph })}
                  </Typography>
                  <PairCellGrid rows={asFirst} sourceId={sourceId} view={state.view} onPick={onPickPair} />
                </Box>
              )}
              {asSecond.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>
                    {fmt(t.asSecond, { glyph: anchor.glyph })}
                  </Typography>
                  <PairCellGrid rows={asSecond} sourceId={sourceId} view={state.view} onPick={onPickPair} />
                </Box>
              )}
            </>
          )}
        </Box>
      )}
    </Box>
  );
}
