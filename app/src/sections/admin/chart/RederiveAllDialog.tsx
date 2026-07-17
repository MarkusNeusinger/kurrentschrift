// RederiveAllDialog — bulk re-derive of every authored glyph, with a report.
//
// After pipeline/anchor-density improvements land, every stored template can
// be recomputed from its raw stylus path. This dialog runs that over ALL
// authored glyphs: per glyph it first fetches the stored-vs-candidate score
// (`GET .../quality`, a dry run), then applies via `/resample` (force), and
// reports the per-glyph delta — regressions show red so a worsened letter is
// caught immediately instead of discovered later in the quiz.

import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useCallback, useMemo, useRef, useState } from 'react';

import { useAdmin } from '@/context/AdminContext';
import { knownGlyph } from '@/domain/glyphs';
import { getQuality, postResample } from '@/lib/api';
import { de, fmt } from '@/locales/admin';

interface Props {
  open: boolean;
  onClose: () => void;
}

type RowStatus = 'pending' | 'scoring' | 'applying' | 'done' | 'failed';

interface RederiveRow {
  label: string; // letter char
  key: string; // the glyph_key scored and re-derived
  status: RowStatus;
  before?: number;
  after?: number;
  error?: string;
}

// Scores are 0–100 and the table rounds to 0.1 — below half a point is noise,
// not a meaningful improvement/regression.
const DELTA_EPSILON = 0.5;

function deltaColor(delta: number): string {
  if (delta > DELTA_EPSILON) return 'success.main';
  if (delta < -DELTA_EPSILON) return 'error.main';
  return 'text.secondary';
}

