// M4 fit overlay: the canonical template fitted to its own crop skeleton.
//
// Backend (`core.fit.fit_glyph_to_crop`) optimises the template control points
// against the instance skeleton + distance transform and returns crop-local
// overlay polylines. This view draws them over the crop — skeleton (faint),
// canonical placement (grey), fitted result (red) — plus the fit diagnostics,
// with a live lambda_reg slider showing the regularisation trade-off.

import RefreshIcon from '@mui/icons-material/Refresh';
import { Alert, Box, Button, Chip, CircularProgress, Slider, Stack, Typography } from '@mui/material';
import { useCallback, useEffect, useState } from 'react';

import { cropUrl, getFit } from '@/lib/api';
import type { FitData } from '@/lib/api';
import { de } from '@/locales';
import { useColumnWidth } from '@/sections/admin/diagnostics/useColumnWidth';

interface Props {
  glyphKey: string;
  cropCacheBust?: number;
  // Override the responsive default overlay width (the Diagnose modal goes big);
  // still clamped to the viewport.
  colWidth?: number;
  colHeight?: number;
}

const COL_H = 360;

function polylinePoints(pts: Array<[number, number]>): string {
  return pts.map(([x, y]) => `${x},${y}`).join(' ');
}

// Split a sampled polyline at the pen-stroke boundaries so the overlay draws each
// stroke on its own instead of bridging a pen lift. Missing/[0] => one stroke.
function polylineSegments(pts: Array<[number, number]>, starts?: number[]): Array<Array<[number, number]>> {
  if (!starts || starts.length <= 1) return [pts];
  return starts.map((a, i) => pts.slice(a, i + 1 < starts.length ? starts[i + 1] : pts.length));
}

export function FitView({ glyphKey, cropCacheBust, colWidth, colHeight }: Props) {
  const COL_W = useColumnWidth(colWidth);
  const COL_H_PX = colHeight ?? COL_H;
  const [data, setData] = useState<FitData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lambda, setLambda] = useState(1.0);

  const fetchFit = useCallback(
    (lambdaReg: number) => {
      setLoading(true);
      setError(null);
      getFit(glyphKey, lambdaReg)
        .then((d) => setData(d))
        .catch((e) => setError(String(e)))
        .finally(() => setLoading(false));
    },
    [glyphKey],
  );

  useEffect(() => {
    fetchFit(lambda);
    // Re-fit on glyph change / crop edits; lambda changes go through the slider commit.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [glyphKey, cropCacheBust]);

  if (loading && !data) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 2 }}>
        <CircularProgress size={16} />
        <Typography variant="caption" color="text.secondary">
          {de.admin.fit.computing}
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity={error.includes('404') ? 'info' : 'error'}>
          {error.includes('404') ? de.admin.diagnostics.noCanonicalShort : error}
        </Alert>
        <Button size="small" startIcon={<RefreshIcon />} onClick={() => fetchFit(lambda)} sx={{ mt: 1 }}>
          {de.admin.diagnostics.reload}
        </Button>
      </Box>
    );
  }

  if (!data) return null;

  const cropW = data.crop_size.w;
  const cropH = data.crop_size.h;
  const scale = Math.min(COL_W / cropW, COL_H_PX / cropH);
  const displayW = cropW * scale;
  const displayH = cropH * scale;
  const m = data.fit;

  return (
    <Stack spacing={1.5}>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'flex-start' }}>
        {/* Overlay: crop + skeleton + canonical (grey) + fit (red) */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          <Typography variant="caption" color="text.secondary">
            {de.admin.fit.overlayHeading}
          </Typography>
          <Box sx={{ position: 'relative', width: displayW, height: displayH, bgcolor: '#fff' }}>
            <img
              src={cropUrl(glyphKey, cropCacheBust)}
              alt="fit-overlay"
              width={displayW}
              height={displayH}
              style={{ display: 'block', position: 'absolute', inset: 0, opacity: 0.3 }}
            />
            <svg
              width={displayW}
              height={displayH}
              viewBox={`0 0 ${cropW} ${cropH}`}
              style={{ position: 'absolute', inset: 0 }}
            >
              {/* skeleton points */}
              {data.skeleton_polyline_px.map(([x, y], i) => (
                <circle key={i} cx={x} cy={y} r={0.6} fill="#ff8080" />
              ))}
              {/* canonical placement (pre-fit) — one polyline per pen-stroke */}
              {polylineSegments(data.canonical_polyline_px, data.polyline_stroke_starts).map((seg, i) => (
                <polyline key={`canon-${i}`} fill="none" stroke="#888" strokeWidth={1.4} strokeDasharray="4 3" points={polylinePoints(seg)} />
              ))}
              {/* fitted result — one polyline per pen-stroke */}
              {polylineSegments(data.fitted_polyline_px, data.polyline_stroke_starts).map((seg, i) => (
                <polyline key={`fit-${i}`} fill="none" stroke="#e02030" strokeWidth={2} points={polylinePoints(seg)} />
              ))}
            </svg>
          </Box>
        </Box>

        {/* Fit diagnostics */}
        <Stack spacing={0.75} sx={{ minWidth: 180 }}>
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            <Chip
              size="small"
              color={m.success ? 'success' : 'warning'}
              label={m.success ? de.admin.fit.converged : de.admin.fit.notConverged}
            />
            <Chip size="small" variant="outlined" label={`${m.iterations} ${de.admin.fit.iterations}`} />
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
            {de.admin.fit.geoRmse} {m.geo_rmse_px_initial} → <strong>{m.geo_rmse_px}</strong> px
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
            {de.admin.fit.widthRmse} {m.width_rmse_px} px
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
            {de.admin.fit.maxAnchorDelta} {m.max_anchor_delta} · λ={m.lambda_reg}
          </Typography>
          <Typography variant="caption" color="text.disabled">
            {de.admin.fit.lambdaHint}
          </Typography>
        </Stack>
      </Box>

      {/* lambda_reg slider */}
      <Box sx={{ px: 1 }}>
        <Typography variant="caption" color="text.secondary">
          {de.admin.fit.regularization} {lambda.toFixed(2)}
        </Typography>
        <Slider
          size="small"
          min={0.01}
          max={5}
          step={0.01}
          value={lambda}
          onChange={(_e, v) => setLambda(v as number)}
          onChangeCommitted={(_e, v) => fetchFit(v as number)}
          valueLabelDisplay="auto"
        />
      </Box>
    </Stack>
  );
}
