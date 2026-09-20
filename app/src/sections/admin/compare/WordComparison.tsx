// The Verbindungs-Platten of the source — the Abb.-20 pair drills, each next
// to the same combination composed by the engine.
//
// Until V14 this component was BOTH the pair-drill wall and the Wörter
// overview, which is why it owned the specimen list, the scores and the sweep.
// The Wörter route is an Arbeitsliste now and owns those itself
// (`words/WordOverview.tsx`), so what is left here is the one caller that
// never had a list: the collapsed „Verbindungs-Platten der Vorlage einblenden"
// block inside the Übergänge overview. It carries no URL state on purpose — it
// is a sub-block of another view's overview, and a second set of list
// parameters on the same route could only describe one of the two surfaces.
//
// The card itself lives in `compare/WordCard.tsx`, shared with the Wörter
// list and its gallery.

import RefreshIcon from '@mui/icons-material/Refresh';
import { Alert, Box, Button, CircularProgress, Typography } from '@mui/material';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { useAdmin } from '@/context/adminState';
import { getWordSamples, getWordSampleScore } from '@/lib/api';
import type { WordSampleOut, WordSampleScoreOut } from '@/lib/api';
import { invalidateRenderWord } from '@/lib/api/renderCache';
import { de, fmt } from '@/locales/admin';
import { PairEditorDialog } from '@/sections/admin/pairs/PairEditorDialog';
import { pairKeysOf } from '@/sections/admin/pairs/pairKeys';
import { traceStatusOf } from '@/sections/admin/shell/model';
import { useWorkbench } from '@/sections/admin/shell/workbenchState';

import { PairMeasuredChips } from './PairMeasuredChips';
import { WordCard } from './WordCard';
import { usePairMeasurements } from './pairMeasurement';

/** A drill plate of this hand: a `pair` specimen with no foreign-set tag.
 * Truthiness, not `!= null` — an empty tag must not count as another hand. */
const isDrill = (sample: WordSampleOut): boolean => !sample.sample_set && sample.kind === 'pair';

