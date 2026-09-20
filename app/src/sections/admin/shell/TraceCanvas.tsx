// The surface a Bahn is drawn on — one geometry for both re-tracing editors.
//
// Extracted from `belege/WordTraceEditorDialog` when the Eigenhand got its own
// editor beside the plate one (author decision G, 2026-09-20). Everything
// between the pointer and the stored coordinate is common and lives here: the
// crop-pixel viewBox, the registration matrix, the pen rules (one pointer at a
// time, touch inert while writing, a pen-down that never moved is a lift, not
// a stroke), the Anpassen warp, the manual pan and the drawn lineature.
//
// What is NOT common is the picture underneath — the plate crop is a public
// route an `<image href>` can load, the strip crop is admin-gated and
// `private, no-store`, so it arrives as a blob — and what a save writes. Both
// are the caller's business. Copying the geometry into the second editor
// instead of sharing it would have let the two surfaces disagree about where a
// stroke lies, which is the one defect that looks like nothing on screen.
//
// `mode` carries a fourth value the plate editor never uses: `point` hands
// every pen sample to the caller as a CROP-pixel position and changes nothing
// itself. That is how the strip editor drags a letter boundary without a
// second pointer implementation growing beside this one.

import { Box } from '@mui/material';
import { useEffect, useRef, useState, type Dispatch, type ReactNode, type SetStateAction } from 'react';

import { overlay } from '@/sections/admin/overlayColors';
import {
  cropToTrace,
  registrationMatrix,
  strokePathD,
  warpTraceStrokes,
  type TracePoint,
  type TraceRegistration,
} from '@/sections/admin/belege/registration';
import { holdsGrip, releaseGrip, takeGrip, type Grip } from '@/sections/admin/setup-wizard/gestureUtils';

// Minimum pointer travel between two stored samples (x-height units) — dense
// enough for a faithful ductus, sparse enough to stay far below the schema's
// per-stroke point cap on a slow, deliberate trace.
const MIN_STEP_XH = 0.015;

// The stored line behind the drawn one: a muted grey-green that reads as „was
// here before" beside the draft colour without competing with the ink.
const GHOST_COLOR = '#8b9a95';

export type TraceMode = 'draw' | 'adjust' | 'pan' | 'point';

export type PointPhase = 'down' | 'move' | 'up';

interface Props {
  /** The underlay's own pixel frame — what the viewBox spans. */
  width: number;
  height: number;
  /** The frame the strokes are stored in, expressed in those pixels. */
  reg: TraceRegistration;
  strokes: TracePoint[][];
  onStrokes: Dispatch<SetStateAction<TracePoint[][]>>;
  /** Called for every change a save would have to store. */
  onDirty: () => void;
  mode: TraceMode;
  /** Canvas width as a fraction of the available area (1 = full width). */
  zoom: number;
  /** Falloff radius of the Anpassen drag, in x-heights. */
  nudgeRadius: number;
  /** The picture under the line, as SVG the caller builds. */
  underlay: ReactNode;
  /** The stored line as a ghost, where the caller wants one shown. */
  ghost?: TracePoint[][] | null;
  /** Extra SVG in CROP pixels, drawn over the strokes. */
  overlayNode?: ReactNode;
  /** Every pen sample in `point` mode, in CROP pixels. */
  onPoint?: (point: TracePoint, phase: PointPhase) => void;
}

