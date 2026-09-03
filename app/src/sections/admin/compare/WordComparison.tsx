// Word comparison (redesign R1b, stage 1) — the connected-writing specimens of
// the source (words.json sidecar via /word-samples) next to the SAME word
// composed by the engine (/write/word). Two modes like GlyphComparison: side by
// side, or the engine ink projected onto the specimen pixels. The overlay
// registration is exact, not eyeballed: the sidecar carries the specimen's
// crop-local baseline/midband, the composed word lives in template units
// (baseline = 0, 1 unit = x-height), so the map is a pure scale+translate —
// scale = (baseline_y - midband_y) px per unit, left-aligned on the crop edge.

import RefreshIcon from '@mui/icons-material/Refresh';
import { Alert, Box, Button, Chip, CircularProgress, Tooltip, Typography } from '@mui/material';
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';

import { WrittenWord } from '@/components/WrittenWord';
import { useAdmin } from '@/context/adminState';
import { useInView } from '@/hooks/useInView';
import { getWordSamples, getWordSampleScore, wordSampleCropUrl } from '@/lib/api';
import type { ComposedWordOut, WordInstanceOut, WordSampleOut, WordSampleScoreOut } from '@/lib/api';
import { fetchRenderWord, invalidateRenderWord } from '@/lib/api/renderCache';
import { polylineToPathD, ringsToPathD } from '@/lib/svg';
import { de, fmt } from '@/locales/admin';
import { PairEditorDialog } from '@/sections/admin/pairs/PairEditorDialog';
import { pairKeysOf } from '@/sections/admin/pairs/pairKeys';
import {
  matchesTraceFilter,
  traceFrameOf,
  traceMatrix,
  traceStatusOf,
  type TraceFilter,
  type TraceStatus,
} from '@/sections/admin/shell/model';
import { useWorkbench } from '@/sections/admin/shell/workbenchState';
import { garamond } from '@/styles/paper';

import { PairMeasuredChips } from './PairMeasuredChips';
import { usePairMeasurements } from './pairMeasurement';

const FACE_H = 220; // px per face — words are wide, keep cards scannable

export type WordCompareMode = 'words' | 'pairs' | 'other';

function matchesMode(s: WordSampleOut, mode: WordCompareMode): boolean {
  // Truthiness, not != null: an empty set tag must not count as another hand.
  if (mode === 'other') return !!s.sample_set;
  if (s.sample_set) return false;
  return mode === 'pairs' ? s.kind === 'pair' : s.kind === 'word';
}

// Engine ink drawn into the specimen's pixel frame — on the traced row's own
// MEASURED registration wherever one exists (`traceFrameOf`), which is where
// the composition actually belongs; only a sample with no trace falls back to
// pinning the composition's left edge to the crop's.
function SpecimenOverlay({
  sample,
  composed,
  sourceId,
  traced,
  bust,
}: {
  sample: WordSampleOut;
  composed: ComposedWordOut;
  sourceId: string;
  traced: WordInstanceOut | null;
  bust: number;
}) {
  const frame = traceFrameOf(traced, sample);
  const matrix = traced
    ? traceMatrix(frame)
    : `matrix(${frame.xh} 0 0 ${-frame.xh} ${-composed.bounds.min_x * frame.xh} ${frame.baselineRow})`;
  const scale = FACE_H / sample.height;
  return (
    <svg
      width={sample.width * scale}
      height={FACE_H}
      viewBox={`0 0 ${sample.width} ${sample.height}`}
      style={{ display: 'block', background: '#fff', maxWidth: '100%' }}
    >
      <image
        href={wordSampleCropUrl(sourceId, sample.id, bust)}
        x={0}
        y={0}
        width={sample.width}
        height={sample.height}
        preserveAspectRatio="none"
      />
      <g transform={matrix}>
        {composed.items.map((it, i) =>
          it.rings ? (
            <path key={i} d={ringsToPathD(it.rings)} fill="#e02030" fillOpacity={0.42} fillRule="evenodd" />
          ) : (
            <path
              key={i}
              // flipY off — the enclosing <g> flips already (see lib/svg.ts);
              // with the default every generated Übergang was mirrored below
              // the baseline while the letters sat correctly.
              d={polylineToPathD(it.centerline, 0, false)}
              fill="none"
              stroke="#e02030"
              strokeOpacity={0.42}
              strokeWidth={it.stroke_width ?? it.mask_width}
              strokeLinecap="round"
            />
          ),
        )}
      </g>
    </svg>
  );
}

