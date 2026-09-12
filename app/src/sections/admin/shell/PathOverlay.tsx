// A stored pen path drawn so that the MOVEMENT is legible — one component for
// both surfaces that have one: the traced words over a plate crop (Wörter) and
// the Streifen-Pfad over an own-hand strip (Eigenhand).
//
// The flat green line the word cards drew until now says only where the ink
// is. What the author asked to see is the path: which stretch came first,
// which way the pen ran, and where it left the paper. So the same stroke list
// is drawn with
//   * a colour ramp in writing order (first stretch → last),
//   * a filled dot where the pen first touched down,
//   * an arrow head at every stretch's end,
//   * a dashed connector for every Absetzer — the thing a single flat colour
//     hides completely, because a lift looks exactly like a corner,
//   * optional per-stretch index numbers.
//
// Everything is drawn in the PATH's own units (baseline 0, midband 1): the
// caller supplies the SVG matrix, which is the same `traceMatrix` the word
// cards already use, so this component knows nothing about pixels. `unit` is
// one display pixel expressed in those units — it keeps hairlines and arrow
// heads the same visual size across crops of very different resolutions.
//
// With every decoration off it draws exactly the line it replaced, which is
// what lets the „Spur" layer stay what it was and „Pfad" be a layer on top.

import { WERKBANK_COLORS } from '@/sections/admin/shell/model';
import {
  arrowPoints,
  labelPointOf,
  liftsOf,
  orderColors,
  startPointOf,
  strokePathD,
  tipOf,
  type Stroke,
} from '@/sections/admin/shell/pathOverlay';

// ~2/3 of a hairline stroke's own width: thick enough to read over black ink,
// thin enough that the ink it follows still shows on both sides of it. In PATH
// units, so the line is the same fraction of an x-height on every surface.
const LINE_WIDTH = 0.11;

// The decorations are measured against that LINE, not against a display pixel
// — that is the one sizing mistake this overlay invites. A word card draws the
// path at x-height 29 viewBox px, so the line is 3.2 px wide there and a 7 px
// arrow head sits entirely INSIDE it (measured on `Säbel`, 2026-09-12: the
// triangles were in the DOM and invisible on screen, and the lift dashes at
// 0.7 px on/off read as a solid line). As multiples of the line width they
// stay in proportion at every x-height and every zoom.
const ARROW_LEN = 2.4 * LINE_WIDTH; // length of the direction triangle
const ARROW_SPREAD = 0.8; // its base width, as a fraction of the length
const START_DOT_R = 1.3 * LINE_WIDTH;
const LIFT_WIDTH = 0.5 * LINE_WIDTH;
const LIFT_DASH = 2 * LINE_WIDTH;
// The floor is the other half: where the whole path is only a few pixels tall
// (a strip at ¼ zoom) the proportional size would fall under one pixel.
const ARROW_MIN_PX = 6;
const DOT_MIN_PX = 2.5;
const DASH_MIN_PX = 3;
// The index label is the one thing that is NOT proportional: a number is
// readable or it is not, and that is a question of screen pixels.
const LABEL_PX = 9;

interface Props {
  strokes: Stroke[];
  // One display pixel in path units — see the module comment.
  unit: number;
  // Off: the plain line in `color` (what the word card drew before). On: the
  // order ramp, the start dot, the direction arrows and the lift dashes.
  detail?: boolean;
  // The flat colour, used when `detail` is off and as the ramp's first stretch.
  color?: string;
  opacity?: number;
  // Number every pen-down stretch. Exact but busy — off unless asked for.
  showIndex?: boolean;
}

export function PathOverlay({
  strokes,
  unit,
  detail = false,
  color = WERKBANK_COLORS.traceOverInk,
  opacity = 0.95,
  showIndex = false,
}: Props) {
  const drawn = strokes.filter((stroke) => stroke.length > 1);
  const colors = detail ? orderColors(drawn.length, color, WERKBANK_COLORS.pathLast) : [];
  const lifts = detail ? liftsOf(strokes) : [];
  const start = detail ? startPointOf(strokes) : null;
  const width = LINE_WIDTH;
  const arrow = Math.max(ARROW_LEN, ARROW_MIN_PX * unit);
  const dotR = Math.max(START_DOT_R, DOT_MIN_PX * unit);
  const dash = Math.max(LIFT_DASH, DASH_MIN_PX * unit);

  return (
    <>
      {/* The lifts go UNDER the strokes: an Absetzer is what happened between
          two stretches, and it must never look like ink of its own. */}
      {lifts.map((lift, i) => (
        <line
          key={`lift-${i}`}
          x1={lift.from[0]}
          y1={lift.from[1]}
          x2={lift.to[0]}
          y2={lift.to[1]}
          stroke={WERKBANK_COLORS.lift}
          strokeOpacity={0.75}
          strokeWidth={LIFT_WIDTH}
          strokeDasharray={`${dash} ${dash}`}
          strokeLinecap="butt"
        />
      ))}
      {drawn.map((stroke, i) => {
        const tint = detail ? colors[i] : color;
        const tip = detail ? tipOf(stroke) : null;
        const head = tip ? arrowPoints(tip, arrow, ARROW_SPREAD) : null;
        const label = showIndex ? labelPointOf(stroke, LABEL_PX * unit) : null;
        return (
          <g key={`stroke-${i}`}>
            <path
              d={strokePathD(stroke)}
              fill="none"
              stroke={tint}
              strokeOpacity={opacity}
              strokeWidth={width}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            {head && <polygon points={head} fill={tint} fillOpacity={opacity} />}
            {label && (
              <text
                x={label[0]}
                y={label[1]}
                fill={tint}
                fillOpacity={opacity}
                fontSize={LABEL_PX * unit}
                textAnchor="middle"
                dominantBaseline="middle"
                // The enclosing <g> flips y (units grow upwards) — without
                // undoing it for the glyph itself every number stands on its head.
                transform={`translate(${label[0]} ${label[1]}) scale(1 -1) translate(${-label[0]} ${-label[1]})`}
              >
                {i + 1}
              </text>
            )}
          </g>
        );
      })}
      {start && (
        <circle cx={start[0]} cy={start[1]} r={dotR} fill={colors[0] ?? color} fillOpacity={opacity} />
      )}
    </>
  );
}
