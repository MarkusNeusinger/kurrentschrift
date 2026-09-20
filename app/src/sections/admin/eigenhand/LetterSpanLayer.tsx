// Die Buchstabengrenzen über der Bahn — which stretch of the line is which
// letter, and where the author may move the seam between two of them.
//
// Drawn in the CROP's pixels (the editor's own viewBox), so it sits in the same
// frame as the picture and needs no second matrix: every point goes through
// `traceToCrop`, the one conversion `belege/registration.ts` owns.
//
// The two hues alternate and mean NOTHING beyond „this is a different letter
// than the one beside it" — the letter itself is written next to each stretch,
// so no reading rides on colour alone (design-system §2). The handle is the
// app's one „active" accent, because that is exactly what it is: the thing
// under the pen.
//
// Non-interactive by construction: the editor's canvas owns every pointer
// (`TraceCanvas` mode `point`), so this layer draws and never listens. Two
// pointer implementations over one surface is how a drag ends up drawing a
// stroke.

import type { EigenhandPfadSpan } from '@/lib/api';
import { traceToCrop, type TracePoint, type TraceRegistration } from '@/sections/admin/belege/registration';
import type { SpanSeam } from '@/sections/admin/eigenhand/letterSpans';
import { SPAN_AUTHORED } from '@/sections/admin/eigenhand/letterSpans';
import { landmarkColors, overlay } from '@/sections/admin/overlayColors';

// Alternating separation hues, both AA on the white work surface and neither
// of them the ink's own near-black.
const SPAN_COLORS = [landmarkColors.crossing, landmarkColors.retrace] as const;

/** Handle radius and label size as fractions of the x-height, so both keep
 * their proportion at every zoom and on every strip. */
const HANDLE_R_XH = 0.16;
const LABEL_XH = 0.55;

export function LetterSpanLayer({
  spans,
  strokes,
  reg,
  seams,
  grabbed,
  labelOf,
}: {
  spans: readonly EigenhandPfadSpan[];
  /** The strokes as they are drawn right now, in trace units. */
  strokes: readonly (readonly TracePoint[])[];
  reg: TraceRegistration;
  seams: readonly SpanSeam[];
  /** Index into `seams` of the boundary under the pen, or null. */
  grabbed: number | null;
  /** The letter a shaped slot stands for — '' where the word cannot say. */
  labelOf: (slot: number) => string;
}) {
  const handleR = HANDLE_R_XH * reg.xh;
  const label = LABEL_XH * reg.xh;
  return (
    <g pointerEvents="none">
      {spans.map((span, index) => {
        const stroke = strokes[span.stroke];
        if (!stroke) return null;
        const points = stroke.slice(span.first, span.last + 1).map((point) => traceToCrop(reg, point));
        if (points.length === 0) return null;
        const color = SPAN_COLORS[index % SPAN_COLORS.length];
        const middle = points[Math.floor(points.length / 2)];
        const text = labelOf(span.slot);
        return (
          <g key={`span-${index}`}>
            <polyline
              points={points.map(([x, y]) => `${x},${y}`).join(' ')}
              fill="none"
              stroke={color}
              strokeOpacity={0.75}
              strokeWidth={4}
              vectorEffect="non-scaling-stroke"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            {text !== '' && (
              // Above the line, in the crop's own y-down frame: the label says
              // WHICH letter a stretch is, which is what makes a boundary
              // correctable rather than a guess about a coloured segment.
              <text
                x={middle[0]}
                y={middle[1] - handleR - label * 0.3}
                fill={color}
                fontSize={label}
                textAnchor="middle"
                dominantBaseline="alphabetic"
              >
                {text}
              </text>
            )}
          </g>
        );
      })}
      {seams.map((seam, index) => {
        const stroke = strokes[seam.stroke];
        const point = stroke?.[seam.sample];
        if (!point) return null;
        const [x, y] = traceToCrop(reg, point);
        const authored = spans[seam.before]?.herkunft === SPAN_AUTHORED;
        return (
          <circle
            key={`seam-${index}`}
            cx={x}
            cy={y}
            r={grabbed === index ? handleR * 1.4 : handleR}
            fill={overlay.active}
            fillOpacity={authored ? 0.95 : 0.6}
            stroke={overlay.gripOutline}
            strokeWidth={1}
            vectorEffect="non-scaling-stroke"
          />
        );
      })}
    </g>
  );
}
