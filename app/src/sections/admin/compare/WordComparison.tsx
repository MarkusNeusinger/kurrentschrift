// Word comparison (redesign R1b, stage 1) — the connected-writing specimens of
// the source (words.json sidecar via /word-samples) next to the SAME word
// composed by the engine (/write/word). Two modes like GlyphComparison: side by
// side, or the engine ink projected onto the specimen pixels. The overlay
// registration is exact, not eyeballed: the sidecar carries the specimen's
// crop-local baseline/midband, the composed word lives in template units
// (baseline = 0, 1 unit = x-height), so the map is a pure scale+translate —
// scale = (baseline_y - midband_y) px per unit, left-aligned on the crop edge.

import { Alert, Box, Button, Chip, CircularProgress, Tooltip, Typography } from '@mui/material';
import { useEffect, useMemo, useRef, useState } from 'react';

import { WrittenWord } from '@/components/WrittenWord';
import { useAdmin } from '@/context/AdminContext';
import { useInView } from '@/hooks/useInView';
import { getWordSamples, getWordSampleScore, wordSampleCropUrl } from '@/lib/api';
import type { ComposedWordOut, WordSampleOut, WordSampleScoreOut } from '@/lib/api';
import { fetchRenderWord, invalidateRenderWord } from '@/lib/api/renderCache';
import { polylineToPathD, ringsToPathD } from '@/lib/svg';
import { de } from '@/locales/admin';
import { PairEditorDialog } from '@/sections/admin/pairs/PairEditorDialog';
import { pairKeysOf } from '@/sections/admin/pairs/pairKeys';
import { garamond } from '@/styles/paper';

const FACE_H = 220; // px per face — words are wide, keep cards scannable

export type WordCompareMode = 'words' | 'pairs' | 'other';

function matchesMode(s: WordSampleOut, mode: WordCompareMode): boolean {
  // Truthiness, not != null: an empty set tag must not count as another hand.
  if (mode === 'other') return !!s.sample_set;
  if (s.sample_set) return false;
  return mode === 'pairs' ? s.kind === 'pair' : s.kind === 'word';
}

// Engine ink drawn into the specimen's pixel frame. Same transform idea as
// CropWrittenOverlay for single glyphs, but the composed word already has its
// own x-layout — only left-align it to the crop (specimen boxes are tight).
function SpecimenOverlay({ sample, composed, sourceId }: { sample: WordSampleOut; composed: ComposedWordOut; sourceId: string }) {
  const unitPx = sample.baseline_y - sample.midband_y; // px per template unit
  const ex = -composed.bounds.min_x * unitPx; // engine left edge → crop left edge
  const matrix = `matrix(${unitPx} 0 0 ${-unitPx} ${ex} ${sample.baseline_y})`;
  const scale = FACE_H / sample.height;
  return (
    <svg
      width={sample.width * scale}
      height={FACE_H}
      viewBox={`0 0 ${sample.width} ${sample.height}`}
      style={{ display: 'block', background: '#fff', maxWidth: '100%' }}
    >
      <image
        href={wordSampleCropUrl(sourceId, sample.id)}
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
              d={polylineToPathD(it.centerline)}
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
  score,
  onOpenEditor,
}: {
  sample: WordSampleOut;
  sourceId: string;
  overlay: boolean;
  score?: WordSampleScoreOut;
  onOpenEditor?: () => void;
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
    fetchRenderWord(sourceId, sample.word)
      .then((c) => {
        if (!cancelled) setComposed(c);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [inView, sourceId, sample.word]);

  const cropW = (FACE_H / sample.height) * sample.width;

  return (
    <Box ref={ref} sx={{ border: 1, borderColor: 'divider', borderRadius: 2, p: 2, bgcolor: 'background.paper', display: 'flex', flexDirection: 'column', gap: 1 }}>
      <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, flexWrap: 'wrap' }}>
        <Typography sx={{ fontFamily: garamond, fontSize: 24, lineHeight: 1 }}>{sample.word}</Typography>
        <Typography variant="caption" color="text.secondary">
          {sample.id}
        </Typography>
        {sample.sample_set && <Chip size="small" label={sample.sample_set} />}
        {score && <ScoreChip score={score} />}
        {composed && composed.missing.length > 0 && (
          <Chip size="small" color="warning" label={`${de.admin.compare.missingPrefix}${composed.missing.join(', ')}`} />
        )}
        {onOpenEditor && (
          <Button size="small" variant="text" onClick={onOpenEditor} sx={{ ml: 'auto' }}>
            {de.admin.compare.openPairEditor}
          </Button>
        )}
      </Box>

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
              <SpecimenOverlay sample={sample} composed={composed} sourceId={sourceId} />
            </Box>
          </Box>
        )
      ) : (
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', alignItems: 'flex-start' }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, minWidth: 0 }}>
            <Typography variant="caption" color="text.secondary">
              {de.admin.compare.colCrop}
            </Typography>
            <Box sx={{ height: FACE_H, display: 'flex', alignItems: 'center', bgcolor: '#fff', borderRadius: 1, px: 1 }}>
              <img
                src={wordSampleCropUrl(sourceId, sample.id)}
                alt={`${de.admin.compare.specimenAlt} ${sample.word}`}
                width={cropW}
                height={FACE_H}
                loading="lazy"
                decoding="async"
                style={{ display: 'block', maxWidth: '100%', objectFit: 'contain' }}
              />
            </Box>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, minWidth: 0 }}>
            <Typography variant="caption" color="text.secondary">
              {de.admin.compare.colWritten}
            </Typography>
            <Box sx={{ height: FACE_H, display: 'flex', alignItems: 'center', bgcolor: '#fff', borderRadius: 1, px: 1 }}>
              <WrittenWord text={sample.word} sourceId={sourceId} height={FACE_H * 0.9} animate={false} showLineature />
            </Box>
          </Box>
        </Box>
      )}
    </Box>
  );
}

