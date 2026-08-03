// The one handle in the whole admin that changes what the engine WRITES.
//
// `apply-laufform` promotes a hand's stored aggregates into template variant
// 100 — the running forms `/write/word` renders in flowing runs. Everything
// else in the hand model measures; this one step renders (issue #270,
// optimierungs-werkbank.md §3), and that asymmetry is the entire reason it
// gets its own dialog instead of a button among the inspection controls:
//
//   1. It says plainly what will change, for the WHOLE hand, before anything
//      happens — which glyphs get a new running form, which already agree with
//      their median (distance 0, nothing to gain), which are written for the
//      first time, and which the step will skip and why.
//   2. It requires an explicit confirmation. The endpoint is idempotent and a
//      re-run is harmless, but overwriting authored-looking geometry on a
//      misclick is not the kind of surprise this project wants.
//   3. Afterwards it reports what actually happened, so the run leaves a
//      readable trace rather than a silent success.
//
// It deliberately offers no per-glyph selection: the endpoint applies a hand's
// aggregates wholesale, and a UI that implied otherwise would be lying about
// what the button does.

import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useState } from 'react';

import { applyLaufform } from '@/lib/api';
import type { AggregateApplyOut, AggregateOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';

// What the apply WOULD do to one glyph, derived from the same row the letter
// view already holds — so the preview costs no extra request and cannot
// disagree with the freshness chips shown beside it.
interface Preview {
  glyphKey: string;
  nInstances: number;
  dev: number | null;
  // No stored running form yet: this glyph gains one.
  creates: boolean;
}

function previewOf(aggregates: AggregateOut[]): Preview[] {
  return aggregates
    // Only base-variant aggregates feed the derived row (a variant-100
    // aggregate would let the Laufform derive from itself) — the endpoint
    // skips the rest, so the preview must not promise them either.
    .filter((agg) => agg.variant === 0)
    .map((agg) => ({
      glyphKey: agg.glyph_key,
      nInstances: agg.n_instances,
      dev: agg.laufform_dev_xh,
      creates: agg.laufform_anchors === null,
    }))
    .sort((a, b) => (b.dev ?? Infinity) - (a.dev ?? Infinity) || a.glyphKey.localeCompare(b.glyphKey));
}

export function LaufformApplyDialog({
  handId,
  aggregates,
  onClose,
  onApplied,
}: {
  handId: string;
  aggregates: AggregateOut[];
  onClose: () => void;
  // The write landed — the caller refetches the statistics layer and the
  // rendered forms, both of which just changed.
  onApplied: () => void;
}) {
  const t = de.admin.laufform;
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<AggregateApplyOut | null>(null);
  const [error, setError] = useState(false);

  const rows = previewOf(aggregates);
  const changing = rows.filter((r) => r.dev === null || r.dev > 0).length;

  const run = () => {
    setBusy(true);
    setError(false);
    applyLaufform(handId)
      .then((out) => {
        setResult(out);
        onApplied();
      })
      .catch(() => setError(true))
      .finally(() => setBusy(false));
  };

  return (
    <Dialog open onClose={busy ? undefined : onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <WarningAmberIcon color="warning" />
        {t.title}
      </DialogTitle>
      <DialogContent>
        {result ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            <Alert severity="success">
              {fmt(t.doneSummary, { applied: result.applied.length, skipped: result.skipped.length })}
            </Alert>
            {result.applied.length > 0 && (
              <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                {result.applied.map((key) => (
                  <Chip
                    key={key.glyph_key}
                    size="small"
                    variant="outlined"
                    color={key.created ? 'success' : 'default'}
                    label={
                      key.created
                        ? fmt(t.doneCreated, { key: key.glyph_key })
                        : fmt(t.doneUpdated, {
                            key: key.glyph_key,
                            value: key.laufform_dev_xh === null ? '—' : key.laufform_dev_xh.toFixed(3),
                          })
                    }
                  />
                ))}
              </Box>
            )}
            {result.skipped.length > 0 && (
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  {t.doneSkippedLabel}
                </Typography>
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                  {result.skipped.map((skip) => (
                    <Chip
                      key={`${skip.glyph_key}:${skip.variant}`}
                      size="small"
                      variant="outlined"
                      label={`${skip.glyph_key} · ${t.skipReason[skip.reason as keyof typeof t.skipReason] ?? skip.reason}`}
                    />
                  ))}
                </Box>
              </Box>
            )}
            <Typography variant="caption" color="text.secondary">
              {t.doneHint}
            </Typography>
          </Box>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            {/* The warning first, in the words that matter: this is the step
                that leaves the measuring half of the system. */}
            <Alert severity="warning">{t.warning}</Alert>
            <Typography variant="body2" color="text.secondary">
              {fmt(t.intro, { hand: handId })}
            </Typography>

            {rows.length === 0 ? (
              <Alert severity="info">{t.nothingToApply}</Alert>
            ) : (
              <>
                <Typography variant="body2">
                  {fmt(t.previewSummary, { total: rows.length, changing })}
                </Typography>
                {/* Both axes scroll: the list is long, and at 390px the three
                    columns do not fit — clipping the distance column would
                    hide the one number the decision rests on. */}
                <Box sx={{ maxHeight: 260, overflowY: 'auto', overflowX: 'auto' }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>{t.colGlyph}</TableCell>
                        <TableCell align="right">{t.colOccurrences}</TableCell>
                        <TableCell align="right">{t.colDeviation}</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {rows.map((row) => (
                        <TableRow key={row.glyphKey}>
                          <TableCell>{row.glyphKey}</TableCell>
                          <TableCell align="right">{row.nInstances}</TableCell>
                          <TableCell align="right">
                            {row.creates ? (
                              <Chip size="small" color="success" variant="outlined" label={t.cellNew} />
                            ) : row.dev === null ? (
                              <Typography variant="caption" color="text.disabled">
                                {t.cellIncomparable}
                              </Typography>
                            ) : row.dev === 0 ? (
                              <Typography variant="caption" color="text.disabled">
                                {t.cellUnchanged}
                              </Typography>
                            ) : (
                              <Typography variant="caption" color="warning.main">
                                {row.dev.toFixed(3)}
                              </Typography>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Box>
              </>
            )}
            {error && <Alert severity="error">{t.failed}</Alert>}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={busy}>
          {result ? de.admin.pairs.close : de.admin.werkbank.cancel}
        </Button>
        {!result && rows.length > 0 && (
          <Button
            variant="contained"
            color="warning"
            onClick={run}
            disabled={busy}
            startIcon={busy ? <CircularProgress size={14} /> : undefined}
          >
            {t.confirm}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
