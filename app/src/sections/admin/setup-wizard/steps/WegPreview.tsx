// Inline Weg preview — the optimized silhouette laid over the crop, its score
// and the per-category penalty breakdown, shown under the Weg controls once a
// canonical is saved. It answers "did the optimisation land?" at a glance; the
// full raw-vs-optimized analysis (and the per-glyph re-derive) lives in the
// single Diagnose modal.
//
// The Weg is saved on the same step (the pipeline optimizes on every save); this
// derives the stored raw_path once more server-side (POST trace-preview, a dry
// run) and renders the optimized silhouette over the crop.

import RefreshIcon from '@mui/icons-material/Refresh';
import { Box, Chip, CircularProgress, Stack, ToggleButton, Tooltip, Typography } from '@mui/material';
import { useEffect, useRef } from 'react';

import { useAdmin } from '@/context/AdminContext';
import { cropUrl } from '@/lib/api';
import type { TracePreviewOut } from '@/lib/api';
import { de } from '@/locales/admin';
import { HintHeading } from './HintHeading';
import { ScoreBreakdown, SilhouetteSvg, scoreColor } from './previewParts';

interface Props {
  glyphKey: string;
  cropCacheBust?: number;
  hasDraftSource: boolean; // strokes drawn OR a stored canonical to compare
  nAnchors: number;
  preview: TracePreviewOut | null;
  previewBusy: boolean;
  computePreview: (nAnchors: number) => Promise<void>;
}

const PANEL_W = 240;

export function WegPreview({ glyphKey, cropCacheBust, hasDraftSource, nAnchors, preview, previewBusy, computePreview }: Props) {
  const { sourceId } = useAdmin();
  const t = de.wizard.optimize;

  // Re-arm when the glyph changes so the next glyph computes fresh. Declared
  // before the compute effect so a glyph switch resets the marker before it runs.
  const lastComputed = useRef<number | null>(null);
  useEffect(() => {
    lastComputed.current = null;
  }, [glyphKey]);
  // Auto-compute when a saved Weg exists, and recompute whenever the anchor count
  // changes (a re-save with a different n_anchors). `nAnchors` is the saved
  // canonical's authoritative count (see the parent), not the possibly-lagging
  // bbox value, so the preview always matches what was actually stored.
  useEffect(() => {
    if (hasDraftSource && !previewBusy && lastComputed.current !== nAnchors) {
      lastComputed.current = nAnchors;
      void computePreview(nAnchors);
    }
  }, [hasDraftSource, previewBusy, nAnchors, computePreview]);

  if (!hasDraftSource) return null;

  const cropW = preview?.refined.crop_size.w ?? 1;
  const cropH = preview?.refined.crop_size.h ?? 1;
  const panelH = (PANEL_W * cropH) / cropW;
  const delta =
    preview?.raw.quality && preview?.refined.quality ? preview.refined.quality.score - preview.raw.quality.score : null;

  return (
    <Stack spacing={1} sx={{ borderTop: 1, borderColor: 'divider', pt: 1.5 }}>
      <HintHeading
        title={t.title}
        action={
          <Tooltip title={t.recompute}>
            <span>
              <ToggleButton value="recompute" size="small" selected={false} disabled={previewBusy} aria-label={t.recompute} onChange={() => void computePreview(nAnchors)}>
                <RefreshIcon fontSize="small" />
              </ToggleButton>
            </span>
          </Tooltip>
        }
      >
        <Typography variant="body2" gutterBottom>
          {t.body}
        </Typography>
        <Typography variant="body2">{t.overlayCaption}</Typography>
      </HintHeading>

      {previewBusy && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 1 }}>
          <CircularProgress size={16} />
          <Typography variant="caption" color="text.secondary">
            {t.computing}
          </Typography>
        </Box>
      )}

      {preview && !previewBusy && (
        <>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {preview.refined.quality && (
              <Chip size="small" color={scoreColor(preview.refined.quality.score)} label={`${t.score} ${preview.refined.quality.score.toFixed(1)}`} />
            )}
            {delta != null && (
              <Typography variant="caption" sx={{ fontFamily: 'monospace' }} color={delta >= 0 ? 'success.main' : 'error.main'}>
                {t.delta} {delta >= 0 ? '+' : ''}
                {delta.toFixed(1)}
              </Typography>
            )}
          </Box>
          <Box sx={{ width: PANEL_W, height: panelH, bgcolor: '#fff', border: 1, borderColor: 'divider', position: 'relative' }}>
            <img
              src={cropUrl(sourceId, glyphKey, cropCacheBust)}
              alt="crop"
              width={PANEL_W}
              height={panelH}
              style={{ display: 'block', position: 'absolute', inset: 0, objectFit: 'fill' }}
            />
            <Box sx={{ position: 'absolute', inset: 0 }}>
              <SilhouetteSvg data={preview.refined} w={PANEL_W} h={panelH} fill="#e02030" fillOpacity={0.45} />
            </Box>
          </Box>
          {preview.refined.quality && <ScoreBreakdown quality={preview.refined.quality} />}
        </>
      )}
    </Stack>
  );
}