// Loss thresholds for the chip colour — same scale as the wordbench headline
// (lower better; the current bench baseline sits around 0.3).
function lossColor(loss: number): 'success' | 'warning' | 'error' {
  if (loss < 0.25) return 'success';
  if (loss < 0.4) return 'warning';
  return 'error';
}

// The three worst segments as "label penalty" lines for the chip tooltip —
// the number says how much, the label says which letter/join.
function worstSegments(score: WordSampleScoreOut): string[] {
  return [...score.segments]
    .sort((a, b) => b.penalty - a.penalty)
    .slice(0, 3)
    .map((s) => {
      const label = s.kind === 'connector' ? (s.pair ?? []).map((k) => k ?? '·').join('→') : (s.glyph_key ?? '?');
      return `${label} ${s.penalty.toFixed(2)}`;
    });
}

function ScoreChip({ score }: { score: WordSampleScoreOut }) {
  if (score.failed) {
    return <Chip size="small" color="error" variant="outlined" label={de.admin.compare.scoreFailed} />;
  }
  const lines = worstSegments(score);
  return (
    <Tooltip title={lines.length ? `${de.admin.compare.scoreWorstSegments} ${lines.join(' · ')}` : ''}>
      <Chip size="small" color={lossColor(score.loss)} variant="outlined" label={`Loss ${score.loss.toFixed(2)}`} />
    </Tooltip>
  );
}

function WordCard({
  sample,
  sourceId,
  overlay,
  traced,
  status,
  bust,
  score,
  measured,
  onOpenEditor,
  onPick,
}: {
  sample: WordSampleOut;
  sourceId: string;
  overlay: boolean;
  // This specimen's stored trace, when one exists — used ONLY for the overlay's
  // registration (see SpecimenOverlay); the card never draws the trace itself.
  traced: WordInstanceOut | null;
  // Where the specimen stands in the manual tracing pass — computed once by the
  // list (it filters and tallies on the same value).
  status: TraceStatus;
  // The admin-wide reload stamp — see `reload` below.
  bust: number;
  score?: WordSampleScoreOut;
  // The „Gemessen" readout — pair cards only (the caller owns the scope), so
  // the card itself stays agnostic of the occurrence/aggregate layers.
  measured?: ReactNode;
  onOpenEditor?: () => void;
  // Open this specimen in the Wörter view — the list is the overview, the
  // detail is where its trace, occurrences and score live.
  onPick?: () => void;
}) {
  const [ref, inView] = useInView<HTMLDivElement>();
  const [composed, setComposed] = useState<ComposedWordOut | null>(null);
  const [error, setError] = useState(false);

  // The overlay needs the raw composed payload (WrittenWord keeps its own
  // internal); fetched through the shared render cache, so the side-by-side
  // WrittenWord and the overlay share one request per word.
  useEffect(() => {
    if (!inView) return;
    let cancelled = false;
    fetchRenderWord(sourceId, sample.word, bust)
      .then((c) => {
        if (!cancelled) setComposed(c);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [inView, sourceId, sample.word, bust]);

  const cropW = (FACE_H / sample.height) * sample.width;

  return (
    <Box ref={ref} sx={{ border: 1, borderColor: 'divider', borderRadius: 2, p: 2, bgcolor: 'background.paper', display: 'flex', flexDirection: 'column', gap: 1 }}>
      <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, flexWrap: 'wrap' }}>
        <Typography sx={{ fontFamily: garamond, fontSize: 24, lineHeight: 1 }}>{sample.word}</Typography>
        <Typography variant="caption" color="text.secondary">
          {sample.id}
        </Typography>
        {sample.sample_set && <Chip size="small" label={sample.sample_set} />}
        {/* The manual-reference progress marker: a done card gets the green
            chip, a clipped specimen the warning one — plain absence still IS
            the "still to do" state, so the list stays scannable while working
            through the hand-traced reference set. */}
        {status === 'authored' && (
          <Tooltip title={de.admin.belege.provenanceAuthored}>
            <Chip size="small" color="success" label={de.admin.compare.authoredChip} />
          </Tooltip>
        )}
        {status === 'incomplete' && (
          <Tooltip title={sample.note || de.admin.compare.incompleteChipHint}>
            <Chip size="small" color="warning" variant="outlined" label={de.admin.compare.incompleteChip} />
          </Tooltip>
        )}
        {score && <ScoreChip score={score} />}
        {composed && composed.missing.length > 0 && (
          <Chip size="small" color="warning" label={`${de.admin.compare.missingPrefix}${composed.missing.join(', ')}`} />
        )}
        <Box sx={{ display: 'flex', gap: 1, ml: 'auto' }}>
          {onPick && (
            <Button
              size="small"
              variant="text"
              onClick={onPick}
              aria-label={fmt(de.admin.compare.openWordFor, { word: sample.word })}
            >
              {de.admin.compare.openWord}
            </Button>
          )}
          {onOpenEditor && (
            <Button size="small" variant="text" onClick={onOpenEditor}>
              {de.admin.compare.openPairEditor}
            </Button>
          )}
        </Box>
      </Box>

      {measured}

      {error ? (
        <Alert severity="error" sx={{ py: 0 }}>
          {de.admin.compare.wordRenderError}
        </Alert>
      ) : !inView ? (
        <Box sx={{ height: FACE_H }} />
      ) : overlay ? (
        !composed ? (
          <Box sx={{ height: FACE_H, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <CircularProgress size={24} />
          </Box>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            <Typography variant="caption" color="text.secondary">
              {de.admin.compare.overlayHeading}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', bgcolor: '#fff', borderRadius: 1, px: 1, overflowX: 'auto' }}>
              <SpecimenOverlay sample={sample} composed={composed} sourceId={sourceId} traced={traced} bust={bust} />
            </Box>
          </Box>
        )
      ) : (
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', alignItems: 'flex-start' }}>
          {/* `flex: 1 1 320px` rather than a natural width: side by side is the
              point, so the two faces shrink together instead of wrapping the
              written one under the crop — and below ~700px they still stack. */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, minWidth: 0, flex: '1 1 320px' }}>
            <Typography variant="caption" color="text.secondary">
              {de.admin.compare.colCrop}
            </Typography>
            <Box sx={{ height: FACE_H, display: 'flex', alignItems: 'center', bgcolor: '#fff', borderRadius: 1, px: 1 }}>
              <img
                src={wordSampleCropUrl(sourceId, sample.id, bust)}
                alt={`${de.admin.compare.specimenAlt} ${sample.word}`}
                width={cropW}
                height={FACE_H}
                loading="lazy"
                decoding="async"
                style={{ display: 'block', maxWidth: '100%', objectFit: 'contain' }}
              />
            </Box>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, minWidth: 0, flex: '1 1 320px' }}>
            <Typography variant="caption" color="text.secondary">
              {de.admin.compare.colWritten}
            </Typography>
            <Box sx={{ height: FACE_H, display: 'flex', alignItems: 'center', bgcolor: '#fff', borderRadius: 1, px: 1 }}>
              <WrittenWord
                text={sample.word}
                sourceId={sourceId}
                height={FACE_H * 0.9}
                animate={false}
                showLineature
                bust={bust}
              />
            </Box>
          </Box>
        </Box>
      )}
    </Box>
  );
}

