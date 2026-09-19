// The Wörter overview — the work list, its toolbar and the gallery behind the
// switch, with ONE place deciding which Wortproben are on screen.
//
// It sits between the view (`WordView`, which owns the typed subject) and the
// three bodies: the compact list is the default (V14), the card wall the
// opt-in, and the third tab is the Nachfahr-Übersicht, which is a stack of the
// author's own lines rather than a list of Wortproben.
//
// Six axes live in the URL and nowhere else (author decision Q5 a of
// 2026-09-19): `ansicht` · `sort` · `seite` · `filter` (the free-text „Proben
// filtern") · `status` (the Nachfahren selection) · `reiter` (which tab). A
// link out of the Auftragskorb has to open the same view on another device,
// which `localStorage` cannot do — and the free-text field the header carries
// („Wort oder Satz" → „Schreiben") is NOT one of them: it writes a subject,
// which is `w=`.
//
// The specimen list, the scores and the sweep moved up here from
// `WordComparison`, which kept them for a card wall that was also the
// overview. Both bodies now read the same rows, so switching between list and
// gallery keeps the scores that were just paid for.

import RefreshIcon from '@mui/icons-material/Refresh';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  FormControlLabel,
  MenuItem,
  Switch,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { useAdmin } from '@/context/adminState';
import { getWordSamples, getWordSampleScore } from '@/lib/api';
import type { WordInstanceOut, WordSampleOut, WordSampleScoreOut } from '@/lib/api';
import { invalidateRenderWord } from '@/lib/api/renderCache';
import { de, fmt } from '@/locales/admin';
import { WordCard } from '@/sections/admin/compare/WordCard';
import { ListEmpty, ListPager, ListSortSwitch, ListViewSwitch } from '@/sections/admin/shell/WorkList';
import { useKorbItems } from '@/sections/admin/shell/korbState';
import { korbCountsOf } from '@/sections/admin/shell/korbTargets';
import { clampPage, pageSlice, readListState, writeListState, type ListState } from '@/sections/admin/shell/listState';
import { useWorkbench } from '@/sections/admin/shell/workbenchState';
import { TOUCH_TARGET } from '@/styles/hitArea';

import { AuthoredTraceReview } from './AuthoredTraceReview';
import { WordList } from './WordList';
import {
  WORD_LIST_SPEC,
  WORD_STATUSES,
  WORD_TABS,
  buildWordRows,
  matchesWordFilters,
  sortWordRows,
  wordTally,
  wordsRankable,
  type WordRow,
  type WordSort,
  type WordStatus,
  type WordTab,
} from './wordRows';

type WordListState = ListState<never, WordSort, WordStatus, WordTab>;

const STATUS_LABELS: Record<WordStatus, string> = {
  alle: de.admin.compare.statusAll,
  offen: de.admin.compare.statusOpen,
  nachgefahren: de.admin.compare.statusAuthored,
  unvollstaendig: de.admin.compare.statusIncomplete,
};

const TAB_LABELS: Record<WordTab, string> = {
  woerter: de.admin.compare.tabWords,
  andere: de.admin.compare.tabOther,
  nachgefahren: de.admin.words.tabAuthored,
};

