// Word editor (Werkbank W3) — the manual re-tracing surface over one stored
// word occurrence. The specimen crop is the underlay, the stored trace the
// starting point; the admin re-draws the ductus with the S-Pen (every pen lift
// starts a new stroke, exactly like the wizard's Weg step) and saves it as an
// `authored` word_instance. Authored rows are ground truth for statistics and
// training — never a rendering patch (optimierungs-werkbank.md §3/§6), and the
// server's overwrite protection keeps them safe from every re-harvest.
//
// The save reuses the batch endpoint with a SINGLE item and without `replace`,
// so exactly this occurrence is written and no other row is touched. `row` may
// be a STORED row or a seeded starting point for a Wortprobe nobody has traced
// yet (`seedWordInstance`, shell/model.ts — identity and registration frame off
// the sidecar, slot labels from the shaper, no strokes). The dialog does not
// care which: the upsert creates the row either way, so a caller never has to
// rebuild this write flow to reach an untraced occurrence.

import {
  Alert,
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Slider,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';

import { InfoHint } from '@/components/InfoHint';
import { getHand, putWordInstances, wordSampleCropUrl } from '@/lib/api';
import type { HandOut, WordInstanceOut, WordSampleOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import {
  frameStale,
  reanchorStrokes,
  sanitizeStrokes,
  traceRegistration,
  type TracePoint,
} from '@/sections/admin/belege/registration';
import { isDevSetSpecimen } from '@/sections/admin/belege/tracebenchDevSet';
import { TraceCanvas } from '@/sections/admin/shell/TraceCanvas';
import { garamond } from '@/styles/paper';

// Anpassen falloff radius (x-height units): the default covers a typical
// wobble without reaching the neighbouring letter; the slider range keeps it
// between "one bump" and "half a body".
const NUDGE_DEFAULT_XH = 0.25;
const NUDGE_MIN_XH = 0.1;
const NUDGE_MAX_XH = 0.8;

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
  // The row's stored frame — and, when the sidecar lineature moved under it
  // (the exporter's frame gate), the HEALED frame the editor works in instead:
  // saving in the stale frame would echo it back verbatim and the row would
  // stay `frame_stale` forever, so a stale row re-anchors on open — the
  // strokes keep their crop-pixel place, the frame becomes the sidecar's.
  const storedReg = useMemo(() => traceRegistration(row.measurements, sample), [row.measurements, sample]);
  const stale = frameStale(storedReg, sample);
  const reg = useMemo(
    () =>
      stale
        ? { xh: sample.baseline_y - sample.midband_y, tx: storedReg.tx, baselineRow: sample.baseline_y }
        : storedReg,
    [stale, storedReg, sample],
  );
  const baseStrokes = useMemo(
    () => (stale ? reanchorStrokes(copyStrokes(row.strokes), storedReg, reg) : copyStrokes(row.strokes)),
    [stale, row.strokes, storedReg, reg],
  );
  const [strokes, setStrokes] = useState<TracePoint[][]>(() => copyStrokes(baseStrokes));
  // Zoom factor for the drawing surface (1 = dialog width). Default 0.2: on
  // the fullscreen canvas that lands near natural pen-on-paper writing size
  // (author-calibrated on the tablet), so most words need no adjustment.
  const [zoom, setZoom] = useState(0.2);
  // Explicit MODE instead of finger gestures: while writing, the resting hand
  // and stray fingers constantly shoved the view around. In draw and adjust
  // mode touch input is fully inert; in pan mode every pointer drags the view.
  // Anpassen (adjust) drags the drawn line locally instead of adding strokes —
  // the wizard's Weg mechanism, for ironing a tablet wobble out of one spot.
  const [mode, setMode] = useState<'draw' | 'adjust' | 'pan'>('draw');
  const [nudgeRadius, setNudgeRadius] = useState(NUDGE_DEFAULT_XH);
  // A re-anchored (previously stale) frame is itself worth saving — the row
  // only heals once the fresh registration is stored.
  const [dirty, setDirty] = useState(stale);
  const [showStored, setShowStored] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hand, setHand] = useState<HandOut | null>(null);
  const [handFailed, setHandFailed] = useState(false);
  // Editing one of the ten frozen dev-split words re-baselines the trace
  // bench; the save asks once instead of silently rewriting the ruler.
  const [confirmDev, setConfirmDev] = useState(false);

  const handId = row.hand_id ?? fallbackHandId;

  // No reset effect: the caller mounts the dialog per occurrence (keyed by the
  // row identity), so the state initialisers above already are the fresh start.

  // The hand is echoed back as read: the batch upserts the writer row whole, so
  // sending anything less than the stored fields would wipe its era/note as a
  // side effect. Saving stays disabled until the row is resolved.
  useEffect(() => {
    if (!open || !handId) return;
    let cancelled = false;
    getHand(handId, { retries: 1 })
      .then((h) => {
        if (!cancelled) {
          setHand(h);
          setHandFailed(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setHand(null);
          setHandFailed(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [open, handId]);

  const savable = useMemo(() => sanitizeStrokes(strokes), [strokes]);
  const canSave = open && dirty && savable.length > 0 && !saving && hand !== null;
  const devWord = isDevSetSpecimen(row.kind, row.specimen_id);

  const save = async () => {
    if (!hand) return;
    // A dev-split word is the frozen ruler's reference — ask once, explicitly,
    // instead of silently rewriting what every §14 number was measured against.
    if (devWord && !confirmDev) {
      setConfirmDev(true);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const res = await putWordInstances(sourceId, {
        hand: { id: hand.id, label: hand.label, era: hand.era, note: hand.note },
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

  // Full screen with every control ABOVE the drawing surface: while writing
  // with the pen, the hand rests exactly where footer controls would sit and
  // a graze there used to interrupt the stroke. Nothing clickable below the
  // word — the canvas owns the rest of the viewport.
  //
  // The paper suppresses text selection and the context menu: an S-Pen
  // long-press otherwise selects the hint text (native selection handles +
  // copy toolbar) or opens the browser context menu mid-stroke. Buttons and
  // the slider are unaffected; the InfoHint popover renders in a portal
  // outside the paper and stays selectable.
  return (
    <Dialog
      open={open}
      onClose={onClose}
      fullScreen
      slotProps={{
        paper: {
          sx: { userSelect: 'none' },
          onContextMenu: (e: React.MouseEvent) => e.preventDefault(),
        },
      }}
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', py: 1 }}>
        <Typography component="span" sx={{ fontFamily: garamond, fontSize: 24, lineHeight: 1 }}>
          {row.word}
        </Typography>
        <Typography component="span" variant="body2" color="textSecondary">
          {fmt(t.editorTitle, { specimen: row.specimen_id })}
        </Typography>
        <InfoHint title={t.editOpen}>
          {t.editorIntro} {t.editorAuthoredHint}
        </InfoHint>
        <Typography variant="caption" color="textSecondary" sx={{ ml: 'auto' }}>
          {fmt(t.editorStrokeCount, { strokes: savable.length })} · {fmt(t.editorSlots, { slots: row.slots.join(' ') })}
        </Typography>
        <Button size="small" onClick={onClose} disabled={saving}>
          {t.editorClose}
        </Button>
        <Button size="small" variant="contained" color={confirmDev ? 'warning' : 'primary'} onClick={save} disabled={!canSave}>
          {confirmDev ? t.editorSaveDevConfirm : t.editorSave}
        </Button>
      </DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', minHeight: 0, pb: 1 }}>
        <Box sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Draw · adjust · pan as an explicit toggle (the wizard's pattern):
              gestures on the canvas cannot coexist with a resting writing
              hand. Adjust drags the drawn line locally — for the tablet
              wobble a whole redraw would be disproportionate to. */}
          <ToggleButtonGroup
            size="small"
            exclusive
            aria-label={t.editorModeGroup}
            value={mode}
            onChange={(_, v: 'draw' | 'adjust' | 'pan' | null) => v !== null && setMode(v)}
          >
            <ToggleButton value="draw">{t.editorModeDraw}</ToggleButton>
            <ToggleButton value="adjust">{t.editorModeAdjust}</ToggleButton>
            <ToggleButton value="pan">{t.editorModePan}</ToggleButton>
          </ToggleButtonGroup>
          {mode === 'adjust' && (
            <>
              <Typography variant="caption" color="textSecondary" sx={{ minWidth: 88 }}>
                {t.editorNudgeRadius} {nudgeRadius.toLocaleString('de-DE', { maximumFractionDigits: 2 })}
              </Typography>
              <Slider
                size="small"
                value={nudgeRadius}
                min={NUDGE_MIN_XH}
                max={NUDGE_MAX_XH}
                step={0.05}
                // Snapped to the 0.05 grid — MUI accumulates min + k·step in
                // floats (same fix as the zoom slider above).
                onChange={(_, v) => setNudgeRadius(Math.round((v as number) * 20) / 20)}
                aria-label={t.editorNudgeRadius}
                sx={{ width: 140, flexShrink: 0, mx: 1 }}
              />
            </>
          )}
          {/* The value lives in this permanent label: the slider sits directly
              under the dialog title, so MUI's pop-up value tooltip is clipped
              by the header and never readable. minWidth keeps the row from
              jittering as the number's width changes while dragging. */}
          <Typography variant="caption" color="textSecondary" sx={{ minWidth: 74 }}>
            {t.editorZoom} {zoom.toLocaleString('de-DE', { maximumFractionDigits: 2 })}×
          </Typography>
          <Slider
            size="small"
            value={zoom}
            // 0.1–2: fullscreen made the 1× baseline much larger than the old
            // dialog width, so natural writing size sits well below 1× — and
            // tablet use showed zoom beyond 2× goes unused while making the
            // slider too coarse to set precisely (8× packed 158 steps into
            // its width; 2× leaves 38).
            min={0.1}
            max={2}
            step={0.05}
            // Snapped to the 0.05 grid: MUI accumulates min + k·step in
            // floats, so raw values arrive as 0.15000000000000002 etc.
            onChange={(_, v) => setZoom(Math.round((v as number) * 20) / 20)}
            aria-label={t.editorZoom}
            sx={{ width: 220, flexShrink: 0, mx: 1 }}
          />
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
              setStrokes(copyStrokes(baseStrokes));
              // A stale row stays dirty: only a SAVE stores the healed frame.
              setDirty(stale);
              setConfirmDev(false);
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
          <Typography variant="caption" color="textSecondary">
            {mode === 'adjust' ? t.editorAdjustHint : t.editorZoomHint}
          </Typography>
        </Box>
        {stale && (
          <Alert severity="info" sx={{ mb: 1 }}>
            {t.editorFrameReanchored}
          </Alert>
        )}
        {devWord && dirty && (
          <Alert severity="warning" sx={{ mb: 1 }}>
            {t.editorDevWordWarning}
          </Alert>
        )}
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
        {handId !== null && handFailed && (
          <Alert severity="warning" sx={{ mb: 1 }}>
            {fmt(t.editorHandUnresolved, { id: handId })}
          </Alert>
        )}
        {/* The drawing surface itself is shared with the Eigenhand's strip
            editor (`shell/TraceCanvas`): same viewBox, same pen rules, same
            registration matrix. Only the picture underneath differs — the
            specimen crop route is deliberately PUBLIC so a bare `<image href>`
            can load it without the admin header (`api/routers/word_samples.py`),
            which is exactly what the strip crop cannot do. */}
        <TraceCanvas
          width={sample.width}
          height={sample.height}
          reg={reg}
          strokes={strokes}
          onStrokes={setStrokes}
          onDirty={() => setDirty(true)}
          mode={mode}
          zoom={zoom}
          nudgeRadius={nudgeRadius}
          ghost={showStored && dirty ? baseStrokes : null}
          underlay={
            <image
              href={wordSampleCropUrl(sourceId, sample.id)}
              x={0}
              y={0}
              width={sample.width}
              height={sample.height}
              preserveAspectRatio="none"
            />
          }
        />
      </DialogContent>
    </Dialog>
  );
}