export function WordComparison({ overlay, onPick }: { overlay: boolean; onPick?: (sample: WordSampleOut) => void }) {
  const { source, sourceId, cropCacheBust, refreshCrop } = useAdmin();
  const [samples, setSamples] = useState<WordSampleOut[] | null>(null);
  const [error, setError] = useState(false);
  const [scores, setScores] = useState<Record<string, WordSampleScoreOut>>({});
  const [scoring, setScoring] = useState<{ done: number; total: number } | null>(null);
  const [scoreError, setScoreError] = useState(false);
  const scoringRun = useRef(0);
  const [editing, setEditing] = useState<{ sample: WordSampleOut; left: string; right: string } | null>(null);
  // Per-sample remount counter — bumped after an override save to force the
  // card's composed-word refetch (the render cache entry is evicted with it).
  const [cardTick, setCardTick] = useState<Record<string, number>>({});
  // The measured layers behind the joins (Handmodell H2) — loaded ONCE per
  // source: a drill card is one join, and the readout is what makes this block
  // more than a picture. The hook reuses what it already holds for the source,
  // so collapsing the block and opening it again costs no request.
  const measurements = usePairMeasurements(sourceId, true);
  // The stored traces, only for the overlay's registration — already loaded by
  // the shell for the whole workbench, so this costs no request.
  const { wordRows } = useWorkbench();
  const tracedById = useMemo(() => new Map(wordRows.map((r) => [r.specimen_id, r])), [wordRows]);

  // „Neu laden": `refreshCrop` moves the admin-wide stamp that keys the render
  // cache AND rides the request, so the written faces really recompose (the
  // CDN holds /write/word for a day); the crops are re-requested with it.
  const reload = useCallback(() => {
    for (const s of samples ?? []) invalidateRenderWord(sourceId, s.word);
    refreshCrop();
  }, [samples, sourceId, refreshCrop]);

  // Drop everything the previous source produced DURING RENDER instead of in
  // the effect below — React's "adjusting state when a prop changes"
  // (react-hooks/set-state-in-effect). The run counter stays in the effect:
  // bumping a ref during render is its own violation (react-hooks/refs).
  const loadKey = `${sourceId} ${cropCacheBust}`;
  const [shownFor, setShownFor] = useState(loadKey);
  if (shownFor !== loadKey) {
    setShownFor(loadKey);
    setSamples(null);
    setError(false);
    setScores({});
    setScoring(null);
    setScoreError(false);
    setEditing(null); // an open pair editor must not outlive its source
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

  const statusOf = useCallback(
    (s: WordSampleOut) => traceStatusOf(s, tracedById.get(s.id) ?? null),
    [tracedById],
  );

  // Progress of the manual reference set over the whole drill list. The clipped
  // specimens leave the DENOMINATOR: they are not work anyone can do, and
  // counting them would keep the tally short of its total for good.
  const authoredTally = useMemo(() => {
    const rows = (samples ?? []).filter(isDrill).map(statusOf);
    return {
      done: rows.filter((st) => st === 'authored').length,
      total: rows.filter((st) => st !== 'incomplete').length,
      incomplete: rows.filter((st) => st === 'incomplete').length,
    };
  }, [samples, statusOf]);

  const visible = useMemo(() => {
    const rows = (samples ?? []).filter(isDrill);
    // Once scored, worst first — that IS the work list. Unscored rows keep
    // their sidecar order at the end. Deliberately NOT while the sweep runs:
    // re-sorting per incoming score would make the cards jump on every
    // completed request; the chips fill in place, the ranking lands once.
    return rows.length && !scoring && Object.keys(scores).length
      ? [...rows].sort((a, b) => (scores[b.id]?.loss ?? -1) - (scores[a.id]?.loss ?? -1))
      : rows;
  }, [samples, scores, scoring]);

  // Sequentially score every drill plate: the endpoint is CPU-bound
  // server-side (compose + chamfer grid search), a parallel fan-out would
  // just queue on the single instance and risk timeouts.
  const loadScores = async () => {
    const run = ++scoringRun.current;
    const targets = (samples ?? []).filter(isDrill);
    setScoreError(false);
    setScoring({ done: 0, total: targets.length });
    for (let i = 0; i < targets.length; i += 1) {
      try {
        const score = await getWordSampleScore(sourceId, targets[i].id);
        if (run !== scoringRun.current) return;
        setScores((prev) => ({ ...prev, [targets[i].id]: score }));
      } catch {
        if (run !== scoringRun.current) return;
        setScoreError(true);
      }
      setScoring({ done: i + 1, total: targets.length });
    }
    setScoring(null);
  };

  if (!source) return null;
  if (error) return <Alert severity="error">{de.admin.compare.wordsLoadError}</Alert>;
  if (samples === null) {
    return (
      <Box sx={{ p: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress size={28} />
      </Box>
    );
  }
  if (visible.length === 0) return <Alert severity="info">{de.admin.compare.wordsEmpty}</Alert>;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 1100 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
        <Button size="small" variant="outlined" onClick={loadScores} disabled={scoring !== null}>
          {scoring ? `${de.admin.compare.scoreBusy} (${scoring.done}/${scoring.total})` : de.admin.compare.scoreButton}
        </Button>
        {scoring && <CircularProgress size={16} />}
        {scoreError && (
          <Typography variant="caption" color="error">
            {de.admin.compare.scoreError}
          </Typography>
        )}
        <Typography variant="caption" color="textSecondary">
          {fmt(de.admin.compare.authoredCount, { done: authoredTally.done, total: authoredTally.total })}
          {authoredTally.incomplete > 0 &&
            ` · ${fmt(de.admin.compare.incompleteCount, { count: authoredTally.incomplete })}`}
        </Typography>
        <Button size="small" variant="outlined" startIcon={<RefreshIcon />} onClick={reload} sx={{ ml: 'auto' }}>
          {de.admin.compare.reload}
        </Button>
      </Box>
      {/* One quiet line for the whole block, never per card: the measured layer
          is secondary context — a failed read degrades the cards, it does not
          break them. */}
      {(measurements.status === 'error' || measurements.aggregates.status === 'unavailable') && (
        <Typography variant="caption" color="textSecondary">
          {measurements.status === 'error' ? de.admin.compare.measuredLoadError : de.admin.compare.measuredUnavailable}
        </Typography>
      )}
      {visible.map((s) => {
        // A drill card links straight into the pair editor (redesign R1b →
        // R3 circle) — with its specimen crop as the editor's underlay.
        const keys = pairKeysOf(s.word);
        return (
          <WordCard
            // The tick remounts the card after an override save, so its
            // "as written" render refetches the just-changed composition.
            key={`${s.id}:${cardTick[s.id] ?? 0}:${cropCacheBust}`}
            sample={s}
            sourceId={sourceId}
            overlay={overlay}
            traced={tracedById.get(s.id) ?? null}
            status={statusOf(s)}
            bust={cropCacheBust}
            score={scores[s.id]}
            // Matched by the SAME base-key pair the editor deep link uses, so
            // the numbers and the „Im Paar-Editor öffnen" target can never
            // describe two different joins. A ligature-folding pair (no join,
            // no keys) gets no readout either.
            measured={
              keys ? (
                <PairMeasuredChips
                  measurements={measurements}
                  leftKey={keys[0]}
                  rightKey={keys[1]}
                  specimenId={s.id}
                />
              ) : undefined
            }
            onOpenEditor={keys ? () => setEditing({ sample: s, left: keys[0], right: keys[1] }) : undefined}
            onPick={onPick ? () => onPick(s) : undefined}
          />
        );
      })}
      {editing && (
        <PairEditorDialog
          open
          onClose={() => setEditing(null)}
          pairText={editing.sample.word}
          leftKey={editing.left}
          rightKey={editing.right}
          sourceId={sourceId}
          specimen={editing.sample}
          onChanged={() => {
            // An override change makes the card stale twice over: drop its
            // score (the chip must not mislead; a fresh sweep re-ranks) AND
            // evict the composed word from the shared render cache + remount
            // the card, so "as written"/overlay show the post-override join.
            invalidateRenderWord(sourceId, editing.sample.word);
            setCardTick((prev) => ({ ...prev, [editing.sample.id]: (prev[editing.sample.id] ?? 0) + 1 }));
            setScores((prev) => {
              const next = { ...prev };
              delete next[editing.sample.id];
              return next;
            });
          }}
        />
      )}
    </Box>
  );
}
