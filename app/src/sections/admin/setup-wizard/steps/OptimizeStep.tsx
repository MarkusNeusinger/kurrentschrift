// Step 5 "Optimieren" — the raw-vs-optimized comparison before anything is saved.
//
// The drawn Weg is derived twice server-side (POST trace-preview, a dry run):
// once raw (widths measured point-by-point, anchors only snapped) and once
// optimized (anchors + widths pulled onto the ink edge, corner knots kept
// sharp). Both render as written glyphs side by side with their image-space
// quality scores; only "Anwenden & speichern" persists the optimized form.

import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import RefreshIcon from '@mui/icons-material/Refresh';
import { Alert, Box, Button, Chip, CircularProgress, Stack, Typography } from '@mui/material';
import { useEffect, useRef } from 'react';

import { WrittenGlyph } from '@/components/WrittenGlyph';
import { de } from '@/locales';
import type { TracePreviewOut, WrittenPreviewData } from '@/lib/api';

interface Props {
  glyphKey: string;
  hasDraftSource: boolean; // strokes drawn OR a stored canonical to re-optimize
  nAnchors: number;
  draftReady: boolean;
  preview: TracePreviewOut | null;
  previewBusy: boolean;
  optimizeApplied: boolean;
  busy: boolean;
  prepareOptimize: (nAnchors: number) => Promise<void>;
  applyOptimized: () => Promise<void>;
}

function scoreColor(score: number): 'success' | 'warning' | 'error' {
  if (score >= 85) return 'success';
  if (score >= 70) return 'warning';
  return 'error';
}

function Variant({ title, cacheKey, data }: { title: string; cacheKey: string; data: WrittenPreviewData }) {
  const t = de.wizard.optimize;
  return (
    <Stack spacing={0.75} sx={{ alignItems: 'flex-start', minWidth: 220 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="caption" color="text.secondary">
          {title}
        </Typography>
        {data.quality && <Chip size="small" color={scoreColor(data.quality.score)} label={`${t.score} ${data.quality.score.toFixed(1)}`} />}
      </Box>
      {/* The synthetic cacheKey keeps preview payloads out of the real glyph's
          WrittenGlyph cache (quiz/diagnostics must never see a raw variant). */}
      <WrittenGlyph glyphKey={cacheKey} data={data} height={220} />
    </Stack>
  );
}

export function OptimizeStep({
  glyphKey,
  hasDraftSource,
  nAnchors,
  draftReady,
  preview,
  previewBusy,
  optimizeApplied,
  busy,
  prepareOptimize,
  applyOptimized,
}: Props) {
  const t = de.wizard.optimize;

  // Entering the step without a prepared draft (footer "Weiter" instead of the
  // Weg step's button) computes the comparison once automatically; failures
  // fall through to the manual "Neu berechnen" button.
  const autoRan = useRef(false);
  useEffect(() => {
    if (!autoRan.current && hasDraftSource && !draftReady && !previewBusy) {
      autoRan.current = true;
      void prepareOptimize(nAnchors);
    }
  }, [hasDraftSource, draftReady, previewBusy, nAnchors, prepareOptimize]);

  const delta =
    preview?.raw.quality && preview?.refined.quality ? preview.refined.quality.score - preview.raw.quality.score : null;

  return (
    <Stack spacing={1.5}>
      <Typography variant="subtitle2">{t.title}</Typography>
      <Typography variant="body2" color="text.secondary">
        {t.body}
      </Typography>

      {!hasDraftSource && <Alert severity="info">{t.needTrace}</Alert>}

      {previewBusy && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 2 }}>
          <CircularProgress size={16} />
          <Typography variant="caption" color="text.secondary">
            {t.computing}
          </Typography>
        </Box>
      )}

      {preview && !previewBusy && (
        <>
          <Box sx={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            <Variant title={t.before} cacheKey={`${glyphKey}#preview-raw`} data={preview.raw} />
            <Variant title={t.after} cacheKey={`${glyphKey}#preview-refined`} data={preview.refined} />
          </Box>
          {delta != null && (
            <Typography variant="body2" sx={{ fontFamily: 'monospace' }} color={delta >= 0 ? 'success.main' : 'error.main'}>
              {t.delta} {delta >= 0 ? '+' : ''}
              {delta.toFixed(1)}
            </Typography>
          )}
        </>
      )}

      {optimizeApplied && <Alert severity="success">{t.applied}</Alert>}

      <Stack direction="row" spacing={1}>
        <Button
          size="small"
          variant="contained"
          startIcon={busy ? <CircularProgress size={14} color="inherit" /> : <AutoFixHighIcon />}
          disabled={!draftReady || previewBusy || busy || optimizeApplied}
          onClick={() => void applyOptimized()}
        >
          {t.apply}
        </Button>
        <Button
          size="small"
          variant="outlined"
          startIcon={<RefreshIcon />}
          disabled={!hasDraftSource || previewBusy || busy}
          onClick={() => void prepareOptimize(nAnchors)}
        >
          {t.recompute}
        </Button>
      </Stack>
    </Stack>
  );
}
