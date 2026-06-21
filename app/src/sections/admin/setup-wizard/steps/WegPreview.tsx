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
import {
  Box,
  Chip,
  CircularProgress,
  LinearProgress,
  Stack,
  ToggleButton,
  Tooltip,
  Typography,
} from '@mui/material';
import { useEffect, useRef } from 'react';

import { useAdmin } from '@/context/AdminContext';
import { cropUrl } from '@/lib/api';
import type { QualityData, TracePreviewOut, WrittenPreviewData } from '@/lib/api';
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

const PANEL_W = 240;

function scoreColor(score: number): 'success' | 'warning' | 'error' {
  if (score >= 85) return 'success';
  if (score >= 70) return 'warning';
  return 'error';
}

// Naturalness-metric components shown as the per-category penalty breakdown
// (Sütterlin/Gleichzug only — the Kurrent metric carries no `components`). Order
// mirrors the glyph bench's stdout; `naturalness` is the aggregate, not a
// category, so it's excluded here.
type ComponentKey = 'smoothness' | 'verticality' | 'corner' | 'collinearity' | 'retrace' | 'coverage';
const COMPONENT_KEYS: ComponentKey[] = ['smoothness', 'verticality', 'corner', 'collinearity', 'retrace', 'coverage'];
const NOTABLE_PENALTY = 0.15; // mirrors glyphlab's _SCORE_HI — a deduction worth flagging
const PENALTY_EPS = 0.005; // below this a category is effectively perfect / not applicable
const BAR_FULL_PENALTY = 0.3; // penalty mapped to a full bar (penalties rarely exceed this)

function penaltyColor(val: number): 'error' | 'warning' | 'primary' {
  if (val >= 0.25) return 'error';
  if (val >= NOTABLE_PENALTY) return 'warning';
  return 'primary';
}

// "Where did the points go" — the optimized form's deductions per category,
// sorted worst-first, just like the glyph bench / glyphlab caption.
function ScoreBreakdown({ quality }: { quality: QualityData }) {
  const t = de.wizard.optimize;
  const c = quality.components;
  if (!c) return null; // Kurrent metric: no per-category breakdown
  const rows = COMPONENT_KEYS.map((key) => ({ key, val: c[key] }))
    .filter((r) => r.val >= PENALTY_EPS)
    .sort((a, b) => b.val - a.val);
  return (
    <Stack spacing={0.75} sx={{ maxWidth: 360 }}>
      <Typography variant="caption" color="text.secondary">
        {t.breakdownHeading}
      </Typography>
      {rows.length === 0 ? (
        <Typography variant="caption" color="success.main">
          {t.breakdownNone}
        </Typography>
      ) : (
        rows.map((r) => {
          const color = penaltyColor(r.val);
          return (
            <Box key={r.key} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Tooltip title={t.catHint[r.key]} placement="left">
                {/* tabIndex so keyboard focus (not just hover) triggers the hint */}
                <Typography
                  variant="caption"
                  tabIndex={0}
                  sx={{ width: 78, flexShrink: 0, fontFamily: 'monospace', cursor: 'help' }}
                >
                  {t.cat[r.key]}
                </Typography>
              </Tooltip>
              <LinearProgress
                variant="determinate"
                value={Math.min(r.val / BAR_FULL_PENALTY, 1) * 100}
                color={color}
                sx={{ flex: 1, height: 6, borderRadius: 1, opacity: r.val >= NOTABLE_PENALTY ? 1 : 0.5 }}
              />
              <Typography
                variant="caption"
                sx={{ width: 36, textAlign: 'right', fontFamily: 'monospace' }}
                color={color === 'primary' ? 'text.secondary' : `${color}.main`}
              >
                {r.val.toFixed(2)}
              </Typography>
            </Box>
          );
        })
      )}
      <Typography variant="caption" color="text.disabled">
        {t.breakdownHint}
      </Typography>
    </Stack>
  );
}

// Silhouette rings (crop pixels) as one evenodd SVG path — loop counters stay
// open. silhouette_px is the per-stroke ring list from the preview payload.
function SilhouetteSvg({ data, w, h, fill, fillOpacity = 1 }: { data: WrittenPreviewData; w: number; h: number; fill: string; fillOpacity?: number }) {
  const strokes = data.silhouette_px ?? [];
  return (
    <svg width={w} height={h} viewBox={`0 0 ${data.crop_size.w} ${data.crop_size.h}`} style={{ display: 'block' }}>
      {strokes.map((rings, i) => (
        <path key={i} d={ringsToPathD(rings)} fill={fill} fillOpacity={fillOpacity} fillRule="evenodd" />
      ))}
    </svg>
  );
}

export function WegPreview({ glyphKey, cropCacheBust, hasDraftSource, nAnchors, preview, previewBusy, computePreview }: Props) {
  const { sourceId } = useAdmin();
  const t = de.wizard.optimize;

  // Auto-compute the comparison once when a saved Weg exists without a preview.
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

  if (!hasDraftSource) return null;

  const cropW = preview?.refined.crop_size.w ?? 1;
  const cropH = preview?.refined.crop_size.h ?? 1;
  const panelH = (PANEL_W * cropH) / cropW;
  const delta =
    preview?.raw.quality && preview?.refined.quality ? preview.refined.quality.score - preview.raw.quality.score : null;

  return (
    <Stack spacing={1} sx={{ borderTop: 1, borderColor: 'divider', pt: 1.5 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="subtitle2" sx={{ flex: 1 }}>
          {t.title}
        </Typography>
        <Tooltip title={t.recompute}>
          <span>
            <ToggleButton value="recompute" size="small" selected={false} disabled={previewBusy} onChange={() => void computePreview(nAnchors)}>
              <RefreshIcon fontSize="small" />
            </ToggleButton>
          </span>
        </Tooltip>
      </Box>
      <Typography variant="caption" color="text.secondary">
        {t.body}
      </Typography>

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
          <Typography variant="caption" color="text.disabled">
            {t.overlayCaption}
          </Typography>
          {preview.refined.quality && <ScoreBreakdown quality={preview.refined.quality} />}
        </>
      )}
    </Stack>
  );
}
