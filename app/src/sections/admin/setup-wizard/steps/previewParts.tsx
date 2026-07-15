// Shared building blocks for the wizard's optimisation/verification surfaces:
// the crop-pixel silhouette overlay, the per-category penalty breakdown ("where
// did the score go") and the score→colour mapping. Used by the inline Weg
// preview (WegPreview, Weg step) and the Übersicht verification panel
// (OverviewVerify) so both render the comparison identically.

import { Box, LinearProgress, Stack, Tooltip, Typography } from '@mui/material';

import { ringsToPathD } from '@/lib/svg';
import { de } from '@/locales/admin';
import type { QualityData, WrittenPreviewData } from '@/lib/api';

export function scoreColor(score: number): 'success' | 'warning' | 'error' {
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
export function ScoreBreakdown({ quality }: { quality: QualityData }) {
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

// Silhouette rings (crop pixels) as one evenodd SVG path per pen-stroke — loop
// counters stay open. silhouette_px is the per-stroke ring list from the
// preview payload (the optimized render in crop coordinates, aligned to the crop
// image so it overlays exactly).
export function SilhouetteSvg({
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
