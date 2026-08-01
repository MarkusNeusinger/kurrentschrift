// Word editor (Werkbank W3) — the manual re-tracing surface over one stored
// word occurrence. The specimen crop is the underlay, the stored trace the
// starting point; the admin re-draws the ductus with the S-Pen (every pen lift
// starts a new stroke, exactly like the wizard's Weg step) and saves it as an
// `authored` word_instance. Authored rows are ground truth for statistics and
// training — never a rendering patch (optimierungs-werkbank.md §3/§6), and the
// server's overwrite protection keeps them safe from every re-harvest.
//
// The save reuses the batch endpoint with a SINGLE item and without `replace`,
// so exactly this occurrence is written and no other row is touched. Only rows
// that already exist can be edited: the Belege list is built from stored rows,
// and an occurrence without one has no slot labels to preserve.

import {
  Alert,
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useRef, useState } from 'react';

import { getHand, putWordInstances, wordSampleCropUrl } from '@/lib/api';
import type { HandOut, WordInstanceOut, WordSampleOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { overlay } from '@/sections/admin/overlayColors';
import {
  cropToTrace,
  registrationMatrix,
  sanitizeStrokes,
  strokePathD,
  traceRegistration,
  type TracePoint,
} from '@/sections/admin/belege/registration';
import { holdsGrip, releaseGrip, takeGrip, type Grip } from '@/sections/admin/setup-wizard/gestureUtils';
import { garamond } from '@/styles/paper';

// Minimum pointer travel between two stored samples (x-height units) — dense
// enough for a faithful ductus, sparse enough to stay far below the schema's
// per-stroke point cap on a slow, deliberate trace.
const MIN_STEP_XH = 0.015;

interface Props {
  open: boolean;
  onClose: () => void;
  row: WordInstanceOut;
  sample: WordSampleOut;
  sourceId: string;
  // The source's writer — used when the row itself carries no hand (the batch
  // needs one; it get-or-creates the row).
  fallbackHandId: string | null;
  // Called after a successful save so the list re-reads the stored rows.
  onSaved: () => void;
}

const copyStrokes = (strokes: WordInstanceOut['strokes']): TracePoint[][] =>
  strokes.map((s) => s.map(([x, y]) => [x, y] as TracePoint));

export function WordTraceEditorDialog({ open, onClose, row, sample, sourceId, fallbackHandId, onSaved }: Props) {
  const t = de.admin.belege;
  const [strokes, setStrokes] = useState<TracePoint[][]>(() => copyStrokes(row.strokes));
  const [dirty, setDirty] = useState(false);
  const [showStored, setShowStored] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hand, setHand] = useState<HandOut | null>(null);

  const svgRef = useRef<SVGSVGElement | null>(null);
  const gripRef = useRef<Grip>({ current: null });

  const reg = useMemo(() => traceRegistration(row.measurements, sample), [row.measurements, sample]);
  const matrix = useMemo(() => registrationMatrix(reg), [reg]);
  const handId = row.hand_id ?? fallbackHandId;

  // No reset effect: the caller mounts the dialog per occurrence (keyed by the
  // row identity), so the state initialisers above already are the fresh start.

  // The hand is echoed back as read: the batch upserts the writer row whole, so
  // sending id + label only would wipe its era/note as a side effect.
  useEffect(() => {
    if (!open || !handId) return;
    let cancelled = false;
    getHand(handId, { retries: 1 })
      .then((h) => {
        if (!cancelled) setHand(h);
      })
      .catch(() => {
        if (!cancelled) setHand(null);
      });
    return () => {
      cancelled = true;
    };
  }, [open, handId]);

  const toTrace = (clientX: number, clientY: number): TracePoint | null => {
    const svg = svgRef.current;
    if (!svg) return null;
    const box = svg.getBoundingClientRect();
    if (box.width === 0 || box.height === 0) return null;
    const px = ((clientX - box.left) / box.width) * sample.width;
    const py = ((clientY - box.top) / box.height) * sample.height;
    return cropToTrace(reg, [px, py]);
  };

  const onPointerDown = (e: React.PointerEvent<SVGSVGElement>) => {
    const p = toTrace(e.clientX, e.clientY);
    if (!p) return;
    // One pointer at a time: a palm resting beside the S-Pen must not hijack
    // the stroke the pen is drawing (same rule as the wizard canvas).
    if (!takeGrip(gripRef.current, e.pointerId)) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    setStrokes((prev) => [...prev, [p]]);
    setDirty(true);
  };

  const onPointerMove = (e: React.PointerEvent<SVGSVGElement>) => {
    if (!holdsGrip(gripRef.current, e.pointerId)) return;
    const p = toTrace(e.clientX, e.clientY);
    if (!p) return;
    setStrokes((prev) => {
      if (prev.length === 0) return prev;
      const current = prev[prev.length - 1];
      const last = current[current.length - 1];
      if (last && Math.hypot(p[0] - last[0], p[1] - last[1]) < MIN_STEP_XH) return prev;
      return [...prev.slice(0, -1), [...current, p]];
    });
  };

  // Pen up = Absetzen: the stroke ends here and the next pen-down starts a new
  // one. A pen-down that never moved is a stray tap, not a stroke — drop it so
  // undo and the save gate count real strokes only.
  const onPointerUp = (e: React.PointerEvent<SVGSVGElement>) => {
    if (!releaseGrip(gripRef.current, e.pointerId)) return;
    setStrokes((prev) => (prev.length && prev[prev.length - 1].length < 2 ? prev.slice(0, -1) : prev));
  };

  const savable = useMemo(() => sanitizeStrokes(strokes), [strokes]);
  const canSave = open && dirty && savable.length > 0 && !saving && Boolean(handId);

  const save = async () => {
    if (!handId) return;
    setSaving(true);
    setError(null);
    try {
      const res = await putWordInstances(sourceId, {
        hand: hand
          ? { id: hand.id, label: hand.label, era: hand.era, note: hand.note }
          : { id: handId, label: handId },
        items: [
          {
            kind: row.kind,
            specimen_id: row.specimen_id,
            word: row.word,
            // The slot labels stay as harvested — the editor re-traces the
            // ductus, it does not re-shape the word.
            slots: row.slots,
            strokes: savable,
            provenance: 'authored',
            measurements: {
              ...row.measurements,
              // Keep the row displayable in exactly the frame it was drawn in
              // (the row shift is already folded into baselineRow).
              registration_px: { tx: reg.tx, ty: 0, baseline_row: reg.baselineRow },
              xh_px: reg.xh,
              // The auto-fit QC describes the REPLACED path; carrying it over
              // would keep a hand-fixed word ranked by dead numbers.
              fitted_slots: undefined,
              unfitted_slots: undefined,
              geo_rmse_px_by_slot: undefined,
            },
          },
        ],
      });
      if (res.stored < 1) throw new Error('nothing stored');
      onSaved();
      onClose();
    } catch {
      setError(t.editorSaveFailed);
    } finally {
      setSaving(false);
    }
  };

  const midbandRow = reg.baselineRow - reg.xh;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'baseline', gap: 1, flexWrap: 'wrap' }}>
        <Typography component="span" sx={{ fontFamily: garamond, fontSize: 26, lineHeight: 1 }}>
          {row.word}
        </Typography>
        <Typography component="span" variant="body2" color="text.secondary">
          {fmt(t.editorTitle, { specimen: row.specimen_id })}
        </Typography>
      </DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
          {t.editorIntro}
        </Typography>
        {error && (
          <Alert severity="error" sx={{ mb: 1 }}>
            {error}
          </Alert>
        )}
        {!handId && (
          <Alert severity="warning" sx={{ mb: 1 }}>
            {t.editorNoHand}
          </Alert>
        )}
        <svg
          ref={svgRef}
          viewBox={`0 0 ${sample.width} ${sample.height}`}
          style={{
            display: 'block',
            width: '100%',
            background: '#fff',
            borderRadius: 6,
            touchAction: 'none',
            cursor: 'crosshair',
          }}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
        >
          <image
            href={wordSampleCropUrl(sourceId, sample.id)}
            x={0}
            y={0}
            width={sample.width}
            height={sample.height}
            preserveAspectRatio="none"
          />
          {/* Grundlinie + Mittellinie of the registration frame the trace is
              stored in — the writer sees which line their v = 0/1 sits on. */}
          <line
            x1={0}
            x2={sample.width}
            y1={reg.baselineRow}
            y2={reg.baselineRow}
            stroke={overlay.idle}
            strokeWidth={0.6}
            strokeOpacity={0.7}
          />
          <line
            x1={0}
            x2={sample.width}
            y1={midbandRow}
            y2={midbandRow}
            stroke={overlay.idle}
            strokeWidth={0.6}
            strokeOpacity={0.5}
            strokeDasharray="3 3"
          />
          <g transform={matrix}>
            {showStored &&
              dirty &&
              row.strokes.map((stroke, i) => (
                <path
                  key={`stored-${i}`}
                  d={strokePathD(stroke.map(([x, y]) => [x, y] as TracePoint))}
                  fill="none"
                  stroke="#8b9a95"
                  strokeOpacity={0.6}
                  strokeWidth={0.05}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              ))}
            {strokes.map((stroke, i) => (
              <path
                key={i}
                d={strokePathD(stroke)}
                fill="none"
                stroke={overlay.draft}
                strokeOpacity={0.9}
                strokeWidth={0.07}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            ))}
          </g>
        </svg>
        <Box sx={{ display: 'flex', gap: 1, mt: 1, alignItems: 'center', flexWrap: 'wrap' }}>
          <Button
            size="small"
            onClick={() => {
              setStrokes((prev) => prev.slice(0, -1));
              setDirty(true);
            }}
            disabled={strokes.length === 0}
          >
            {t.editorUndo}
          </Button>
          <Button
            size="small"
            onClick={() => {
              setStrokes([]);
              setDirty(true);
            }}
            disabled={strokes.length === 0}
          >
            {t.editorClear}
          </Button>
          <Button
            size="small"
            onClick={() => {
              setStrokes(copyStrokes(row.strokes));
              setDirty(false);
            }}
            disabled={!dirty}
          >
            {t.editorReset}
          </Button>
          <FormControlLabel
            sx={{ mr: 0 }}
            control={<Checkbox size="small" checked={showStored} onChange={(e) => setShowStored(e.target.checked)} />}
            label={<Typography variant="caption">{t.editorShowStored}</Typography>}
          />
          <Typography variant="caption" color="text.secondary">
            {fmt(t.editorStrokeCount, { strokes: savable.length })} · {fmt(t.editorSlots, { slots: row.slots.join(' ') })}
          </Typography>
        </Box>
      </DialogContent>
      <DialogActions>
        <Typography variant="caption" color="text.secondary" sx={{ mr: 'auto', ml: 2 }}>
          {t.editorAuthoredHint}
        </Typography>
        <Button onClick={onClose} disabled={saving}>
          {t.editorClose}
        </Button>
        <Button variant="contained" onClick={save} disabled={!canSave}>
          {t.editorSave}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
