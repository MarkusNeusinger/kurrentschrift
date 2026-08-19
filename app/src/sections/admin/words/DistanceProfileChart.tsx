// The Abstandsprofil curve under a word card: x = arc along the stored trace
// (written ink only), y = nearest distance of the engine composition, in xh.
// One series, so the caption is the legend (dataviz: a single series carries
// no legend box); the line wears the engine's own red because colour follows
// the entity, and the hover crosshair reports the value AND pins the probe
// onto the crop above via `onHover` — the mountain in the curve is HERE in
// the word.

import { useState } from 'react';

import { WERKBANK_COLORS } from '@/sections/admin/shell/model';
import { paper } from '@/styles/paper';

import type { DistanceProfile, ProfilePoint } from './distanceProfile';

// Fixed logical size (the duel page's discipline): the card scrolls a too-wide
// chart instead of squeezing its text.
const PLOT_W = 760;
const PLOT_H = 110;
const ML = 40;
const MR = 8;
const MT = 8;
const MB = 24;

// The probe over the crop and the crosshair share one accent that belongs to
// neither ink — matching the duel page's probe, so the gesture reads the same
// on both surfaces.
export const PROBE_COLOR = '#f59e0b';

// The y-axis never collapses below this, so a clean word still shows a scale.
const MIN_YMAX = 0.3;

function gridStep(ymax: number): number {
  if (ymax <= 0.6) return 0.1;
  if (ymax <= 1.2) return 0.2;
  return 0.5;
}

export function DistanceProfileChart({
  profile,
  axisLabel,
  onHover,
}: {
  profile: DistanceProfile;
  axisLabel: string;
  onHover?: (point: ProfilePoint | null) => void;
}) {
  const [cursor, setCursor] = useState<ProfilePoint | null>(null);
  const { points, lifts } = profile;
  if (points.length < 2) return null;

  const arcTotal = points[points.length - 1].arc;
  if (arcTotal <= 0) return null;
  const ymax = Math.max(MIN_YMAX, Math.ceil(profile.max * 10) / 10);
  const sx = (arc: number) => ML + (arc / arcTotal) * PLOT_W;
  const sy = (dist: number) => MT + PLOT_H * (1 - Math.min(dist, ymax) / ymax);
  const width = ML + PLOT_W + MR;
  const height = MT + PLOT_H + MB;

  const yTicks: number[] = [];
  for (let v = 0; v <= ymax + 1e-9; v += gridStep(ymax)) yTicks.push(Number(v.toFixed(2)));
  const xStep = arcTotal <= 12 ? 2 : 5;
  const xTicks: number[] = [];
  for (let a = 0; a <= arcTotal + 1e-9; a += xStep) xTicks.push(a);

  const pick = (clientX: number, rect: DOMRect): ProfilePoint => {
    const arc = Math.max(0, Math.min(arcTotal, ((clientX - rect.left) * (width / rect.width) - ML) / (PLOT_W / arcTotal)));
    let lo = 0;
    let hi = points.length - 1;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (points[mid].arc < arc) lo = mid + 1;
      else hi = mid;
    }
    return points[lo];
  };

  const move = (event: React.PointerEvent<SVGSVGElement>) => {
    const point = pick(event.clientX, event.currentTarget.getBoundingClientRect());
    setCursor(point);
    onHover?.(point);
  };
  const leave = () => {
    setCursor(null);
    onHover?.(null);
  };

  // Tooltip flips to the left of the crosshair near the right edge.
  const tipRight = cursor !== null && sx(cursor.arc) > ML + PLOT_W - 90;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      style={{ display: 'block', background: '#fff', touchAction: 'none' }}
      onPointerMove={move}
      onPointerLeave={leave}
      aria-label={axisLabel}
    >
      <rect x={ML} y={MT} width={PLOT_W} height={PLOT_H} fill="none" stroke={paper.line} />
      {yTicks.map((v) => (
        <g key={`y${v}`}>
          <line x1={ML} x2={ML + PLOT_W} y1={sy(v)} y2={sy(v)} stroke={paper.line} strokeOpacity={0.55} />
          <text x={ML - 5} y={sy(v) + 3.5} textAnchor="end" fontSize={10} fill="#8a8578">
            {v.toFixed(1)}
          </text>
        </g>
      ))}
      {xTicks.map((a) => (
        <g key={`x${a}`}>
          <line x1={sx(a)} x2={sx(a)} y1={MT} y2={MT + PLOT_H} stroke={paper.line} strokeOpacity={0.55} />
          <text x={sx(a)} y={MT + PLOT_H + 12} textAnchor="middle" fontSize={10} fill="#8a8578">
            {a}
          </text>
        </g>
      ))}
      {lifts.map((arc, i) => (
        <line
          key={`l${i}`}
          x1={sx(arc)}
          x2={sx(arc)}
          y1={MT}
          y2={MT + PLOT_H}
          stroke="#b5b0a1"
          strokeDasharray="3 3"
        />
      ))}
      <polyline
        points={points.map((p) => `${sx(p.arc).toFixed(1)},${sy(p.dist).toFixed(1)}`).join(' ')}
        fill="none"
        stroke={WERKBANK_COLORS.engine}
        strokeWidth={1.6}
        strokeLinejoin="round"
      />
      <text x={ML + PLOT_W / 2} y={height - 2} textAnchor="middle" fontSize={10} fill="#8a8578">
        {axisLabel}
      </text>
      {cursor && (
        <g pointerEvents="none">
          <line x1={sx(cursor.arc)} x2={sx(cursor.arc)} y1={MT} y2={MT + PLOT_H} stroke={PROBE_COLOR} />
          <text
            x={sx(cursor.arc) + (tipRight ? -6 : 6)}
            y={MT + 12}
            textAnchor={tipRight ? 'end' : 'start'}
            fontSize={11}
            fill="#4a463c"
          >
            {`${cursor.dist.toFixed(2)} xh`}
          </text>
        </g>
      )}
    </svg>
  );
}
