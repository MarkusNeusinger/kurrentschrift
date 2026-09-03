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
import { Alert, Box, Button, CircularProgress, Stack, Typography } from '@mui/material';
import { useCallback, useEffect, useState } from 'react';

import { useAdmin } from '@/context/adminState';
import { getQuality, postResample } from '@/lib/api';
import type { QualityComparison, QualityData } from '@/lib/api';
import { apiErrorText } from '@/sections/admin/shell/apiErrorText';
import type { ApiErrorText } from '@/sections/admin/shell/apiErrorText';
import { de } from '@/locales/admin';
import { ScoreBreakdown, ScoreChip } from '@/sections/admin/quality/scoreParts';
import { ErrorText } from '@/sections/admin/shell/ErrorText';

interface Props {
  glyphKey: string;
  // Bumped by the admin context on every trace/resample — refetches the scores.
  cropCacheBust?: number;
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
      {label} {value}
    </Typography>
  );
}

function MetricCard({ title, q }: { title: string; q: QualityData }) {
  const t = de.admin.quality;
  // The naturalness metric (Sütterlin/Gleichzug) and the Kurrent pixel metric
  // return different fields under the same shape — `naturalness` discriminates.
  const isNaturalness = q.naturalness != null;
  return (
    <Stack spacing={0.5} sx={{ minWidth: 200 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="caption" color="text.secondary">
          {title}
        </Typography>
        <ScoreChip score={q.score} />
      </Box>
      <MetricRow label={t.iou} value={q.iou.toFixed(3)} />
      <MetricRow label={t.chamfer} value={`${q.chamfer_mean_px.toFixed(2)} px`} />
      {isNaturalness ? (
        <>
          <MetricRow label={t.naturalness} value={(q.naturalness ?? 0).toFixed(2)} />
          <MetricRow label={t.gate} value={(q.gate ?? 0).toFixed(2)} />
        </>
      ) : (
        <>
          <MetricRow label={t.geoRmse} value={`${(q.geo_rmse_px ?? 0).toFixed(2)} px`} />
          <MetricRow label={t.waviness} value={(q.waviness_ratio ?? 0).toFixed(2)} />
        </>
      )}
      {/* The same payload carries the per-category breakdown the wizard shows;
          leaving it out here made the Diagnose modal the one place that has the
          numbers and does not say where the points went. */}
      <Box sx={{ mt: 0.5 }}>
        <ScoreBreakdown quality={q} heading={t.breakdownHeading} hint={t.breakdownHint} />
      </Box>
    </Stack>
  );
}

export function QualityView({ glyphKey, cropCacheBust }: Props) {
  const { sourceId, refreshCrop } = useAdmin();
  const t = de.admin.quality;
  const [data, setData] = useState<QualityComparison | null>(null);
  // Starts true: the first render already waits for the scores the effect below
  // requests, so the spinner is the honest first frame.
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [applied, setApplied] = useState(false);
  const [error, setError] = useState<ApiErrorText | null>(null);

  // The request only; the flags it used to raise belong to whoever triggers it —
  // the render guard below on a key change, the retry button in its handler. A
  // setState in an effect body is the violation (set-state-in-effect); in the
  // promise continuation it is not.
  const fetchQuality = useCallback(() => {
    getQuality(sourceId, glyphKey)
      .then((d) => setData(d))
      .catch((e: unknown) => setError(apiErrorText(e)))
      .finally(() => setLoading(false));
  }, [sourceId, glyphKey]);

  // React's "adjusting state when a prop changes" — the key carries exactly the
  // effect's inputs (`fetchQuality` is itself derived from source + glyph), so a
  // refetch and the flags it resets happen in one render.
  const loadKey = `${sourceId} ${glyphKey} ${cropCacheBust ?? ''}`;
  const [shownFor, setShownFor] = useState(loadKey);
  if (shownFor !== loadKey) {
    setShownFor(loadKey);
    setApplied(false);
    setLoading(true);
    setError(null);
  }

  useEffect(() => {
    fetchQuality();
  }, [fetchQuality, cropCacheBust]);

  // The retry path sets its own flags: an event handler may, an effect may not.
  const retry = () => {
    setLoading(true);
    setError(null);
    fetchQuality();
  };

  const apply = useCallback(() => {
    setApplying(true);
    setError(null);
    // force: the diagnostics' re-derive is the one deliberate write that may
    // touch a locked glyph — exactly what the server-side lock flag is for.
    postResample(sourceId, glyphKey, { force: true })
      .then(() => {
        setApplied(true);
        // Bumps cropCacheBust → every diagnostic-derived view (including this
        // one) refetches against the freshly stored canonical.
        refreshCrop();
      })
      .catch((e: unknown) => setError(apiErrorText(e)))
      .finally(() => setApplying(false));
  }, [sourceId, glyphKey, refreshCrop]);

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
        {/* No canonical yet is a state, not a failure — the typed status says
            so without sniffing the message. */}
        <Alert severity={error.status === 404 ? 'info' : 'error'}>
          {error.status === 404 ? de.admin.diagnostics.noCanonicalShort : <ErrorText error={error} />}
        </Alert>
        <Button size="small" startIcon={<RefreshIcon />} onClick={retry} sx={{ mt: 1 }}>
          {de.admin.diagnostics.reload}
        </Button>
      </Box>
    );
  }

  if (!data) return null;

  const delta = data.candidate ? data.candidate.score - data.stored.score : null;

  return (
    <Stack spacing={1.5}>
      {error && (
        <Alert severity="error">
          <ErrorText error={error} />
        </Alert>
      )}
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