export function WordOverview({ onPick }: { onPick: (word: string, sampleId: string) => void }) {
  const [params, setParams] = useSearchParams();
  const { source, sourceId, cropCacheBust, refreshCrop } = useAdmin();
  const workbench = useWorkbench();
  const korbItems = useKorbItems();
  const t = de.admin.words;

  // Where a page change scrolls back to.
  const topRef = useRef<HTMLDivElement | null>(null);

  const [samples, setSamples] = useState<WordSampleOut[] | null>(null);
  const [error, setError] = useState(false);
  // „Überlagern" is a rendering mode of the card, not work-list state — it
  // stays component state and out of the URL.
  const [overlay, setOverlay] = useState(false);
  const [scores, setScores] = useState<Record<string, WordSampleScoreOut>>({});
  const [scoring, setScoring] = useState<{ done: number; total: number } | null>(null);
  const [scoreError, setScoreError] = useState(false);
  const scoringRun = useRef(0);

  // Drop everything the previous source produced DURING RENDER instead of in
  // the effect below — React's "adjusting state when a prop changes"
  // (react-hooks/set-state-in-effect). The guard carries the effect's inputs, so
  // the list never paints one frame of the old source's words and scores. The
  // run counter stays in the effect: bumping a ref during render is its own
  // violation (react-hooks/refs), and invalidating the sweep one commit later
  // is early enough — the sweep only ever writes from an async continuation.
  const loadKey = `${sourceId} ${cropCacheBust}`;
  const [shownFor, setShownFor] = useState(loadKey);
  if (shownFor !== loadKey) {
    setShownFor(loadKey);
    setSamples(null);
    setError(false);
    setScores({});
    setScoring(null);
    setScoreError(false);
  }

  useEffect(() => {
    let cancelled = false;
    scoringRun.current += 1; // invalidate an in-flight score sweep of the old source
    getWordSamples(sourceId, { retries: 2 }, cropCacheBust)
      .then((rows) => {
        if (!cancelled) setSamples(rows);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => {
      cancelled = true;
    };
    // cropCacheBust: „Neu laden" must re-fetch the sample metadata too — the
    // rects/heights can have changed, and stale dims squash the fresh crops.
  }, [sourceId, cropCacheBust]);

  // „Neu laden" — the letters list's button, for words. `refreshCrop` moves the
  // admin-wide stamp that keys the render cache AND rides the request, so the
  // written faces really recompose (the CDN holds /write/word for a day).
  const reload = useCallback(() => {
    for (const sample of samples ?? []) invalidateRenderWord(sourceId, sample.word);
    refreshCrop();
  }, [samples, sourceId, refreshCrop]);

  // Memoised on the params object, which `useSearchParams` keeps stable per
  // location: `readListState` builds fresh arrays, and an unmemoised state
  // would make every memo below it recompute on every render.
  const state = useMemo(() => readListState<never, WordSort, WordStatus, WordTab>(params, WORD_LIST_SPEC), [params]);
  const tab: WordTab = state.tab ?? WORD_TABS[0];
  // List state REPLACES, so the back button keeps walking the inspection
  // history `focus.ts` promises instead of a log of every keystroke in the
  // search field. The subject still pushes — a different question, a different
  // hop.
  const update = (next: Partial<WordListState>) =>
    setParams(writeListState(params, next, WORD_LIST_SPEC), { replace: true });

  const tracesBySpecimen = useMemo(() => {
    const map = new Map<string, WordInstanceOut[]>();
    for (const row of workbench.wordRows) {
      const list = map.get(row.specimen_id);
      if (list) list.push(row);
      else map.set(row.specimen_id, [row]);
    }
    return map;
  }, [workbench.wordRows]);

  const korbByWord = useMemo(() => korbCountsOf(korbItems)?.byWord ?? null, [korbItems]);

  const rows = useMemo(
    () => buildWordRows({ samples: samples ?? [], tracesBySpecimen, tab, korbByWord, scores }),
    [samples, tracesBySpecimen, tab, korbByWord, scores],
  );
  const selected = useMemo(
    () => sortWordRows(rows.filter((row) => matchesWordFilters(row, state.status, state.text)), state.sort),
    [rows, state.status, state.text, state.sort],
  );
  const page = clampPage(state.page, selected.length);
  const shown = useMemo(() => pageSlice(selected, state.page), [selected, state.page]);
  const tally = useMemo(() => wordTally(rows), [rows]);

  // A page the selection cannot fill is corrected at render time — and the URL
  // with it, or a shared link would describe a page the view is not on. Only
  // once the selection HAS rows: before the first read it is empty for
  // everyone, and rewriting then would eat a deep link's `seite=`.
  useEffect(() => {
    if (selected.length > 0 && page !== state.page) {
      setParams(writeListState(params, { page }, WORD_LIST_SPEC), { replace: true });
    }
  }, [selected.length, page, state.page, params, setParams]);

  // Sequentially score every Wortprobe of the TAB — unchanged in scope: the
  // endpoint is CPU-bound server-side (compose + chamfer grid search), so a
  // parallel fan-out would just queue on the single instance. What is new is
  // that the button keeps the second half of its name in the URL: the ranking
  // it produces is written as `sort=schlechteste` rather than applied
  // invisibly, so the order survives opening a word and coming back.
  const loadScores = async () => {
    const run = ++scoringRun.current;
    const targets = rows;
    setScoreError(false);
    setScoring({ done: 0, total: targets.length });
    for (let i = 0; i < targets.length; i += 1) {
      try {
        const score = await getWordSampleScore(sourceId, targets[i].sampleId);
        if (run !== scoringRun.current) return;
        setScores((prev) => ({ ...prev, [targets[i].sampleId]: score }));
      } catch {
        if (run !== scoringRun.current) return;
        setScoreError(true);
      }
      setScoring({ done: i + 1, total: targets.length });
    }
    setScoring(null);
    // Through the updater form: `params` from the closure is a snapshot from
    // before the sweep, and the reader may well have filtered meanwhile.
    setParams((prev) => writeListState(prev, { sort: 'schlechteste' }, WORD_LIST_SPEC), { replace: true });
  };

  if (!source) return null;

  const filtered = state.text.trim() !== '' || (state.status !== null && state.status !== WORD_STATUSES[0]);
  const resetFilters = () => update({ text: '', status: WORD_STATUSES[0] });

  const searchField = (
    <TextField
      size="small"
      label={t.filterLabel}
      value={state.text}
      onChange={(e) => update({ text: e.target.value })}
      sx={{ width: 200 }}
    />
  );

  const tabs = (
    <ToggleButtonGroup
      size="small"
      exclusive
      value={tab}
      onChange={(_e, next: WordTab | null) => next && update({ tab: next })}
      aria-label={t.tabsLabel}
      sx={{ mt: 0.25 }}
    >
      {WORD_TABS.map((value) => (
        <ToggleButton key={value} value={value} sx={{ minHeight: TOUCH_TARGET }}>
          {TAB_LABELS[value]}
        </ToggleButton>
      ))}
    </ToggleButtonGroup>
  );

  // The Nachfahr-Übersicht is the authored rows BY DEFINITION — a status
  // filter, a Loss ranking and a list/gallery switch over it would each have
  // exactly one meaningful setting, so the tab keeps only the search field.
  if (tab === 'nachgefahren') {
    return (
      <Box ref={topRef}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'flex-start', mb: 2 }}>
          {searchField}
          {tabs}
        </Box>
        <AuthoredTraceReview filterText={state.text} onPickWord={onPick} />
      </Box>
    );
  }

  return (
    <Box ref={topRef}>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mb: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'flex-start' }}>
          {searchField}
          <TextField
            select
            size="small"
            label={de.admin.compare.statusLabel}
            value={state.status ?? WORD_STATUSES[0]}
            onChange={(e) => update({ status: e.target.value as WordStatus })}
            sx={{ width: 190 }}
          >
            {WORD_STATUSES.map((value) => (
              <MenuItem key={value} value={value}>
                {STATUS_LABELS[value]}
              </MenuItem>
            ))}
          </TextField>
          {tabs}
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <ListSortSwitch
            sort={state.sort}
            label={de.admin.compare.sortLabel}
            options={[
              { token: 'reihenfolge', label: t.sortOrder },
              {
                token: 'schlechteste',
                label: de.admin.compare.sortWorst,
                disabled: !wordsRankable(rows),
                disabledHint: t.sortWorstUnavailable,
              },
            ]}
            onChange={(token) => update({ sort: token as WordSort })}
          />
          <ListViewSwitch view={state.view} onChange={(view) => update({ view })} />
          <Typography variant="caption" color="text.secondary">
            {filtered
              ? fmt(de.admin.liste.counterFiltered, {
                  shown: shown.length,
                  selected: selected.length,
                  total: rows.length,
                })
              : fmt(de.admin.liste.counter, { shown: shown.length, total: rows.length })}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: { sm: 'auto' } }}>
            <FormControlLabel
              control={<Switch size="small" checked={overlay} onChange={(e) => setOverlay(e.target.checked)} />}
              label={<Typography variant="caption">{de.admin.compare.overlayToggle}</Typography>}
            />
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
        {/* The Fremdhand tab is view-only context, never a scoring reference —
            so it offers no sweep and explains itself instead. */}
        {tab === 'andere' ? (
          <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 720 }}>
            {de.admin.compare.otherIntro}
          </Typography>
        ) : (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
            <Button
              size="small"
              variant="outlined"
              onClick={loadScores}
              disabled={scoring !== null || rows.length === 0}
              sx={{ minHeight: TOUCH_TARGET }}
            >
              {scoring
                ? `${de.admin.compare.scoreBusy} (${scoring.done}/${scoring.total})`
                : de.admin.compare.scoreButton}
            </Button>
            {scoring && <CircularProgress size={16} />}
            {scoreError && (
              <Typography variant="caption" color="error">
                {de.admin.compare.scoreError}
              </Typography>
            )}
            <Typography variant="caption" color="text.secondary">
              {fmt(de.admin.compare.authoredCount, { done: tally.done, total: tally.total })}
              {tally.incomplete > 0 && ` · ${fmt(de.admin.compare.incompleteCount, { count: tally.incomplete })}`}
            </Typography>
          </Box>
        )}
      </Box>

      {error ? (
        <Alert severity="error">{de.admin.compare.wordsLoadError}</Alert>
      ) : samples === null ? (
        <Box sx={{ p: 4, display: 'flex', justifyContent: 'center' }}>
          <CircularProgress size={28} />
        </Box>
      ) : shown.length === 0 ? (
        // Two silences kept apart: a source with no Wortprobe of this tab at
        // all, and a search or status that happens to match none of them.
        <ListEmpty filtered={rows.length > 0} emptyText={de.admin.compare.wordsEmpty} onReset={resetFilters} />
      ) : state.view === 'liste' ? (
        <WordList
          rows={shown}
          sourceId={sourceId}
          cropCacheBust={cropCacheBust}
          overlay={overlay}
          onPick={(row) => onPick(row.word, row.sampleId)}
        />
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 1100 }}>
          {shown.map((row: WordRow) => (
            <WordCard
              // The page is part of the key because `useInView` is one-shot: a
              // card swapped in under the previous page's key would keep its
              // „already seen" flag and never fetch its own composition.
              key={`${row.sampleId}:${page}:${cropCacheBust}`}
              sample={row.sample}
              sourceId={sourceId}
              overlay={overlay}
              traced={row.traced}
              status={row.status}
              bust={cropCacheBust}
              score={row.score ?? undefined}
              onPick={() => onPick(row.word, row.sampleId)}
            />
          ))}
        </Box>
      )}

      <Box sx={{ mt: 2 }}>
        {/* The pager sits under the list, so a page change has to take the
            reader back up with it: consecutive pages are near-identical in
            height, and `scrollTop` would survive the swap intact. */}
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
