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
// Since issue #273 it also carries the per-glyph SELECTION. The aggregate gate
// dropped to `min_n = 1` — a key seen once is a statistic like any other, and
// hiding it helped nobody — which moved the whole question of "how much do I
// trust this median?" here, to the one step that renders. So the table has a
// checkbox per row, well-attested rows are proposed pre-checked, thin ones are
// marked as such, and every row stays selectable: the human decides, the
// request then says exactly what the checkboxes did (`glyph_keys`).

import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import {
  Alert,
  Box,
  Button,
  Checkbox,
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
import { useMemo, useState } from 'react';

import { applyLaufform } from '@/lib/api';
import type { AggregateApplyOut, AggregateOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import {
  LOW_N,
  defaultSelection,
  isLowN,
  minOccurrencesFor,
  previewOf,
  willChange,
} from '@/sections/admin/letters/laufformPreview';

// The preview maths live in the pure sibling `laufformPreview.ts`.

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

  // The aggregates prop is stable for the dialog's lifetime (the letter view
  // refetches only after `onApplied`), so the preview and its proposed
  // selection are computed once — recomputing would throw away the admin's
  // ticks on every render.
  const rows = useMemo(() => previewOf(aggregates), [aggregates]);
  const changing = rows.filter(willChange).length;
  const [selected, setSelected] = useState<Set<string>>(() => new Set(defaultSelection(rows)));

  const toggle = (glyphKey: string) =>
    setSelected((previous) => {
      const next = new Set(previous);
      if (!next.delete(glyphKey)) next.add(glyphKey);
      return next;
    });
  const allSelected = rows.length > 0 && selected.size === rows.length;
  const toggleAll = () => setSelected(allSelected ? new Set() : new Set(rows.map((row) => row.glyphKey)));

  const run = () => {
    setBusy(true);
    setError(false);
    // Always explicit: an empty selection never becomes "all" by omission, and
    // a deliberately ticked thin row travels as a lowered floor rather than as
    // a silent one — the endpoint refuses it otherwise.
    applyLaufform(
      handId,
      rows.filter((row) => selected.has(row.glyphKey)).map((row) => row.glyphKey),
      minOccurrencesFor(rows, selected),
    )
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
                      // The occurrence count is the whole reason for a
                      // `below_min_occurrences` skip, so it rides along; an
                      // `anchor_spike` skip carries its spike ratio against
                      // the gate (§14 LF8); the other reasons carry no number
                      // and print none.
                      label={`${skip.glyph_key} · ${
                        t.skipReason[skip.reason as keyof typeof t.skipReason] ?? skip.reason
                      }${skip.n_instances == null ? '' : ` (${skip.n_instances})`}${
                        skip.spike_ratio == null
                          ? ''
                          : ` (${skip.spike_ratio.toFixed(2)} > ${(skip.spike_max ?? 0).toFixed(2)})`
                      }`}
                    />
                  ))}
                </Box>
              </Box>
            )}
            {result.excluded.length > 0 && (
              // Not a skip — these were never asked for. Named anyway, so the
              // report says what was left alone as plainly as what was written.
              <Typography variant="caption" color="text.secondary">
                {fmt(t.doneExcluded, { count: result.excluded.length, keys: result.excluded.join(' · ') })}
              </Typography>
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
                  {`${fmt(t.previewSummary, { total: rows.length, changing })} ${fmt(t.previewSelected, {
                    selected: selected.size,
                  })}`}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {fmt(t.previewSelectionHint, { count: LOW_N })}
                </Typography>
                {/* Both axes scroll: the list is long, and at 390px the three
                    columns do not fit — clipping the distance column would
                    hide the one number the decision rests on. */}
                <Box sx={{ maxHeight: 260, overflowY: 'auto', overflowX: 'auto' }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell padding="checkbox">
                          <Checkbox
                            size="small"
                            checked={allSelected}
                            indeterminate={selected.size > 0 && !allSelected}
                            onChange={toggleAll}
                            slotProps={{ input: { 'aria-label': t.selectAll } }}
                          />
                        </TableCell>
                        <TableCell>{t.colGlyph}</TableCell>
                        <TableCell align="right">{t.colOccurrences}</TableCell>
                        <TableCell align="right">{t.colDeviation}</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {rows.map((row) => (
                        <TableRow key={row.glyphKey} hover selected={selected.has(row.glyphKey)}>
                          <TableCell padding="checkbox">
                            <Checkbox
                              size="small"
                              checked={selected.has(row.glyphKey)}
                              onChange={() => toggle(row.glyphKey)}
                              slotProps={{ input: { 'aria-label': fmt(t.selectRow, { key: row.glyphKey }) } }}
                            />
                          </TableCell>
                          <TableCell>{row.glyphKey}</TableCell>
                          <TableCell align="right">
                            {/* The trust cue at the moment of the decision: a
                                median over one or two occurrences is stated as
                                such, not left to be read off a bare number. */}
                            {isLowN(row) ? (
                              <Chip
                                size="small"
                                color="warning"
                                variant="outlined"
                                label={fmt(t.cellLowN, { count: row.nInstances })}
                              />
                            ) : (
                              row.nInstances
                            )}
                          </TableCell>
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
            // Nothing ticked is not a whole-hand apply — it is nothing to do.
            disabled={busy || selected.size === 0}
            startIcon={busy ? <CircularProgress size={14} /> : undefined}
          >
            {selected.size === 1 ? t.confirmOne : fmt(t.confirm, { count: selected.size })}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
