// QualityView — image-space quality of the stored canonical vs a re-derive dry run.
//
// Backend (`GET .../quality`) scores the rendered silhouette against the
// binarized crop twice: `stored` is what the DB holds, `candidate` is what a
// fresh re-derivation from the raw stylus path with the CURRENT pipeline code
// would achieve (nothing written). The admin compares both and applies the
// candidate via /resample — the explicit per-glyph write-back path after
// pipeline improvements land.

import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import RefreshIcon from '@mui/icons-material/Refresh';
import { Alert, Box, Button, Chip, CircularProgress, Stack, Typography } from '@mui/material';
import { useCallback, useEffect, useState } from 'react';

import { useAdmin } from '@/context/AdminContext';
import { getQuality, postResample } from '@/lib/api';
import type { QualityComparison, QualityData } from '@/lib/api';
import { de } from '@/locales';

interface Props {
  glyphKey: string;
  // Bumped by the admin context on every trace/resample — refetches the scores.
  cropCacheBust?: number;
}

function scoreColor(score: number): 'success' | 'warning' | 'error' {
  if (score >= 85) return 'success';
  if (score >= 70) return 'warning';
  return 'error';
}

function MetricCard({ title, q }: { title: string; q: QualityData }) {
  const t = de.admin.quality;
  return (
    <Stack spacing={0.5} sx={{ minWidth: 200 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="caption" color="text.secondary">
          {title}
        </Typography>
        <Chip size="small" color={scoreColor(q.score)} label={`${t.score} ${q.score.toFixed(1)}`} />
      </Box>
      <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
        {t.iou} {q.iou.toFixed(3)}
      </Typography>
      <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
        {t.chamfer} {q.chamfer_mean_px.toFixed(2)} px
      </Typography>
      <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
        {t.geoRmse} {q.geo_rmse_px.toFixed(2)} px
      </Typography>
      <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
        {t.waviness} {q.waviness_ratio.toFixed(2)}
      </Typography>
    </Stack>
  );
}

export function QualityView({ glyphKey, cropCacheBust }: Props) {
  const { refreshCrop } = useAdmin();
  const t = de.admin.quality;
  const [data, setData] = useState<QualityComparison | null>(null);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [applied, setApplied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchQuality = useCallback(() => {
    setLoading(true);
    setError(null);
    getQuality(glyphKey)
      .then((d) => setData(d))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [glyphKey]);

  useEffect(() => {
    setApplied(false);
    fetchQuality();
  }, [fetchQuality, cropCacheBust]);

  const apply = useCallback(() => {
    setApplying(true);
    setError(null);
    // force: the diagnostics' re-derive is the one deliberate write that may
    // touch a locked glyph — exactly what the server-side lock flag is for.
    postResample(glyphKey, { force: true })
      .then(() => {
        setApplied(true);
        // Bumps cropCacheBust → every diagnostic-derived view (including this
        // one) refetches against the freshly stored canonical.
        refreshCrop();
      })
      .catch((e) => setError(String(e)))
      .finally(() => setApplying(false));
  }, [glyphKey, refreshCrop]);

  if (loading && !data) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 2 }}>
        <CircularProgress size={16} />
        <Typography variant="caption" color="text.secondary">
          {t.computing}
        </Typography>
      </Box>
    );
  }

  if (error && !data) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity={error.includes('404') ? 'info' : 'error'}>
          {error.includes('404') ? de.admin.diagnostics.noCanonicalShort : error}
        </Alert>
        <Button size="small" startIcon={<RefreshIcon />} onClick={fetchQuality} sx={{ mt: 1 }}>
          {de.admin.diagnostics.reload}
        </Button>
      </Box>
    );
  }

  if (!data) return null;

  const delta = data.candidate ? data.candidate.score - data.stored.score : null;

  return (
    <Stack spacing={1.5}>
      {error && <Alert severity="error">{error}</Alert>}
      {applied && <Alert severity="success">{t.applied}</Alert>}
      <Box sx={{ display: 'flex', gap: 4, flexWrap: 'wrap', alignItems: 'flex-start' }}>
        <MetricCard title={t.stored} q={data.stored} />
        {data.candidate ? (
          <>
            <MetricCard title={t.candidate} q={data.candidate} />
            <Stack spacing={1} sx={{ minWidth: 220 }}>
              {delta != null && (
                <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                  {t.delta} {delta >= 0 ? '+' : ''}
                  {delta.toFixed(1)}
                </Typography>
              )}
              <Button
                size="small"
                variant="contained"
                startIcon={applying ? <CircularProgress size={14} color="inherit" /> : <AutoFixHighIcon />}
                disabled={applying}
                onClick={apply}
              >
                {t.apply}
              </Button>
              <Typography variant="caption" color="text.disabled" sx={{ maxWidth: 260 }}>
                {t.applyHint}
              </Typography>
            </Stack>
          </>
        ) : (
          <Typography variant="caption" color="text.disabled">
            {t.noCandidate}
          </Typography>
        )}
      </Box>
    </Stack>
  );
}
