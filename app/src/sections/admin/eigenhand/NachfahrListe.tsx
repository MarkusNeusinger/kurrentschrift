// Die Nachfahr-Liste — the Eigenhand's work list, one row per written word BOX.
//
// The surface the plan called „der Filter ‚Nachfahren'" and that turned out to
// be a whole list: Phase 1 put the work-list machinery into the three Vorlage
// overviews only, and the strip panel orders per FASSUNG by Streifen-Befund, so
// there was nothing to filter (`admin-redesign.md` §7.2, corrected 2026-09-20).
// This is that machinery with the KASTEN as its subject — same `listState.ts`
// axes, same `WorkList.tsx` parts, same rules about what a missing read may
// claim.
//
// ONE request for the whole hand (`GET /eigenhand/pfade/{hand}`): the state of
// every box without a single point of a Bahn. Answering the same question
// through the per-Fassung path read costs one request per (strip, Fassung) and
// drags a few thousand points per word along — which is why that read exists.
//
// It shares `?reiter=streifen` with the strip gallery and is chosen with the
// same Liste/Galerie switch every overview has (V14, V2 — „keine eigene
// Unterroute"). The two filters of the page belong to different surfaces, and
// that is stated rather than papered over: the word search narrows both, the
// coverage ITEM only the gallery, because a box row knows its word and not the
// items that word covers.

