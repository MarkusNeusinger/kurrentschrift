// One Wortprobe as a card — the plate's crop and the same word „wie
// geschrieben", or the engine's ink projected onto the plate pixels.
//
// A pure move out of `WordComparison.tsx`, where this component and its overlay
// sat inline: since V14 the card is mounted from TWO places — the gallery of
// the Wörter overview, and an expanded row of its work list — and a list module
// that had to import the whole grid to reach one card would pull the grid's
// fetching with it.
//
// The overlay registration is exact, not eyeballed: the sidecar carries the
// specimen's crop-local baseline/midband, the composed word lives in template
// units (baseline = 0, 1 unit = x-height), so the map is a pure scale+translate
// — and wherever the row carries a MEASURED registration of its own
// (`traceFrameOf`), that one wins over pinning the composition's left edge to
// the crop's.

import { Alert, Box, Button, Chip, CircularProgress, Tooltip, Typography } from '@mui/material';
import { useEffect, useState, type ReactNode } from 'react';

import { WrittenWord } from '@/components/WrittenWord';
import { useInView } from '@/hooks/useInView';
import { wordSampleCropUrl } from '@/lib/api';
import type { ComposedWordOut, WordInstanceOut, WordSampleOut, WordSampleScoreOut } from '@/lib/api';
import { fetchRenderWord } from '@/lib/api/renderCache';
import { polylineToPathD, ringsToPathD } from '@/lib/svg';
import { de, fmt } from '@/locales/admin';
import { traceFrameOf, traceMatrix, WERKBANK_COLORS, type TraceStatus } from '@/sections/admin/shell/model';
import { layerAlpha, layerDash, garamond } from '@/styles/paper';

const FACE_H = 220; // px per face — words are wide, keep cards scannable

// Engine ink drawn into the specimen's pixel frame.
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
            <path
              key={i}
              d={ringsToPathD(it.rings)}
              fill={WERKBANK_COLORS.engine}
              fillOpacity={layerAlpha.engineOverlay}
              fillRule="evenodd"
            />
          ) : (
            <path
              key={i}
              // flipY off — the enclosing <g> flips already (see lib/svg.ts);
              // with the default every generated Übergang was mirrored below
              // the baseline while the letters sat correctly.
              d={polylineToPathD(it.centerline, 0, false)}
              fill="none"
              stroke={WERKBANK_COLORS.engine}
              strokeOpacity={layerAlpha.engineOverlay}
              strokeWidth={it.stroke_width ?? it.mask_width}
              // The engine layer's own stroke style, so a reader who cannot
              // separate its red from the Bahn's Ocker still can (paper.ts) —
              // the cap comes with it, since the dash alone is only half a
              // stroke style.
              strokeDasharray={layerDash.engine.dash.map((d) => d * (it.stroke_width ?? it.mask_width)).join(' ')}
              strokeLinecap={layerDash.engine.cap}
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

export function ScoreChip({ score }: { score: WordSampleScoreOut }) {
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

export function WordCard({
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
  framed = true,
  header = true,
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
  // The admin-wide reload stamp.
  bust: number;
  score?: WordSampleScoreOut;
  // The „Gemessen" readout — pair cards only (the caller owns the scope), so
  // the card itself stays agnostic of the occurrence/aggregate layers.
  measured?: ReactNode;
  onOpenEditor?: () => void;
  // Open this specimen in the Wörter view — the list is the overview, the
  // detail is where its trace, occurrences and score live.
  onPick?: () => void;
  // Both false inside an expanded work-list row: the row around the card
  // already carries the word, its chips and the way in, and a second frame
  // inside the first reads as two cards.
  framed?: boolean;
  header?: boolean;
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
    <Box
      ref={ref}
      sx={{
        ...(framed
          ? { border: 1, borderColor: 'divider', borderRadius: 2, p: 2, bgcolor: 'background.paper' }
          : { pt: 1 }),
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
      }}
    >
      {header && (
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
            <Chip
              size="small"
              color="warning"
              label={`${de.admin.compare.missingPrefix}${composed.missing.join(', ')}`}
            />
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
      )}

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
