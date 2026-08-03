// The aggregate median as a shape: the anchor chain with a dot per anchor and
// a light circle of its MAD spread, over the baseline/midband hairlines — and
// behind it every occurrence the median was condensed from, drawn thin. That
// last layer is what answers "are the occurrences alike at all?" by eye: the
// MAD circles give the number, the bundle of chains gives the shape of the
// spread (a fat circle from two outliers reads very differently from one from
// an evenly scattered set). Same frame for both, because occurrence anchors
// are stored CENTERED, exactly like the median.
//
// Not a rendering of the letter — the ductus prior's widths and stroke topology
// stay with the chart row; this is the geometry the Laufform is derived FROM.
// The caller guarantees at least two anchors (it also owns the frame).
//
// Its own file since the letters overview draws the same sketch small, beside
// the three rendered faces: every stroke width and radius is a multiple of one
// display pixel expressed in template units, so the whole drawing survives
// being handed a different `height` without any other change.

import { de, fmt } from '@/locales/admin';
import { paper } from '@/styles/paper';

import { WERKBANK_COLORS } from './model';
import { boundsOf, pathOf, type SketchAnchor } from './sketchGeometry';

// The letter sketch gets this much room by default since it also carries the
// occurrence chains: one outlier occurrence (a tail pulled up to ~1.6
// x-heights happens) legitimately stretches the frame, and the median must stay
// legible when it does — the alternative, clipping the outlier, would hide
// exactly the thing the layer is there to reveal.
export const SKETCH_H_LETTER = 150;

export function AggregateSketch({
  anchors,
  glyphKey,
  occurrences,
  laufform,
  height = SKETCH_H_LETTER,
}: {
  anchors: SketchAnchor[];
  glyphKey: string;
  occurrences: number[][][];
  // The RENDERED running form (template variant 100), drawn dashed against the
  // median that would replace it. This is the whole "see the difference before
  // you overwrite it" view: two chains in one frame, no registration needed
  // because both live in the chart row's coordinates.
  laufform: number[][];
  height?: number;
}) {
  const t = de.admin.werkbank;
  const points = anchors.map((a) => [a.x, a.y]);

  // The occurrence chains stretch the bounds too — clipping them would make
  // the spread look tighter than it is.
  const { minX, minY, w, h } = boundsOf([...points, ...occurrences.flat(), ...laufform], [0, 1]);
  const width = Math.max(24, (w / h) * height);
  // One display pixel in template units — hairlines and dots stay the same
  // visual size across glyphs of very different extent AND across sketch sizes.
  const u = h / height;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`${minX} ${-(minY + h)} ${w} ${h}`}
      role="img"
      aria-label={fmt(t.statsLetterSketchAria, { key: glyphKey })}
      style={{ display: 'block', background: '#fff', maxWidth: '100%', height: 'auto' }}
    >
      <line x1={minX} x2={minX + w} y1={0} y2={0} stroke={paper.sepiaFaint} strokeWidth={u} />
      <line
        x1={minX}
        x2={minX + w}
        y1={-1}
        y2={-1}
        stroke={paper.sepiaFaint}
        strokeWidth={u}
        strokeDasharray={`${4 * u} ${4 * u}`}
      />
      {/* Occurrences first: they are the ground the median sits on. */}
      {occurrences.map((line, i) => (
        <path
          key={`occ-${i}`}
          d={pathOf(line)}
          fill="none"
          stroke={paper.line}
          strokeWidth={u}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ))}
      {anchors.map((a, i) =>
        a.mad === undefined ? null : (
          <circle key={`mad-${i}`} cx={a.x} cy={-a.y} r={a.mad} fill={paper.line} fillOpacity={0.35} />
        ),
      )}
      {/* What is written TODAY, dashed and in the warning tone — under the
          median so the median stays the figure and this stays the reference. */}
      {laufform.length >= 2 && (
        <path
          d={pathOf(laufform)}
          fill="none"
          stroke={WERKBANK_COLORS.selected}
          strokeOpacity={0.75}
          strokeWidth={1.4 * u}
          strokeDasharray={`${4 * u} ${3 * u}`}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      )}
      <path
        d={pathOf(points)}
        fill="none"
        stroke={WERKBANK_COLORS.trace}
        strokeWidth={1.6 * u}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {anchors.map((a, i) => (
        <circle key={`anchor-${i}`} cx={a.x} cy={-a.y} r={1.6 * u} fill={WERKBANK_COLORS.trace} />
      ))}
    </svg>
  );
}
