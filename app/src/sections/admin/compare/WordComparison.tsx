// Word comparison (redesign R1b, stage 1) — the connected-writing specimens of
// the source (words.json sidecar via /word-samples) next to the SAME word
// composed by the engine (/write/word). Two modes like GlyphComparison: side by
// side, or the engine ink projected onto the specimen pixels. The overlay
// registration is exact, not eyeballed: the sidecar carries the specimen's
// crop-local baseline/midband, the composed word lives in template units
// (baseline = 0, 1 unit = x-height), so the map is a pure scale+translate —
// scale = (baseline_y - midband_y) px per unit, left-aligned on the crop edge.

import { Alert, Box, Chip, CircularProgress, Typography } from '@mui/material';
import { useEffect, useMemo, useState } from 'react';

import { WrittenWord } from '@/components/WrittenWord';
import { useAdmin } from '@/context/AdminContext';
import { useInView } from '@/hooks/useInView';
import { getWordSamples, wordSampleCropUrl } from '@/lib/api';
import type { ComposedWordOut, WordSampleOut } from '@/lib/api';
import { fetchRenderWord } from '@/lib/api/renderCache';
import { polylineToPathD, ringsToPathD } from '@/lib/svg';
import { de } from '@/locales/admin';
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

function WordCard({ sample, sourceId, overlay }: { sample: WordSampleOut; sourceId: string; overlay: boolean }) {
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
        {composed && composed.missing.length > 0 && (
          <Chip size="small" color="warning" label={`${de.admin.compare.missingPrefix}${composed.missing.join(', ')}`} />
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

  useEffect(() => {
    let cancelled = false;
    setSamples(null);
    setError(false);
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

  const visible = useMemo(() => (samples ?? []).filter((s) => matchesMode(s, mode)), [samples, mode]);

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
      {visible.map((s) => (
        <WordCard key={s.id} sample={s} sourceId={sourceId} overlay={overlay} />
      ))}
    </Box>
  );
}
