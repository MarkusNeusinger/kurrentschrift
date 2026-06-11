// Step 5 "Optimieren" — Crop · Vorher · Nachher comparison of the saved Weg.
//
// The Weg is already saved on step 4 (the pipeline optimizes on every save).
// This step derives the drawn/stored Weg twice server-side (POST trace-preview,
// a dry run): once raw (widths measured point-by-point, anchors only snapped)
// and once optimized (anchors + widths pulled onto the ink edge, corner knots
// kept sharp). Two views:
//   · Nebeneinander — Original crop, raw, optimized, all the same size, so the
//     optimization is visible at a glance (with image-space quality scores).
//   · Überlagert — the optimized silhouette drawn semi-transparent over the
//     crop, so areas where it under-/over-covers the ink stand out.

import RefreshIcon from '@mui/icons-material/Refresh';
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { useEffect, useRef, useState } from 'react';

import { cropUrl } from '@/lib/api';
import type { TracePreviewOut, WrittenPreviewData } from '@/lib/api';
import { ringsToPathD } from '@/lib/svg';
import { de } from '@/locales';

interface Props {
  glyphKey: string;
  cropCacheBust?: number;
  hasDraftSource: boolean; // strokes drawn OR a stored canonical to compare
  nAnchors: number;
  preview: TracePreviewOut | null;
  previewBusy: boolean;
  computePreview: (nAnchors: number) => Promise<void>;
}

const PANEL_H = 240;

function scoreColor(score: number): 'success' | 'warning' | 'error' {
  if (score >= 85) return 'success';
  if (score >= 70) return 'warning';
  return 'error';
}

// Silhouette rings (crop pixels) as one evenodd SVG path — loop counters stay
// open. silhouette_px is the per-stroke ring list from the preview payload.
function SilhouetteSvg({
  data,
  w,
  h,
  fill,
  fillOpacity = 1,
}: {
  data: WrittenPreviewData;
  w: number;
  h: number;
  fill: string;
  fillOpacity?: number;
}) {
  const strokes = data.silhouette_px ?? [];
  return (
    <svg width={w} height={h} viewBox={`0 0 ${data.crop_size.w} ${data.crop_size.h}`} style={{ display: 'block' }}>
      {strokes.map((rings, i) => (
        <path key={i} d={ringsToPathD(rings)} fill={fill} fillOpacity={fillOpacity} fillRule="evenodd" />
      ))}
    </svg>
  );
}

function Panel({ title, chip, children, w }: { title: string; chip?: React.ReactNode; children: React.ReactNode; w: number }) {
  return (
    <Stack spacing={0.5} sx={{ alignItems: 'flex-start' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minHeight: 24 }}>
        <Typography variant="caption" color="text.secondary">
          {title}
        </Typography>
        {chip}
      </Box>
      <Box sx={{ width: w, height: PANEL_H, bgcolor: '#fff', border: 1, borderColor: 'divider', position: 'relative' }}>
        {children}
      </Box>
    </Stack>
  );
}

export function OptimizeStep({ glyphKey, cropCacheBust, hasDraftSource, nAnchors, preview, previewBusy, computePreview }: Props) {
  const t = de.wizard.optimize;
  const [view, setView] = useState<'side' | 'overlay'>('side');

  // Auto-compute the comparison once when the step is reached without a preview.
  const autoRan = useRef(false);
  useEffect(() => {
    if (!autoRan.current && hasDraftSource && !preview && !previewBusy) {
      autoRan.current = true;
      void computePreview(nAnchors);
    }
  }, [hasDraftSource, preview, previewBusy, nAnchors, computePreview]);
  // Re-arm the auto-run when the glyph changes (the parent clears `preview`).
  useEffect(() => {
    if (!preview) autoRan.current = false;
  }, [preview, glyphKey]);

  const cropW = preview?.refined.crop_size.w ?? 1;
  const cropH = preview?.refined.crop_size.h ?? 1;
  const panelW = (PANEL_H * cropW) / cropH;
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
          <ToggleButtonGroup size="small" exclusive value={view} onChange={(_e, v: 'side' | 'overlay' | null) => v && setView(v)}>
            <ToggleButton value="side">{t.viewSide}</ToggleButton>
            <ToggleButton value="overlay">{t.viewOverlay}</ToggleButton>
          </ToggleButtonGroup>

          {view === 'side' ? (
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'flex-start' }}>
              <Panel title={t.crop} w={panelW}>
                <img
                  src={cropUrl(glyphKey, cropCacheBust)}
                  alt="crop"
                  width={panelW}
                  height={PANEL_H}
                  style={{ display: 'block', objectFit: 'fill' }}
                />
              </Panel>
              <Panel
                title={t.before}
                w={panelW}
                chip={preview.raw.quality && <Chip size="small" color={scoreColor(preview.raw.quality.score)} label={`${t.score} ${preview.raw.quality.score.toFixed(1)}`} />}
              >
                <SilhouetteSvg data={preview.raw} w={panelW} h={PANEL_H} fill="#111" />
              </Panel>
              <Panel
                title={t.after}
                w={panelW}
                chip={preview.refined.quality && <Chip size="small" color={scoreColor(preview.refined.quality.score)} label={`${t.score} ${preview.refined.quality.score.toFixed(1)}`} />}
              >
                <SilhouetteSvg data={preview.refined} w={panelW} h={PANEL_H} fill="#111" />
              </Panel>
            </Box>
          ) : (
            <Stack spacing={0.5} sx={{ alignItems: 'flex-start' }}>
              <Typography variant="caption" color="text.secondary">
                {t.overlayHeading}
              </Typography>
              <Box sx={{ width: panelW, height: PANEL_H, bgcolor: '#fff', border: 1, borderColor: 'divider', position: 'relative' }}>
                <img
                  src={cropUrl(glyphKey, cropCacheBust)}
                  alt="crop"
                  width={panelW}
                  height={PANEL_H}
                  style={{ display: 'block', position: 'absolute', inset: 0, objectFit: 'fill' }}
                />
                <Box sx={{ position: 'absolute', inset: 0 }}>
                  <SilhouetteSvg data={preview.refined} w={panelW} h={PANEL_H} fill="#e02030" fillOpacity={0.45} />
                </Box>
              </Box>
              <Typography variant="caption" color="text.disabled" sx={{ maxWidth: 420 }}>
                {t.overlayCaption}
              </Typography>
            </Stack>
          )}

          {delta != null && (
            <Typography variant="body2" sx={{ fontFamily: 'monospace' }} color={delta >= 0 ? 'success.main' : 'error.main'}>
              {t.delta} {delta >= 0 ? '+' : ''}
              {delta.toFixed(1)}
            </Typography>
          )}
        </>
      )}

      {hasDraftSource && (
        <Box>
          <ToggleButton value="recompute" size="small" selected={false} disabled={previewBusy} onChange={() => void computePreview(nAnchors)}>
            <RefreshIcon fontSize="small" />
            &nbsp;{t.recompute}
          </ToggleButton>
        </Box>
      )}
    </Stack>
  );
}