export function WordComparison({
  mode,
  overlay,
  filterText = '',
  traceFilter = 'all',
  onPick,
}: {
  mode: WordCompareMode;
  overlay: boolean;
  // Free-text filter over the specimen words, owned by the surrounding view
  // (the list is long enough that scrolling for one word is not a plan).
  filterText?: string;
  // Filter over the manual-tracing status, owned by the surrounding view too:
  // „Offen" turns the list into the to-do list of the tracing pass.
  traceFilter?: TraceFilter;
  onPick?: (sample: WordSampleOut) => void;
}) {
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
  // source for the whole tab and only for the Verbindungen tab: a word card is
  // many joins at once, and the Fremdhand tab is view-only context that is
  // never measured against. The tab switch only flips `enabled` (this view
  // stays mounted), and the hook reuses what it already holds for the source,
  // so leaving and returning costs no request.
  const measurements = usePairMeasurements(sourceId, mode === 'pairs');
  // The stored traces, only for the overlay's registration — already loaded by
  // the shell for the whole workbench, so this costs no request. A sample the
  // harvest never traced simply has none and keeps the left-edge fallback.
  const { wordRows } = useWorkbench();
  const tracedById = useMemo(() => new Map(wordRows.map((r) => [r.specimen_id, r])), [wordRows]);

  // „Neu laden" — the letters grid's button, for words. `refreshCrop` moves the
  // admin-wide stamp that keys the render cache AND rides the request, so the
  // written faces really recompose (the CDN holds /write/word for a day); the
  // crops are re-requested with it, and the cards remount so a card that had
  // already settled paints the new composition rather than its old state.
  const reload = useCallback(() => {
    for (const s of samples ?? []) invalidateRenderWord(sourceId, s.word);
    refreshCrop();
  }, [samples, sourceId, refreshCrop]);

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

  // Progress of the manual reference set for this tab — counted over the
  // mode's whole specimen list (not the filtered slice), so the tally stays
  // the tab's truth while searching. The clipped specimens leave the
  // DENOMINATOR: they are not work anyone can do, and counting them would keep
  // the tally short of its total for good. They get their own number instead.
  const authoredTally = useMemo(() => {
    const rows = (samples ?? []).filter((s) => matchesMode(s, mode)).map(statusOf);
    return {
      done: rows.filter((st) => st === 'authored').length,
      total: rows.filter((st) => st !== 'incomplete').length,
      incomplete: rows.filter((st) => st === 'incomplete').length,
    };
  }, [samples, mode, statusOf]);

  const visible = useMemo(() => {
    const needle = filterText.trim().toLowerCase();
    const rows = (samples ?? [])
      .filter((s) => matchesMode(s, mode))
      .filter((s) => matchesTraceFilter(traceFilter, statusOf(s)))
      .filter((s) => !needle || s.word.toLowerCase().includes(needle));
    // Once scored, worst first — that IS the work list. Unscored rows keep
    // their sidecar order at the end. Deliberately NOT while the sweep runs:
    // re-sorting per incoming score would make the cards jump on every
    // completed request; the chips fill in place, the ranking lands once.
    return rows.length && !scoring && Object.keys(scores).length
      ? [...rows].sort((a, b) => (scores[b.id]?.loss ?? -1) - (scores[a.id]?.loss ?? -1))
      : rows;
  }, [samples, mode, scores, scoring, filterText, traceFilter, statusOf]);

  // Sequentially score every specimen of the tab: the endpoint is CPU-bound
  // server-side (compose + chamfer grid search), a parallel fan-out would
  // just queue on the single instance and risk timeouts.
  const loadScores = async () => {
    const run = ++scoringRun.current;
    const targets = (samples ?? []).filter((s) => matchesMode(s, mode));
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
  if (visible.length === 0) {
    // An empty list means two different things — the source has no specimens
    // at all, or this status has none left (which, for „Offen", is the good
    // news that the pass is through).
    const empty = samples.length === 0 ? de.admin.compare.wordsEmpty : de.admin.compare.statusEmpty;
    return <Alert severity="info">{empty}</Alert>;
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 1100 }}>
      {/* Only the Fremdhand list still explains itself: its "context, never a
          reference" caveat is not obvious from the cards. The words intro
          moved into the view's own header when this became a block — two
          explanatory paragraphs stacked on each other read as two pages. */}
      {mode === 'other' && (
        <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 720 }}>
          {de.admin.compare.otherIntro}
        </Typography>
      )}
      {/* The Fremdhand tab is view-only context, never a scoring reference. */}
      {mode !== 'other' && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
          <Button size="small" variant="outlined" onClick={loadScores} disabled={scoring !== null}>
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
            {fmt(de.admin.compare.authoredCount, { done: authoredTally.done, total: authoredTally.total })}
            {authoredTally.incomplete > 0 &&
              ` · ${fmt(de.admin.compare.incompleteCount, { count: authoredTally.incomplete })}`}
          </Typography>
          {/* Same affordance as the letters grid: re-compose the written faces
              after a template, Laufform or override change, instead of
              reloading the browser tab. */}
          <Button size="small" variant="outlined" startIcon={<RefreshIcon />} onClick={reload} sx={{ ml: 'auto' }}>
            {de.admin.compare.reload}
          </Button>
        </Box>
      )}
      {/* One quiet line for the whole tab, never per card: the measured layer
          is secondary context — a failed read degrades the cards, it does not
          break them. */}
      {mode === 'pairs' && (measurements.status === 'error' || measurements.aggregates.status === 'unavailable') && (
        <Typography variant="caption" color="text.secondary">
          {measurements.status === 'error' ? de.admin.compare.measuredLoadError : de.admin.compare.measuredUnavailable}
        </Typography>
      )}
      {visible.map((s) => {
        // A pair card links straight into the pair editor (redesign R1b →
        // R3 circle) — with its specimen crop as the editor's underlay.
        const keys = mode === 'pairs' ? pairKeysOf(s.word) : null;
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