export function WordComparison({ mode, overlay }: { mode: WordCompareMode; overlay: boolean }) {
  const { source, sourceId } = useAdmin();
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

  useEffect(() => {
    let cancelled = false;
    setSamples(null);
    setError(false);
    setScores({});
    setScoring(null);
    setScoreError(false);
    setEditing(null); // an open pair editor must not outlive its source
    scoringRun.current += 1; // invalidate an in-flight score sweep of the old source
    getWordSamples(sourceId, { retries: 2 })
      .then((rows) => {
        if (!cancelled) setSamples(rows);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [sourceId]);

  const visible = useMemo(() => {
    const rows = (samples ?? []).filter((s) => matchesMode(s, mode));
    // Once scored, worst first — that IS the work list. Unscored rows keep
    // their sidecar order at the end. Deliberately NOT while the sweep runs:
    // re-sorting per incoming score would make the cards jump on every
    // completed request; the chips fill in place, the ranking lands once.
    return rows.length && !scoring && Object.keys(scores).length
      ? [...rows].sort((a, b) => (scores[b.id]?.loss ?? -1) - (scores[a.id]?.loss ?? -1))
      : rows;
  }, [samples, mode, scores, scoring]);

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
  if (visible.length === 0) return <Alert severity="info">{de.admin.compare.wordsEmpty}</Alert>;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 1100 }}>
      <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 720 }}>
        {mode === 'other' ? de.admin.compare.otherIntro : de.admin.compare.wordsIntro}
      </Typography>
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
        </Box>
      )}
      {visible.map((s) => {
        // A pair card links straight into the pair editor (redesign R1b →
        // R3 circle) — with its specimen crop as the editor's underlay.
        const keys = mode === 'pairs' ? pairKeysOf(s.word) : null;
        return (
          <WordCard
            // The tick remounts the card after an override save, so its
            // "as written" render refetches the just-changed composition.
            key={`${s.id}:${cardTick[s.id] ?? 0}`}
            sample={s}
            sourceId={sourceId}
            overlay={overlay}
            score={scores[s.id]}
            onOpenEditor={keys ? () => setEditing({ sample: s, left: keys[0], right: keys[1] }) : undefined}
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
