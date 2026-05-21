// RightPanel — shows the cropped Loth glyph (via /chart/crop) with
// draggable baseline/midband calibration lines and an overlaid stylus
// tracer for capturing the ductus path. "Save Canonical" POSTs the
// captured path to the backend.

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { cropUrl, postTrace, putBbox } from '../api';
import type { Canonical, GlyphBbox, StrokePoint } from '../types';

interface Props {
  glyphKey: string | null;
  bbox: GlyphBbox | null;
  cropCacheBust: number;
  onBboxChange: (key: string, next: GlyphBbox | null) => void;
  onCanonicalSaved: (key: string, canon: Canonical) => void;
}

type CalibField = 'baseline_y' | 'midband_y';

interface DragCalibState {
  field: CalibField;
  startY: number;     // chart-y at pointerdown
  curY: number;       // chart-y now
}

export function RightPanel({ glyphKey, bbox, cropCacheBust, onBboxChange, onCanonicalSaved }: Props) {
  const cropRef = useRef<HTMLDivElement | null>(null);
  const [pathPts, setPathPts] = useState<StrokePoint[]>([]);
  const [tracing, setTracing] = useState(false);
  const [drawing, setDrawing] = useState(false);
  const [msg, setMsg] = useState<{ kind: 'ok' | 'err' | 'info'; text: string } | null>(null);
  const [dragCalib, setDragCalib] = useState<DragCalibState | null>(null);

  // Crop dimensions in chart-pixel coords.
  const cropPxWidth = bbox ? bbox.x1 - bbox.x0 : 0;
  const cropPxHeight = bbox ? bbox.y1 - bbox.y0 : 0;

  // Scale-to-fit factor: how many CSS pixels per chart pixel inside the
  // crop pane. Layout sets the pane to 320px wide; image is upscaled.
  const displayWidthCss = 320;
  const scale = cropPxWidth > 0 ? displayWidthCss / cropPxWidth : 1;
  const displayHeightCss = cropPxHeight * scale;

  // Clear path + tracing when glyph changes.
  useEffect(() => {
    setPathPts([]);
    setTracing(false);
    setDrawing(false);
    setMsg(null);
  }, [glyphKey]);

  const cssToChartY = useCallback(
    (clientY: number): number => {
      const el = cropRef.current;
      if (!el || !bbox) return 0;
      const r = el.getBoundingClientRect();
      const localCss = clientY - r.top;
      const chartLocal = localCss / scale;
      return Math.round(bbox.y0 + chartLocal);
    },
    [bbox, scale],
  );

  const cssToChartXY = useCallback(
    (clientX: number, clientY: number): { x: number; y: number } => {
      const el = cropRef.current;
      if (!el || !bbox) return { x: 0, y: 0 };
      const r = el.getBoundingClientRect();
      const lx = (clientX - r.left) / scale;
      const ly = (clientY - r.top) / scale;
      return { x: bbox.x0 + lx, y: bbox.y0 + ly };
    },
    [bbox, scale],
  );

  // ---- Calibration line drag handlers ----
  const startCalibDrag = useCallback(
    (field: CalibField) => (e: React.PointerEvent<SVGLineElement>) => {
      e.stopPropagation();
      const y = cssToChartY(e.clientY);
      setDragCalib({ field, startY: y, curY: y });
      (e.target as Element).setPointerCapture?.(e.pointerId);
    },
    [cssToChartY],
  );

  const onCalibPointerMove = useCallback(
    (e: React.PointerEvent<SVGSVGElement>) => {
      if (!dragCalib) return;
      const y = cssToChartY(e.clientY);
      setDragCalib({ ...dragCalib, curY: y });
    },
    [dragCalib, cssToChartY],
  );

  const onCalibPointerUp = useCallback(async () => {
    if (!dragCalib || !glyphKey || !bbox) {
      setDragCalib(null);
      return;
    }
    const next: GlyphBbox = { ...bbox, [dragCalib.field]: dragCalib.curY };
    setDragCalib(null);
    try {
      const saved = await putBbox(glyphKey, next);
      onBboxChange(glyphKey, saved);
    } catch (err) {
      setMsg({ kind: 'err', text: `save calib failed: ${err}` });
    }
  }, [dragCalib, glyphKey, bbox, onBboxChange]);

  // ---- Stylus drawing handlers ----
  const onStylusDown = useCallback(
    (e: React.PointerEvent<SVGSVGElement>) => {
      if (!tracing) return;
      // Accept pen explicitly; mouse is allowed as a fallback for desktop testing.
      if (e.pointerType !== 'pen' && e.pointerType !== 'mouse') return;
      e.preventDefault();
      const { x, y } = cssToChartXY(e.clientX, e.clientY);
      setDrawing(true);
      setPathPts([{ x, y, pressure: e.pressure || null, t: 0 }]);
      (e.target as Element).setPointerCapture?.(e.pointerId);
    },
    [tracing, cssToChartXY],
  );

  const onStylusMove = useCallback(
    (e: React.PointerEvent<SVGSVGElement>) => {
      if (dragCalib) return onCalibPointerMove(e);
      if (!drawing) return;
      const { x, y } = cssToChartXY(e.clientX, e.clientY);
      setPathPts((prev) => {
        // Subsample: skip if the new point is closer than ~0.6 chart-px from prev.
        const last = prev[prev.length - 1];
        if (last) {
          const dx = x - last.x;
          const dy = y - last.y;
          if (dx * dx + dy * dy < 0.36) return prev;
        }
        return [...prev, { x, y, pressure: e.pressure || null, t: performance.now() }];
      });
    },
    [dragCalib, drawing, cssToChartXY, onCalibPointerMove],
  );

  const onStylusUp = useCallback(
    (e: React.PointerEvent<SVGSVGElement>) => {
      if (dragCalib) return onCalibPointerUp();
      setDrawing(false);
      e.preventDefault();
    },
    [dragCalib, onCalibPointerUp],
  );

  const saveTrace = useCallback(async () => {
    if (!glyphKey || pathPts.length < 2) return;
    setMsg({ kind: 'info', text: 'saving…' });
    try {
      const canon = await postTrace(glyphKey, { path: pathPts });
      onCanonicalSaved(glyphKey, canon);
      setMsg({ kind: 'ok', text: `saved · ${canon.strokes[0].anchors.length} anchors` });
      setPathPts([]);
      setTracing(false);
    } catch (err) {
      setMsg({ kind: 'err', text: String(err) });
    }
  }, [glyphKey, pathPts, onCanonicalSaved]);

  const setNAnchors = useCallback(
    async (n: number) => {
      if (!glyphKey || !bbox) return;
      const next: GlyphBbox = { ...bbox, n_anchors: n };
      try {
        const saved = await putBbox(glyphKey, next);
        onBboxChange(glyphKey, saved);
      } catch (err) {
        setMsg({ kind: 'err', text: `save n_anchors failed: ${err}` });
      }
    },
    [glyphKey, bbox, onBboxChange],
  );

  // Convert calibration y-values to CSS coords for SVG overlay.
  const baselineCss = useMemo(() => {
    if (!bbox || bbox.baseline_y == null) return null;
    return (bbox.baseline_y - bbox.y0) * scale;
  }, [bbox, scale]);
  const midbandCss = useMemo(() => {
    if (!bbox || bbox.midband_y == null) return null;
    return (bbox.midband_y - bbox.y0) * scale;
  }, [bbox, scale]);
  const dragCalibCss = useMemo(() => {
    if (!dragCalib || !bbox) return null;
    return (dragCalib.curY - bbox.y0) * scale;
  }, [dragCalib, bbox]);

  if (!glyphKey) return <div className="panel right-panel"><p>Select a glyph.</p></div>;
  if (!bbox) {
    return (
      <div className="panel right-panel">
        <h2>{glyphKey}</h2>
        <p className="msg">No bbox yet — drag a rectangle on the chart.</p>
      </div>
    );
  }

  return (
    <div className="panel right-panel">
      <h2>{glyphKey}</h2>

      <div className="crop-host" ref={cropRef} style={{ height: displayHeightCss || 100 }}>
        <img src={cropUrl(glyphKey, cropCacheBust)} alt={`${glyphKey} crop`} width={displayWidthCss} />
        <svg
          className="stylus-overlay"
          width={displayWidthCss}
          height={displayHeightCss}
          viewBox={`0 0 ${displayWidthCss} ${displayHeightCss}`}
          onPointerDown={onStylusDown}
          onPointerMove={onStylusMove}
          onPointerUp={onStylusUp}
          onPointerCancel={() => { setDrawing(false); setDragCalib(null); }}
          style={{ touchAction: 'none' }}
        >
          {/* Baseline line + handle */}
          {baselineCss != null && (
            <g>
              <line
                x1={0} y1={baselineCss} x2={displayWidthCss} y2={baselineCss}
                stroke="#ff5060" strokeWidth={1.5} strokeDasharray="5 3"
                style={{ cursor: 'ns-resize', pointerEvents: 'stroke' }}
                onPointerDown={startCalibDrag('baseline_y')}
              />
              <text x={4} y={baselineCss - 3} fontSize={10} fill="#ff5060">baseline {bbox.baseline_y}</text>
            </g>
          )}
          {midbandCss != null && (
            <g>
              <line
                x1={0} y1={midbandCss} x2={displayWidthCss} y2={midbandCss}
                stroke="#c060ff" strokeWidth={1.5} strokeDasharray="3 3"
                style={{ cursor: 'ns-resize', pointerEvents: 'stroke' }}
                onPointerDown={startCalibDrag('midband_y')}
              />
              <text x={4} y={midbandCss - 3} fontSize={10} fill="#c060ff">midband {bbox.midband_y}</text>
            </g>
          )}
          {dragCalibCss != null && (
            <line
              x1={0} y1={dragCalibCss} x2={displayWidthCss} y2={dragCalibCss}
              stroke={dragCalib?.field === 'baseline_y' ? '#ff5060' : '#c060ff'}
              strokeWidth={2}
            />
          )}
          {/* In-progress stroke */}
          {pathPts.length > 1 && (
            <polyline
              fill="none"
              stroke="#00d2ff"
              strokeWidth={2}
              points={pathPts.map((p) => `${(p.x - bbox.x0) * scale},${(p.y - bbox.y0) * scale}`).join(' ')}
            />
          )}
        </svg>
      </div>

      <div className="calib">
        <span>baseline_y</span>
        <input
          type="number"
          value={bbox.baseline_y ?? ''}
          onChange={async (e) => {
            const v = e.target.value === '' ? null : Number(e.target.value);
            const saved = await putBbox(glyphKey, { ...bbox, baseline_y: v });
            onBboxChange(glyphKey, saved);
          }}
        />
        <span>midband_y</span>
        <input
          type="number"
          value={bbox.midband_y ?? ''}
          onChange={async (e) => {
            const v = e.target.value === '' ? null : Number(e.target.value);
            const saved = await putBbox(glyphKey, { ...bbox, midband_y: v });
            onBboxChange(glyphKey, saved);
          }}
        />
        <span>n_anchors</span>
        <input
          type="number"
          value={bbox.n_anchors ?? ''}
          placeholder="14"
          onChange={(e) => setNAnchors(Number(e.target.value || 14))}
        />
      </div>

      <div className="row">
        <button
          onClick={() => {
            if (tracing) {
              setTracing(false);
              setPathPts([]);
            } else {
              setTracing(true);
              setPathPts([]);
              setMsg({ kind: 'info', text: 'tracing — draw the stroke with stylus' });
            }
          }}
          className={tracing ? 'secondary' : ''}
        >
          {tracing ? 'Cancel' : 'Trace stroke'}
        </button>
        <button disabled={pathPts.length < 2} onClick={saveTrace}>
          Save canonical
        </button>
      </div>

      <div className="row">
        <button
          className="secondary"
          onClick={async () => {
            const next: GlyphBbox = { ...bbox, exclude: [] };
            const saved = await putBbox(glyphKey, next);
            onBboxChange(glyphKey, saved);
          }}
          disabled={bbox.exclude.length === 0}
        >
          Clear excludes ({bbox.exclude.length})
        </button>
      </div>

      {msg && <p className={`msg ${msg.kind}`}>{msg.text}</p>}
      <p className="msg">
        bbox ({bbox.x0},{bbox.y0})→({bbox.x1},{bbox.y1}) · {pathPts.length} pts captured
      </p>
    </div>
  );
}