import { Box, Button, CircularProgress, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { InfoHint } from '@/components/InfoHint';
import { useRovingList } from '@/hooks/useRovingList';
import { getEigenhandPfadBoxes } from '@/lib/api';
import type { EigenhandPfadFassung } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { NachfahrRow } from '@/sections/admin/eigenhand/NachfahrRow';
import {
  BOX_FILTERS,
  BOX_STATUSES,
  STRIP_BOX_LIST_SPEC,
  boxFilterCounts,
  buildStripBoxRows,
  matchesStripBoxFilters,
  sortStripBoxRows,
  stripBoxTally,
  stripBoxesRankable,
  type BoxFilter,
  type BoxSort,
  type BoxStatus,
} from '@/sections/admin/eigenhand/stripBoxRows';
import { apiErrorText } from '@/sections/admin/shell/apiErrorText';
import type { ApiErrorText } from '@/sections/admin/shell/apiErrorText';
import { ErrorText } from '@/sections/admin/shell/ErrorText';
import { useFileMark, useKorbItems } from '@/sections/admin/shell/korbState';
import { korbCountsOf } from '@/sections/admin/shell/korbTargets';
import { clampPage, pageSlice, readListState, writeListState, type ListState } from '@/sections/admin/shell/listState';
import { stripBoxSpecimen } from '@/sections/admin/shell/focus';
import { FilterChipRow, ListEmpty, ListPager } from '@/sections/admin/shell/WorkList';
import { TOUCH_TARGET } from '@/styles/hitArea';
import { paper } from '@/styles/paper';

export function NachfahrListe({
  hand,
  /** The panel's word search (`?wort=`) — it narrows this list too. */
  wort,
  /** The coverage item filter (`?item=`), which only the gallery can answer. */
  item,
  /** Switch the surface back to the gallery — the way out of that mismatch. */
  onShowGalerie,
}: {
  hand: string;
  wort: string;
  item: string | null;
  onShowGalerie: () => void;
}) {
  const t = de.admin.eigenhand.nachfahren;
  const [params, setParams] = useSearchParams();
  const [fassungen, setFassungen] = useState<EigenhandPfadFassung[] | null>(null);
  const [error, setError] = useState<ApiErrorText | null>(null);
  const korbItems = useKorbItems();
  const fileMark = useFileMark();
  // Which rows are open — component state on purpose, the reason `LetterList`
  // gives: a link carries what the reader is looking FOR, not where they
  // happen to be looking.
  const [expanded, setExpanded] = useState<ReadonlySet<string>>(() => new Set());
  const roving = useRovingList();

  // Drop the previous hand's boxes DURING RENDER — React's "adjusting state
  // when a prop changes". Without it the new hand's name would stand over the
  // old hand's Kästen until the request lands.
  const [shownFor, setShownFor] = useState(hand);
  if (shownFor !== hand) {
    setShownFor(hand);
    setFassungen(null);
    setError(null);
  }

  useEffect(() => {
    let cancelled = false;
    getEigenhandPfadBoxes(hand, undefined, { retries: 2 })
      .then((data) => !cancelled && setFassungen(data.fassungen))
      .catch((err: unknown) => {
        if (cancelled) return;
        setFassungen(null);
        setError(apiErrorText(err));
      });
    return () => {
      cancelled = true;
    };
  }, [hand]);

  const state = useMemo(
    () => readListState<BoxFilter, BoxSort, BoxStatus>(params, STRIP_BOX_LIST_SPEC),
    [params],
  );
  // REPLACE, like the three overviews: the back button walks the inspection
  // history, not a log of filter clicks.
  const update = (next: Partial<ListState<BoxFilter, BoxSort, BoxStatus>>) =>
    setParams(writeListState(params, next, STRIP_BOX_LIST_SPEC), { replace: true });

  const korbByBox = useMemo(() => korbCountsOf(korbItems)?.byStripBox ?? null, [korbItems]);
  const rows = useMemo(
    () => buildStripBoxRows({ fassungen: fassungen ?? [], korbByBox }),
    [fassungen, korbByBox],
  );
  const counts = useMemo(() => boxFilterCounts(rows), [rows]);
  const selected = useMemo(
    () => sortStripBoxRows(rows.filter((row) => matchesStripBoxFilters(row, state.filters, state.status, wort))),
    [rows, state.filters, state.status, wort],
  );
  const page = clampPage(state.page, selected.length);
  const shown = useMemo(() => pageSlice(selected, state.page), [selected, state.page]);
  const tally = useMemo(() => stripBoxTally(rows), [rows]);
  const narrowed = state.filters.length > 0 || (state.status !== null && state.status !== BOX_STATUSES[0]);

  // A page the selection cannot fill is corrected at render time, and the URL
  // with it — but only once there ARE rows, or a deep link's `seite=` would be
  // eaten before the read lands (`LetterOverview` states the same rule).
  useEffect(() => {
    if (selected.length > 0 && page !== state.page) {
      setParams(writeListState(params, { page }, STRIP_BOX_LIST_SPEC), { replace: true });
    }
  }, [selected.length, page, state.page, params, setParams]);

  const toggle = (key: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (!next.delete(key)) next.add(key);
      return next;
    });

  if (error) {
    return (
      <Typography variant="caption" sx={{ display: 'block', color: 'warning.main' }}>
        <ErrorText error={error} prefix={t.loadError} />
      </Typography>
    );
  }
  if (fassungen === null) return <CircularProgress size={16} />;

  return (
    <Box>
      <Stack spacing={1.5} sx={{ mb: 2 }}>
        <FilterChipRow
          chips={BOX_FILTERS.map((token) => ({
            token,
            label: t.filters[token],
            count: counts[token],
            active: state.filters.includes(token),
          }))}
          onToggle={(token) => {
            const filter = token as BoxFilter;
            update({
              filters: state.filters.includes(filter)
                ? state.filters.filter((f) => f !== filter)
                : [...state.filters, filter],
            });
          }}
          label={de.admin.liste.filterLabel}
        />
        <Stack direction="row" spacing={2} sx={{ alignItems: 'center', flexWrap: 'wrap', rowGap: 1 }}>
          <TextField
            select
            size="small"
            label={t.statusLabel}
            value={state.status ?? BOX_STATUSES[0]}
            onChange={(e) => update({ status: e.target.value as BoxStatus })}
            sx={{ width: 190 }}
          >
            {BOX_STATUSES.map((value) => (
              <MenuItem key={value} value={value}>
                {t.statuses[value]}
              </MenuItem>
            ))}
          </TextField>
          <InfoHint title={t.statusLabel} label={t.statusLabel}>
            <Stack spacing={0.75}>
              <Typography variant="body2">{t.statusHint}</Typography>
              <Typography variant="body2">{t.viewHint}</Typography>
            </Stack>
          </InfoHint>
          <Typography variant="caption" color="textSecondary">
            {narrowed || wort
              ? fmt(de.admin.liste.counterFiltered, {
                  shown: shown.length,
                  selected: selected.length,
                  total: rows.length,
                })
              : fmt(de.admin.liste.counter, { shown: shown.length, total: rows.length })}
          </Typography>
          {/* The counter of the WHOLE hand beside the list's own: „3 von 4
              Kästen folgen" answers the Bestand, and a number that moved with
              every chip would answer a different question on every click
              (author decision E). */}
          <Typography variant="caption" color="textSecondary">
            {fmt(t.tally, {
              kaesten: tally.kaesten,
              folgt: tally.folgt,
              vonHand: tally.vonHand,
              offen: tally.offen,
            })}
          </Typography>
        </Stack>
        {/* „Schwere zuerst" with nothing measured is the plan order under
            another name — said out loud instead of implied, exactly as the
            disabled sort switches of the three overviews say it. */}
        {rows.length > 0 && !stripBoxesRankable(rows) && (
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: paper.inkSoft }}>
              {t.notRanked}
            </Typography>
            <InfoHint title={t.notRanked} label={t.notRanked}>
              <Typography variant="body2">{t.notRankedHint}</Typography>
            </InfoHint>
          </Stack>
        )}
        {item && (
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap', rowGap: 0.5 }}>
            <Typography variant="caption" sx={{ color: paper.inkSoft }}>
              {t.itemFilterNote}
            </Typography>
            {/* A real button rather than a clickable caption: the one visible
                keyboard focus lives on MUI's own bases, and a bare `<button>`
                would also be under the 44 px floor (§9.1, §9.3). */}
            <Button size="small" onClick={onShowGalerie} sx={{ minHeight: TOUCH_TARGET }}>
              {t.itemFilterAction}
            </Button>
          </Stack>
        )}
      </Stack>

      {shown.length === 0 ? (
        <ListEmpty
          filtered={rows.length > 0}
          emptyText={t.empty}
          onReset={() => update({ filters: [], status: BOX_STATUSES[0] })}
        />
      ) : (
        <Box {...roving.containerProps} sx={{ display: 'flex', flexDirection: 'column', gap: 0.75, maxWidth: 1400 }}>
          {shown.map((row) => (
            <NachfahrRow
              key={row.key}
              rowProps={roving.rowProps(row.key)}
              row={row}
              hand={hand}
              expanded={expanded.has(row.key)}
              onToggle={() => toggle(row.key)}
              // The Korb row for a box: a WORD item whose specimen is the box
              // itself (V7) — same dialog, same note field, one more namespace.
              onMark={() =>
                fileMark({
                  target: { kind: 'word', word: row.word },
                  specimen: {
                    kind: 'strip',
                    id: stripBoxSpecimen(row.strip, row.fassung, row.boxIndex),
                    word: row.word,
                  },
                })
              }
            />
          ))}
        </Box>
      )}

      <Box sx={{ mt: 2 }}>
        <ListPager page={page} total={selected.length} onChange={(next) => update({ page: next })} />
      </Box>
    </Box>
  );
}