export function RederiveAllDialog({ open, onClose }: Props) {
  const { sourceId, bboxesByKey, glyphsByKey, refreshCrop } = useAdmin();
  const t = de.admin.rederive;
  const [rows, setRows] = useState<RederiveRow[] | null>(null);
  const [running, setRunning] = useState(false);
  const cancelRef = useRef(false);

  // One row per authored glyph_key.
  const groups = useMemo<RederiveRow[]>(() => {
    const out: RederiveRow[] = [];
    for (const key of Object.keys(glyphsByKey).sort()) {
      if (!glyphsByKey[key]?.has_data || !bboxesByKey[key]) continue;
      const known = knownGlyph(key);
      if (!known) continue;
      out.push({ label: known.glyph, key, status: 'pending' });
    }
    return out;
  }, [glyphsByKey, bboxesByKey]);

  const effectiveRows = rows ?? groups;
  const doneCount = effectiveRows.filter((r) => r.status === 'done' || r.status === 'failed').length;
  const finished = !running && rows != null && doneCount === rows.length;

  const updateRow = (index: number, patch: Partial<RederiveRow>) =>
    setRows((prev) => (prev ? prev.map((r, i) => (i === index ? { ...r, ...patch } : r)) : prev));

  const run = useCallback(async () => {
    cancelRef.current = false;
    setRunning(true);
    const work = groups.map((g) => ({ ...g, status: 'pending' as RowStatus }));
    setRows(work);
    let applied = 0;
    for (let i = 0; i < work.length; i++) {
      if (cancelRef.current) break;
      // Scoring and applying are decoupled: older templates without pixel-space
      // trace meta 409 on /quality, and the re-derive below is exactly what
      // repairs them — a failed score must not block the apply.
      let before: number | undefined;
      let after: number | undefined;
      let rawPathMissing = false;
      updateRow(i, { status: 'scoring' });
      try {
        const q = await getQuality(sourceId, work[i].key);
        before = q.stored.score;
        after = q.candidate?.score;
        rawPathMissing = q.candidate == null;
      } catch {
        // No before/after columns for this row; still re-derive.
      }
      if (rawPathMissing) {
        // /resample would deterministically 409 without a stored raw_path.
        updateRow(i, { status: 'failed', before, error: t.noRawPath });
        continue;
      }
      try {
        updateRow(i, { status: 'applying', before, after });
        // force: bulk refresh is the deliberate write the lock guard expects.
        await postResample(sourceId, work[i].key, { force: true });
        applied += 1;
        updateRow(i, { status: 'done' });
      } catch (err) {
        updateRow(i, { status: 'failed', error: String(err) });
      }
    }
    if (applied > 0) refreshCrop();
    setRunning(false);
  }, [sourceId, groups, refreshCrop, t.noRawPath]);

  const handleClose = () => {
    if (running) return; // cancel first — closing mid-run would hide the report
    setRows(null);
    onClose();
  };

  const doneRows = (rows ?? []).filter((r) => r.status === 'done' && r.before != null && r.after != null);
  const improved = doneRows.filter((r) => (r.after ?? 0) - (r.before ?? 0) > DELTA_EPSILON).length;
  const worse = doneRows.filter((r) => (r.after ?? 0) - (r.before ?? 0) < -DELTA_EPSILON).length;
  const meanDelta = doneRows.length
    ? doneRows.reduce((s, r) => s + ((r.after ?? 0) - (r.before ?? 0)), 0) / doneRows.length
    : 0;

  return (
    <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
      <DialogTitle>{t.title}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
          {t.intro}
        </Typography>
        {running && <LinearProgress variant="determinate" value={(doneCount / Math.max(1, effectiveRows.length)) * 100} sx={{ mb: 1 }} />}
        {effectiveRows.length === 0 ? (
          <Alert severity="info">{t.empty}</Alert>
        ) : (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>{t.colLetter}</TableCell>
                <TableCell align="right">{t.colBefore}</TableCell>
                <TableCell align="right">{t.colAfter}</TableCell>
                <TableCell align="right">{t.colDelta}</TableCell>
                <TableCell>{t.colStatus}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {effectiveRows.map((r) => {
                const delta = r.before != null && r.after != null ? r.after - r.before : null;
                return (
                  <TableRow key={r.key}>
                    <TableCell sx={{ fontFamily: 'monospace' }}>{r.label}</TableCell>
                    <TableCell align="right">{r.before?.toFixed(1) ?? '–'}</TableCell>
                    <TableCell align="right">{r.after?.toFixed(1) ?? '–'}</TableCell>
                    <TableCell align="right" sx={{ color: delta != null ? deltaColor(delta) : 'text.disabled', fontWeight: 600 }}>
                      {delta != null ? `${delta >= 0 ? '+' : ''}${delta.toFixed(1)}` : '–'}
                    </TableCell>
                    <TableCell>
                      {r.status === 'scoring' || r.status === 'applying' ? (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <CircularProgress size={12} />
                          <Typography variant="caption">{r.status === 'scoring' ? t.statusScoring : t.statusApplying}</Typography>
                        </Box>
                      ) : (
                        <Typography variant="caption" color={r.status === 'failed' ? 'error' : 'text.secondary'} title={r.error}>
                          {r.status === 'pending' ? t.statusPending : r.status === 'done' ? t.statusDone : t.statusFailed}
                        </Typography>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
        {finished && doneRows.length > 0 && (
          <Alert severity={worse > 0 ? 'warning' : 'success'} sx={{ mt: 1.5 }}>
            {fmt(t.summary, {
              improved: String(improved),
              worse: String(worse),
              mean: `${meanDelta >= 0 ? '+' : ''}${meanDelta.toFixed(1)}`,
            })}
            {worse > 0 ? ` ${t.worseHint}` : ''}
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        {running ? (
          <Button onClick={() => (cancelRef.current = true)}>{t.cancel}</Button>
        ) : (
          <Button onClick={handleClose}>{t.close}</Button>
        )}
        <Button
          variant="contained"
          startIcon={running ? <CircularProgress size={14} color="inherit" /> : <PlayArrowIcon />}
          disabled={running || effectiveRows.length === 0}
          onClick={run}
        >
          {t.start}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
