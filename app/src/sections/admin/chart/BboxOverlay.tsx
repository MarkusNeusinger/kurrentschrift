// SVG overlay over the chart scan: bbox rects + labels + lock markers, the
// eraser-stroke outlines, the draw-new rubber band and the move/resize grips.
// Pure props — all state is derived in ChartView and passed in.

import { overlay } from '@/sections/admin/overlayColors';
import type { BboxOut } from '@/lib/api';
import type { Mode } from './chartConstants';
import type { Rect } from './bboxGeometry';
import type { DragState, EditState } from './useBboxEditing';

interface BboxOverlayProps {
  width: number;
  height: number;
  stageWidthCss: number;
  stageHeightCss: number;
  zoom: number;
  mode: Mode;
  bboxesByKey: Record<string, BboxOut>;
  visibleGlyphs: Set<string>;
  activeGlyph: string | null;
  activeLocked: boolean;
  drag: DragState | null;
  edit: EditState | null;
}

export function BboxOverlay({
  width,
  height,
  stageWidthCss,
  stageHeightCss,
  zoom,
  mode,
  bboxesByKey,
  visibleGlyphs,
  activeGlyph,
  activeLocked,
  drag,
  edit,
}: BboxOverlayProps) {
  return (
    <svg
      width={stageWidthCss}
      height={stageHeightCss}
      viewBox={`0 0 ${width} ${height}`}
      style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}
    >
      {Object.entries(bboxesByKey).map(([key, b]) => {
        if (!visibleGlyphs.has(key)) return null;
        const isActive = key === activeGlyph;
        // Locked (finished) glyphs read green; the active one stays orange
        // (thicker), unfinished ones are dashed blue. A locked glyph keeps
        // a solid outline so "done" is legible even when not selected.
        const stroke = b.locked ? overlay.locked : isActive ? overlay.active : overlay.idle;
        return (
          <g key={key}>
            <rect
              x={b.x0}
              y={b.y0}
              width={b.x1 - b.x0}
              height={b.y1 - b.y0}
              fill={b.locked ? overlay.locked : 'none'}
              fillOpacity={b.locked ? 0.08 : undefined}
              stroke={stroke}
              strokeWidth={isActive ? 3 : 1.5}
              strokeDasharray={isActive || b.locked ? undefined : '4 4'}
            />
            <text x={b.x0} y={b.y0 - 4} fontSize={14} fill={stroke} style={{ userSelect: 'none' }}>
              {b.locked ? `🔒 ${key}` : key}
            </text>
            {b.mask_strokes.map((m, i) => (
              <polyline
                key={i}
                points={m.points.map(([x, y]) => `${x},${y}`).join(' ')}
                fill="none"
                stroke={overlay.eraser}
                strokeOpacity={0.5}
                strokeWidth={Math.max(1, m.radius * 2)}
                strokeLinecap="round"
                strokeLinejoin="round"
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
          fill={overlay.draft}
          fillOpacity={0.18}
          stroke={overlay.draft}
          strokeWidth={1.5}
          strokeDasharray="5 3"
        />
      )}
      {mode === 'edit' &&
        !activeLocked &&
        activeGlyph &&
        bboxesByKey[activeGlyph] &&
        (() => {
          const b: Rect = edit ? edit.cur : bboxesByKey[activeGlyph];
          const hs = 9 / zoom; // handle half-size in image px (≈18px on screen)
          const mx = (b.x0 + b.x1) / 2;
          const my = (b.y0 + b.y1) / 2;
          const grips: Array<[number, number]> = [
            [b.x0, b.y0],
            [b.x1, b.y0],
            [b.x0, b.y1],
            [b.x1, b.y1],
            [mx, b.y0],
            [mx, b.y1],
            [b.x0, my],
            [b.x1, my],
          ];
          return (
            <g style={{ pointerEvents: 'none' }}>
              <rect
                x={b.x0}
                y={b.y0}
                width={b.x1 - b.x0}
                height={b.y1 - b.y0}
                fill={overlay.active}
                fillOpacity={0.1}
                stroke={overlay.active}
                strokeWidth={2 / zoom}
              />
              {grips.map(([gx, gy], i) => (
                <rect
                  key={i}
                  x={gx - hs}
                  y={gy - hs}
                  width={hs * 2}
                  height={hs * 2}
                  fill={overlay.active}
                  stroke={overlay.gripOutline}
                  strokeWidth={1 / zoom}
                />
              ))}
            </g>
          );
        })()}
    </svg>
  );
}
