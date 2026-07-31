// Belege (/admin/belege): every stored word-occurrence trace over its specimen
// crop, worst first — the error-finding surface over the occurrence layer
// (handmodell H1/H2). Read-only for now; the coming word editor (manual
// re-tracing → authored rows) will open from these cards.

import { Alert, Box, Chip, CircularProgress, TextField, Tooltip, Typography } from '@mui/material';
import { useEffect, useMemo, useState } from 'react';

import { useAdmin } from '@/context/AdminContext';
import { useInView } from '@/hooks/useInView';
import { getWordSamples, listWordInstances, wordSampleCropUrl } from '@/lib/api';
import type { WordInstanceOut, WordSampleOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { garamond } from '@/styles/paper';

const FACE_H = 220; // px per card face — matches the compare cards' scale

// Mean of the per-slot fit RMSEs; null when the row carries none (authored).
function rmseMean(row: WordInstanceOut): number | null {
  const values = Object.values(row.measurements.geo_rmse_px_by_slot ?? {});
  if (values.length === 0) return null;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

// Worst first: unfitted letters dominate, mean RMSE breaks ties.
function badness(row: WordInstanceOut): number {
  return (row.measurements.unfitted_slots?.length ?? 0) * 10 + (rmseMean(row) ?? 0);
}

function TraceCard({ row, sample, sourceId }: { row: WordInstanceOut; sample: WordSampleOut; sourceId: string }) {
  const [ref, inView] = useInView<HTMLDivElement>();
  const t = de.admin.belege;

  const m = row.measurements;
  const reg = m.registration_px;
  const xh = m.xh_px ?? sample.baseline_y - sample.midband_y;
  const tx = reg?.tx ?? 0;
  const baselineRow = (reg?.baseline_row ?? sample.baseline_y) + (reg?.ty ?? 0);
  // Trace units → crop px: px = (u·xh + tx, baseline_row + ty − v·xh); the
  // matrix does it in one place, so the path d stays in raw trace coordinates.
  const matrix = `matrix(${xh} 0 0 ${-xh} ${tx} ${baselineRow})`;

  const fitted = m.fitted_slots?.length ?? null;
  // Slot indices index into `slots` (the harvest emits them in that space);
  // the fallback keeps older rows from crashing the card.
  const unfitted = (m.unfitted_slots ?? []).map((i) => row.slots[i] ?? String(i));
  const meanRmse = rmseMean(row);
  const cropW = (FACE_H / sample.height) * sample.width;

  return (
    <Box
      ref={ref}
      sx={{ border: 1, borderColor: 'divider', borderRadius: 2, p: 2, bgcolor: 'background.paper' }}
    >
      <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, flexWrap: 'wrap', mb: 1 }}>
        <Typography sx={{ fontFamily: garamond, fontSize: 24, lineHeight: 1 }}>{row.word}</Typography>
        <Typography variant="caption" color="text.secondary">
          {row.specimen_id}
        </Typography>
        <Chip
          size="small"
          variant="outlined"
          color={row.provenance === 'authored' ? 'success' : 'default'}
          label={row.provenance === 'authored' ? t.provenanceAuthored : t.provenanceTraced}
        />
        {fitted !== null && (
          <Chip
            size="small"
            variant="outlined"
            label={fmt(t.fittedChip, { fitted, total: fitted + unfitted.length })}
          />
        )}
        {unfitted.length > 0 && (
          <Chip size="small" color="warning" label={`${t.unfittedPrefix}${unfitted.join(' ')}`} />
        )}
        {meanRmse !== null && (
          <Tooltip title={Object.entries(m.geo_rmse_px_by_slot ?? {})
            .map(([i, v]) => `${row.slots[Number(i)] ?? i}: ${v}`)
            .join(' · ')}
          >
            <Chip size="small" variant="outlined" label={fmt(t.rmseChip, { value: meanRmse.toFixed(2) })} />
          </Tooltip>
        )}
      </Box>
      {inView ? (
        <svg
          width={cropW}
          height={FACE_H}
          viewBox={`0 0 ${sample.width} ${sample.height}`}
          style={{ display: 'block', background: '#fff', maxWidth: '100%', height: 'auto' }}
          role="img"
          aria-label={`${t.cropAlt} ${row.word}`}
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
            {row.strokes.map((stroke, i) => (
              <path
                key={i}
                d={stroke.map(([x, y], j) => `${j === 0 ? 'M' : 'L'}${x},${y}`).join(' ')}
                fill="none"
                stroke="#1c6b57"
                strokeOpacity={0.8}
                strokeWidth={0.07}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            ))}
          </g>
        </svg>
      ) : (
        <Box sx={{ height: FACE_H }} />
      )}
    </Box>
  );
}

export function BelegeView() {
  const { source, sourceId } = useAdmin();
  const [rows, setRows] = useState<WordInstanceOut[] | null>(null);
  const [samples, setSamples] = useState<WordSampleOut[] | null>(null);
  const [error, setError] = useState(false);
  const [filter, setFilter] = useState('');
  const t = de.admin.belege;

  useEffect(() => {
    let cancelled = false;
    setRows(null);
    setSamples(null);
    setError(false);
    Promise.all([listWordInstances(sourceId, undefined, { retries: 2 }), getWordSamples(sourceId, { retries: 2 })])
      .then(([instances, wordSamples]) => {
        if (cancelled) return;
        setRows(instances);
        setSamples(wordSamples);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [sourceId]);

  const sampleById = useMemo(() => new Map((samples ?? []).map((s) => [s.id, s])), [samples]);
  const visible = useMemo(() => {
    const needle = filter.trim().toLowerCase();
    return (rows ?? [])
      .filter((r) => !needle || r.word.toLowerCase().includes(needle))
      .sort((a, b) => badness(b) - badness(a));
  }, [rows, filter]);
  const orphans = useMemo(() => visible.filter((r) => !sampleById.has(r.specimen_id)), [visible, sampleById]);

  if (!source) return null;
  if (error) return <Alert severity="error">{t.loadError}</Alert>;
  if (rows === null || samples === null) {
    return (
      <Box sx={{ p: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress size={28} />
      </Box>
    );
  }

  return (
    <Box sx={{ overflowY: 'auto', height: '100%', p: { xs: 2, md: 3 } }}>
      <Typography variant="h6">{t.title}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 720, mb: 2 }}>
        {t.intro}
      </Typography>
      {rows.length === 0 ? (
        <Alert severity="info">{t.empty}</Alert>
      ) : (
        <>
          <TextField
            size="small"
            label={t.filterLabel}
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            sx={{ mb: 2, maxWidth: 280 }}
          />
          {orphans.map((r) => (
            <Alert key={`${r.kind}:${r.specimen_id}`} severity="warning" sx={{ mb: 1, maxWidth: 720 }}>
              {fmt(t.noSample, { id: r.specimen_id })}
            </Alert>
          ))}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, maxWidth: 1100 }}>
            {visible
              .filter((r) => sampleById.has(r.specimen_id))
              .map((r) => (
                <TraceCard
                  key={`${r.kind}:${r.specimen_id}`}
                  row={r}
                  sample={sampleById.get(r.specimen_id) as WordSampleOut}
                  sourceId={sourceId}
                />
              ))}
          </Box>
        </>
      )}
    </Box>
  );
}