export function TraceCanvas({
  width,
  height,
  reg,
  strokes,
  onStrokes,
  onDirty,
  mode,
  zoom,
  nudgeRadius,
  underlay,
  ghost = null,
  overlayNode,
  onPoint,
}: Props) {
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
  // The same rule for the neutral `point` mode: what the caller receives is a
  // gesture this canvas opened, never a stray move.
  const pointingRef = useRef(false);
  // Manual panning (only ever active in pan MODE): the canvas carries
  // touch-action: none, because Chromium treats the PEN as a pannable pointer
  // too — with `pan-x pan-y` a short pen stroke was recognised as a scroll
  // gesture, the browser fired pointercancel and the drawn line broke off.
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const panRef = useRef<{ id: number; x: number; y: number; left: number; top: number } | null>(null);

  const matrix = registrationMatrix(reg);
  const midbandRow = reg.baselineRow - reg.xh;

  // A mode change ends any in-flight gesture: the next samples of a still-held
  // pointer must not be reinterpreted in the new mode. It lived in the plate
  // editor's own toggle handler before the extraction; here it belongs to the
  // refs it clears, so every caller gets the rule rather than remembering it.
  useEffect(() => {
    nudgeRef.current = null;
    drawingRef.current = false;
    pointingRef.current = false;
  }, [mode]);

  const toCropPx = (clientX: number, clientY: number): TracePoint | null => {
    const svg = svgRef.current;
    if (!svg) return null;
    const box = svg.getBoundingClientRect();
    if (box.width === 0 || box.height === 0) return null;
    return [((clientX - box.left) / box.width) * width, ((clientY - box.top) / box.height) * height];
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
    if (mode === 'point') {
      pointingRef.current = true;
      const px = toCropPx(e.clientX, e.clientY);
      if (px) onPoint?.(px, 'down');
      return;
    }
    if (mode === 'adjust') {
      // Freeze the base geometry; the drag warps this snapshot per move.
      nudgeRef.current = { grab: p, snapshot: strokes };
      return;
    }
    drawingRef.current = true;
    onStrokes((prev) => [...prev, [p]]);
    onDirty();
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
    if (pointingRef.current) {
      const px = toCropPx(e.clientX, e.clientY);
      if (px) onPoint?.(px, 'move');
      return;
    }
    const nudge = nudgeRef.current;
    if (nudge) {
      onStrokes(warpTraceStrokes(nudge.snapshot, nudge.grab, p[0] - nudge.grab[0], p[1] - nudge.grab[1], nudgeRadius));
      onDirty();
      return;
    }
    if (!drawingRef.current) return;
    onStrokes((prev) => {
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
    if (pointingRef.current) {
      pointingRef.current = false;
      const px = toCropPx(e.clientX, e.clientY);
      if (px) onPoint?.(px, 'up');
      return;
    }
    if (nudgeRef.current) {
      nudgeRef.current = null;
      return;
    }
    if (!drawingRef.current) return;
    drawingRef.current = false;
    onStrokes((prev) => (prev.length && prev[prev.length - 1].length < 2 ? prev.slice(0, -1) : prev));
  };

  return (
    // display:flex + margin:auto on the svg centres a small (shrunk) word in
    // BOTH axes of the free canvas area — the writing zone moves to the middle
    // of the screen, away from the header controls a resting pen hand kept
    // grazing; an enlarged word overflows and scrolls exactly as before
    // (margin:auto is the clip-safe centring pattern inside a scroll container).
    <Box
      ref={scrollRef}
      data-trace-canvas={mode}
      sx={{ flex: 1, minHeight: 0, overflow: 'auto', borderRadius: '6px', display: 'flex' }}
    >
      <svg
        ref={svgRef}
        viewBox={`0 0 ${width} ${height}`}
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
          cursor: mode === 'pan' ? 'grab' : mode === 'draw' ? 'crosshair' : 'default',
        }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onPointerLeave={() => setHoverPt(null)}
      >
        {underlay}
        {/* Grundlinie + Mittellinie of the registration frame the trace is
            stored in — the writer sees which line their v = 0/1 sits on. */}
        <line
          x1={0}
          x2={width}
          y1={reg.baselineRow}
          y2={reg.baselineRow}
          stroke={overlay.idle}
          strokeWidth={0.6}
          strokeOpacity={0.7}
        />
        <line
          x1={0}
          x2={width}
          y1={midbandRow}
          y2={midbandRow}
          stroke={overlay.idle}
          strokeWidth={0.6}
          strokeOpacity={0.5}
          strokeDasharray="3 3"
        />
        <g transform={matrix}>
          {(ghost ?? []).map((stroke, i) => (
            <path
              key={`stored-${i}`}
              d={strokePathD(stroke)}
              fill="none"
              stroke={GHOST_COLOR}
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
              // Fixed 2 CSS pixels via non-scaling-stroke: a zoom-compensated
              // width would be constant relative to the CONTAINER, which on a
              // fullscreen tablet makes the line far fatter than the shrunk
              // ink it is supposed to trace.
              strokeWidth={2}
              vectorEffect="non-scaling-stroke"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          ))}
        </g>
        {overlayNode}
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
  );
}
