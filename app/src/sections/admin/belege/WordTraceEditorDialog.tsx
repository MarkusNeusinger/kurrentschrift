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
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Slider,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useRef, useState } from 'react';

import { InfoHint } from '@/components/InfoHint';
import { getHand, putWordInstances, wordSampleCropUrl } from '@/lib/api';
import type { HandOut, WordInstanceOut, WordSampleOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { overlay } from '@/sections/admin/overlayColors';
import {
  cropToTrace,
  frameStale,
  reanchorStrokes,
  registrationMatrix,
  sanitizeStrokes,
  strokePathD,
  traceRegistration,
  warpTraceStrokes,
  type TracePoint,
} from '@/sections/admin/belege/registration';
import { isDevSetSpecimen } from '@/sections/admin/belege/tracebenchDevSet';
import { holdsGrip, releaseGrip, takeGrip, type Grip } from '@/sections/admin/setup-wizard/gestureUtils';
import { garamond } from '@/styles/paper';

// Minimum pointer travel between two stored samples (x-height units) — dense
// enough for a faithful ductus, sparse enough to stay far below the schema's
// per-stroke point cap on a slow, deliberate trace.
const MIN_STEP_XH = 0.015;

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
  // Falloff ring under the pointer in adjust mode (crop px), so the writer
  // sees what a drag would move before touching down.
  const [hoverPt, setHoverPt] = useState<TracePoint | null>(null);

  const svgRef = useRef<SVGSVGElement | null>(null);
  const gripRef = useRef<Grip>({ current: null });
  // The adjust drag warps a SNAPSHOT frozen at pen-down: every move re-warps
  // the same base geometry, so the deformation follows the pointer instead of
  // compounding sample by sample (the wizard's nudge pattern).
  const nudgeRef = useRef<{ grab: TracePoint; snapshot: TracePoint[][] } | null>(null);
  // True only while a DRAW gesture this handler started is in flight. The move
  // handler appends solely under this flag — never merely because the grip is
  // held — so a mid-drag mode flip (a stray toolbar graze; the reason every
  // control sits above the canvas) can never weld pen samples onto a stored
  // stroke it did not open.
  const drawingRef = useRef(false);
  // Manual panning (only ever active in pan MODE): the canvas carries
  // touch-action: none, because Chromium treats the PEN as a pannable pointer
  // too — with `pan-x pan-y` a short pen stroke was recognised as a scroll
  // gesture, the browser fired pointercancel and the drawn line broke off.
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const panRef = useRef<{ id: number; x: number; y: number; left: number; top: number } | null>(null);

  const matrix = useMemo(() => registrationMatrix(reg), [reg]);
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

  const toCropPx = (clientX: number, clientY: number): TracePoint | null => {
    const svg = svgRef.current;
    if (!svg) return null;
    const box = svg.getBoundingClientRect();
    if (box.width === 0 || box.height === 0) return null;
    return [((clientX - box.left) / box.width) * sample.width, ((clientY - box.top) / box.height) * sample.height];
  };

  const toTrace = (clientX: number, clientY: number): TracePoint | null => {
    const px = toCropPx(clientX, clientY);
    return px ? cropToTrace(reg, px) : null;
  };

  const onPointerDown = (e: React.PointerEvent<SVGSVGElement>) => {
    // Pan is an explicit MODE, never a gesture: in draw and adjust mode touch
    // input is completely inert (the writing hand rests on the display), in
    // pan mode any pointer — pen, mouse or finger — drags the view.
    if (mode === 'pan') {
      if (panRef.current === null && scrollRef.current) {
        panRef.current = {
          id: e.pointerId,
          x: e.clientX,
          y: e.clientY,
          left: scrollRef.current.scrollLeft,
          top: scrollRef.current.scrollTop,
        };
        e.currentTarget.setPointerCapture(e.pointerId);
      }
      return;
    }
    if (e.pointerType === 'touch') return;
    const p = toTrace(e.clientX, e.clientY);
    if (!p) return;
    // One pointer at a time: a second pen contact must not hijack the stroke
    // the pen is drawing (same rule as the wizard canvas).
    if (!takeGrip(gripRef.current, e.pointerId)) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    if (mode === 'adjust') {
      // Freeze the base geometry; the drag warps this snapshot per move.
      nudgeRef.current = { grab: p, snapshot: strokes };
      return;
    }
    drawingRef.current = true;
    setStrokes((prev) => [...prev, [p]]);
    setDirty(true);
  };

  const onPointerMove = (e: React.PointerEvent<SVGSVGElement>) => {
    const pan = panRef.current;
    if (pan && e.pointerId === pan.id) {
      if (scrollRef.current) {
        scrollRef.current.scrollLeft = pan.left - (e.clientX - pan.x);
        scrollRef.current.scrollTop = pan.top - (e.clientY - pan.y);
      }
      return;
    }
    // The falloff ring follows the pointer in adjust mode — also on a pure
    // hover (pen in the air, mouse without button), so the reach is visible
    // before anything moves.
    if (mode === 'adjust' && e.pointerType !== 'touch') {
      setHoverPt(toCropPx(e.clientX, e.clientY));
    }
    if (!holdsGrip(gripRef.current, e.pointerId)) return;
    const p = toTrace(e.clientX, e.clientY);
    if (!p) return;
    // Branch on the GESTURE state, never on `mode`: a toolbar graze can flip
    // the mode mid-drag, and the fall-through must not reinterpret the pen.
    const nudge = nudgeRef.current;
    if (nudge) {
      setStrokes(warpTraceStrokes(nudge.snapshot, nudge.grab, p[0] - nudge.grab[0], p[1] - nudge.grab[1], nudgeRadius));
      setDirty(true);
      return;
    }
    if (!drawingRef.current) return;
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
    if (panRef.current?.id === e.pointerId) {
      panRef.current = null;
      return;
    }
    if (!releaseGrip(gripRef.current, e.pointerId)) return;
    if (nudgeRef.current) {
      nudgeRef.current = null;
      return;
    }
    if (!drawingRef.current) return;
    drawingRef.current = false;
    setStrokes((prev) => (prev.length && prev[prev.length - 1].length < 2 ? prev.slice(0, -1) : prev));
  };

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

  const midbandRow = reg.baselineRow - reg.xh;

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
        <Typography component="span" variant="body2" color="text.secondary">
          {fmt(t.editorTitle, { specimen: row.specimen_id })}
        </Typography>
        <InfoHint title={t.editOpen}>
          {t.editorIntro} {t.editorAuthoredHint}
        </InfoHint>
        <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
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
            onChange={(_, v: 'draw' | 'adjust' | 'pan' | null) => {
              if (v === null) return;
              setMode(v);
              if (v !== 'adjust') setHoverPt(null);
              // A mode change ends any in-flight gesture: the next samples of
              // a still-held pointer must not be reinterpreted in the new mode.
              nudgeRef.current = null;
              drawingRef.current = false;
            }}
          >
            <ToggleButton value="draw">{t.editorModeDraw}</ToggleButton>
            <ToggleButton value="adjust">{t.editorModeAdjust}</ToggleButton>
            <ToggleButton value="pan">{t.editorModePan}</ToggleButton>
          </ToggleButtonGroup>
          {mode === 'adjust' && (
            <>
              <Typography variant="caption" color="text.secondary" sx={{ minWidth: 88 }}>
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
          <Typography variant="caption" color="text.secondary" sx={{ minWidth: 74 }}>
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
          <Typography variant="caption" color="text.secondary">
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
        {/* display:flex + margin:auto on the svg centres a small (shrunk) word
            in BOTH axes of the free canvas area — the writing zone moves to
            the middle of the screen, away from the header controls a resting
            pen hand kept grazing; an enlarged word overflows and scrolls
            exactly as before (margin:auto is the clip-safe centring pattern
            inside a scroll container). */}
        <Box ref={scrollRef} sx={{ flex: 1, minHeight: 0, overflow: 'auto', borderRadius: '6px', display: 'flex' }}>
        <svg
          ref={svgRef}
          viewBox={`0 0 ${sample.width} ${sample.height}`}
          style={{
            display: 'block',
            width: `${zoom * 100}%`,
            // Centred in both axes of the canvas area (see the flex container
            // above) — a shrunk word floats mid-screen instead of hugging the
            // top edge right under the controls.
            margin: 'auto',
            flexShrink: 0,
            background: '#fff',
            borderRadius: 6,
            // NO browser gestures on the canvas: Chromium treats the pen as a
            // pannable pointer, so `pan-x pan-y` let the browser cancel a pen
            // stroke after a short distance and scroll instead. Fingers still
            // pan — via the manual handler on panRef, not the browser.
            touchAction: 'none',
            cursor: mode === 'pan' ? 'grab' : mode === 'adjust' ? 'default' : 'crosshair',
          }}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
          onPointerLeave={() => setHoverPt(null)}
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
              baseStrokes.map((stroke, i) => (
                <path
                  key={`stored-${i}`}
                  d={strokePathD(stroke.map(([x, y]) => [x, y] as TracePoint))}
                  fill="none"
                  stroke="#8b9a95"
                  strokeOpacity={0.6}
                  strokeWidth={1.5}
                  vectorEffect="non-scaling-stroke"
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
                // Fixed 2 CSS pixels via non-scaling-stroke: the previous
                // zoom-compensated width was constant relative to the CONTAINER,
                // which on a fullscreen tablet made the line far fatter than the
                // shrunk ink it was supposed to trace.
                strokeWidth={2}
                vectorEffect="non-scaling-stroke"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            ))}
          </g>
          {/* Falloff ring under the pointer (adjust mode): everything inside
              follows a drag, weighted toward the centre. Crop-px frame, so the
              radius scales with the crop exactly like the warp itself. */}
          {mode === 'adjust' && hoverPt && (
            <circle
              cx={hoverPt[0]}
              cy={hoverPt[1]}
              r={nudgeRadius * reg.xh}
              fill={overlay.draft}
              fillOpacity={0.06}
              stroke={overlay.draft}
              strokeOpacity={0.55}
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
              strokeDasharray="4 3"
              pointerEvents="none"
            />
          )}
        </svg>
        </Box>
      </DialogContent>
    </Dialog>
  );
}
