// ChartCanvas — chart.jpg with bbox + exclude + calibration overlays.
//
// Two interaction modes, both via pointerdown/move/up:
//   - default: drag with primary button creates a NEW bbox for the
//     currently-selected glyph (replaces existing bbox if there is one).
//   - shift+drag inside the selected bbox: adds an exclude rectangle.
//
// All coords are in chart-image pixel space (1633×1869). We render the
// chart at its natural size inside a scrollable wrapper; no zoom UI in
// v1 — the user pans by scrolling. CSS pixel == chart pixel.

import { useCallback, useEffect, useRef, useState } from 'react';
import { chartUrl, putBbox } from '../api';
import type { ExcludeRect, GlyphBbox } from '../types';

interface Props {
  chartSize: [number, number];
  bboxes: Record<string, GlyphBbox | null>;
  selected: string | null;
  onChange: (key: string, next: GlyphBbox | null) => void;
}

interface DragState {
  mode: 'bbox' | 'exclude';
  startX: number;
  startY: number;
  curX: number;
  curY: number;
}

export function ChartCanvas({ chartSize, bboxes, selected, onChange }: Props) {
  const [width, height] = chartSize;
  const stageRef = useRef<HTMLDivElement | null>(null);
  const [drag, setDrag] = useState<DragState | null>(null);

  const pointToImage = useCallback((clientX: number, clientY: number) => {
    const el = stageRef.current;
    if (!el) return { x: 0, y: 0 };
    const rect = el.getBoundingClientRect();
    return {
      x: Math.max(0, Math.min(width, Math.round(clientX - rect.left))),
      y: Math.max(0, Math.min(height, Math.round(clientY - rect.top))),
    };
  }, [width, height]);

  const onPointerDown = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      if (!selected) return;
      if (e.button !== 0) return;
      // Pen drawing is reserved for the StylusTracer (right panel).
      if (e.pointerType === 'pen') return;
      const { x, y } = pointToImage(e.clientX, e.clientY);
      const isShift = e.shiftKey;
      const current = bboxes[selected];
      if (isShift && current && x >= current.x0 && x <= current.x1 && y >= current.y0 && y <= current.y1) {
        setDrag({ mode: 'exclude', startX: x, startY: y, curX: x, curY: y });
      } else {
        setDrag({ mode: 'bbox', startX: x, startY: y, curX: x, curY: y });
      }
      (e.target as Element).setPointerCapture?.(e.pointerId);
    },
    [selected, bboxes, pointToImage],
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      if (!drag) return;
      const { x, y } = pointToImage(e.clientX, e.clientY);
      setDrag({ ...drag, curX: x, curY: y });
    },
    [drag, pointToImage],
  );

  const onPointerUp = useCallback(async () => {
    if (!drag || !selected) {
      setDrag(null);
      return;
    }
    const x0 = Math.min(drag.startX, drag.curX);
    const y0 = Math.min(drag.startY, drag.curY);
    const x1 = Math.max(drag.startX, drag.curX);
    const y1 = Math.max(drag.startY, drag.curY);
    if (x1 - x0 < 6 || y1 - y0 < 6) {
      setDrag(null);
      return;
    }
    const current: GlyphBbox | null = bboxes[selected];
    let next: GlyphBbox;
    if (drag.mode === 'exclude' && current) {
      const ex: ExcludeRect = { x0, y0, x1, y1 };
      next = { ...current, exclude: [...current.exclude, ex] };
    } else {
      // creating/replacing the main bbox — preserve calibration if present
      next = {
        x0,
        y0,
        x1,
        y1,
        exclude: [],
        baseline_y: current?.baseline_y ?? null,
        midband_y: current?.midband_y ?? null,
        start_xy: current?.start_xy ?? null,
        n_anchors: current?.n_anchors ?? null,
      };
    }
    setDrag(null);
    try {
      const saved = await putBbox(selected, next);
      onChange(selected, saved);
    } catch (err) {
      console.error('putBbox failed', err);
    }
  }, [drag, selected, bboxes, onChange]);

  // ESC clears in-progress drag.
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setDrag(null);
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, []);

  return (
    <div className="panel chart-wrap" style={{ padding: 0 }}>
      <div className="chart-stage" ref={stageRef} style={{ width, height, position: 'relative' }}>
        <img src={chartUrl()} alt="Loth 1866 chart" width={width} height={height} draggable={false} />
        <svg className="overlay-svg" width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
          {Object.entries(bboxes).map(([key, b]) => {
            if (!b) return null;
            const isSelected = key === selected;
            const stroke = isSelected ? '#ffae00' : '#5da8ff';
            return (
              <g key={key}>
                <rect
                  x={b.x0}
                  y={b.y0}
                  width={b.x1 - b.x0}
                  height={b.y1 - b.y0}
                  fill="none"
                  stroke={stroke}
                  strokeWidth={isSelected ? 3 : 1.5}
                  strokeDasharray={isSelected ? undefined : '4 4'}
                />
                <text
                  x={b.x0}
                  y={b.y0 - 4}
                  fontSize={14}
                  fill={stroke}
                  style={{ pointerEvents: 'none', userSelect: 'none' }}
                >
                  {key}
                </text>
                {b.exclude.map((ex, i) => (
                  <rect
                    key={i}
                    x={ex.x0}
                    y={ex.y0}
                    width={ex.x1 - ex.x0}
                    height={ex.y1 - ex.y0}
                    fill={stroke}
                    fillOpacity={0.18}
                    stroke={stroke}
                    strokeDasharray="3 3"
                    strokeWidth={1}
                  />
                ))}
              </g>
            );
          })}
          {drag && (
            <rect
              x={Math.min(drag.startX, drag.curX)}
              y={Math.min(drag.startY, drag.curY)}
              width={Math.abs(drag.curX - drag.startX)}
              height={Math.abs(drag.curY - drag.startY)}
              fill={drag.mode === 'exclude' ? '#ff6b35' : '#00d2ff'}
              fillOpacity={0.15}
              stroke={drag.mode === 'exclude' ? '#ff6b35' : '#00d2ff'}
              strokeWidth={1.5}
              strokeDasharray="5 3"
            />
          )}
        </svg>
        <div
          className="interact-layer"
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={() => setDrag(null)}
          style={{ position: 'absolute', inset: 0, cursor: selected ? 'crosshair' : 'default' }}
        />
      </div>
    </div>
  );
}
