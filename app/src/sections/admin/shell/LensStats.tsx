// The statistics layers of the Handmodell (Stufenplan H1/H2) as the Werkbank's
// context lenses show them — the "Stufen-Einsicht". Under a LETTER: the stored
// aggregate of the hand, i.e. the per-anchor median (the Laufform's source)
// with its MAD spread plus the pooled layer-1 numbers. Under a JOIN: the
// measured median connector drawn over every occurrence it was condensed from,
// beside the dissection QC — `gen_chamfer` being the audit number this layer
// exists for („gemessen vs. komponiert").
//
// Strictly an inspection surface (optimierungs-werkbank.md §3): a generated
// stage is DISPLAYED and complained about here, never edited. The per-layer
// rebuild is offered because it only recomputes statistics; the
// rendering-changing `apply-laufform` step deliberately has no button.
//
// Everything drawn is drawn honestly: an absent measurement is never printed as
// a measured zero, occurrences the rebuild itself skipped are not drawn into
// the sketch they never fed, and both blocks name the hand the numbers belong
// to (plus a warning when the loaded occurrences name more than one).

import RefreshIcon from '@mui/icons-material/Refresh';
import { Box, Chip, CircularProgress, IconButton, Tooltip, Typography } from '@mui/material';
import { useState } from 'react';

import type { AggregateOut, InstanceOut, PairAggregateOut, PairInstanceOut } from '@/lib/api';
import { de, fmt, specimenKindLabel } from '@/locales/admin';
import { paper } from '@/styles/paper';

import { WERKBANK_COLORS } from './model';

// Same height as the chart-crop thumbnail the old lens showed above it.
const SKETCH_H = 90;
// The letter sketch gets more room since it also carries the occurrence
// chains: one outlier occurrence (a tail pulled up to ~1.6 x-heights happens)
// legitimately stretches the frame, and the median must stay legible when it
// does — the alternative, clipping the outlier, would hide exactly the thing
// the layer is there to reveal.
const SKETCH_H_LETTER = 150;
// Template units of air around the drawn geometry.
const SKETCH_PAD = 0.3;

// The white work surface a sketch is drawn on — same framing as the chart crop
// above it in the letter lens.
const SKETCH_FRAME = {
  bgcolor: '#fff',
  borderRadius: 1,
  border: 1,
  borderColor: 'divider',
  p: 0.5,
  width: 'fit-content',
} as const;

// Why the block can have nothing to show: the lists are still in flight, the
// occurrences name no hand at all, or the admin-gated read failed.
export type StatsStatus = 'loading' | 'ready' | 'unavailable' | 'no-hand';

// Where a block's numbers come from, so it can say so instead of implying a
// hand: `handId` is derived from the loaded occurrences (never a constant),
// `handsMixed` flags that they do not all name the same one, and `layerEmpty`
// separates "this hand was never rebuilt" from "this key stayed below the
// minimum" when there is no row for the selection.
export interface StatsContext {
  status: StatsStatus;
  handId: string | null;
  handsMixed: boolean;
  layerEmpty: boolean;
}

// A rebuild returns the caption the block prints ("123 Paare aus 218
// Vorkommen, 14 übersprungen"); undefined = no hand, so no rebuild is possible.
export type RebuildFn = () => Promise<string>;

const num = (value: number, digits: number): string => value.toFixed(digits);

// „1 Vorlage" vs „2 Vorlagen" — the one count in these blocks whose German
// noun actually inflects („Vorkommen" is invariant, so it needs no twin).
const specimenCount = (count: number): string =>
  fmt(count === 1 ? de.admin.werkbank.statsSpecimensOne : de.admin.werkbank.statsSpecimens, { count });

// A wire point is only usable once it really is a finite 2-vector — the rows
// come from JSONB, so length and finiteness are worth asserting before any
// bounds math turns a NaN into an invisible sketch. The offset's MAD goes
// through the SAME check: a spread is a 2-vector too, and a NaN in it would
// reach `toFixed` (or a whisker's coordinates) just as easily.
const isPoint = (p: unknown): p is number[] =>
  Array.isArray(p) && p.length >= 2 && Number.isFinite(p[0]) && Number.isFinite(p[1]);

// Bounds of a point cloud in template units, padded, plus the y values that
// must stay visible (baseline/midband) whatever the geometry does.
function boundsOf(points: number[][], extraY: number[]): { minX: number; minY: number; w: number; h: number } {
  const xs = points.map(([x]) => x);
  const ys = [...points.map(([, y]) => y), ...extraY];
  const minX = Math.min(...xs) - SKETCH_PAD;
  const maxX = Math.max(...xs) + SKETCH_PAD;
  const minY = Math.min(...ys) - SKETCH_PAD;
  const maxY = Math.max(...ys) + SKETCH_PAD;
  // Guard against a degenerate cloud (a single anchor, a flat connector):
  // a zero extent would make the viewBox — and every derived stroke width —
  // collapse.
  const w = Math.max(maxX - minX, 0.2);
  const h = Math.max(maxY - minY, 0.2);
  return { minX, minY, w, h };
}

// Template units are y-UP (baseline = 0, midband = 1), SVG is y-down: drawing
// every point mirrored keeps the viewBox a plain rectangle.
const pathOf = (points: number[][]): string =>
  points.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x},${-y}`).join(' ');

// Header of one statistics block: the label plus the quiet per-layer rebuild.
// Mounted under a key that changes with the selection, so a stale result
// caption never sits under a different letter.
function StatsHeader({
  label,
  warning,
  onRebuild,
}: {
  label: string;
  warning?: string | null;
  onRebuild?: RebuildFn;
}) {
  const t = de.admin.werkbank;
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const run = () => {
    if (!onRebuild) return;
    setBusy(true);
    setResult(null);
    onRebuild()
      .then(setResult)
      .catch(() => setResult(t.statsRebuildFailed))
      .finally(() => setBusy(false));
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, flexWrap: 'wrap' }}>
      <Typography variant="caption" color="text.secondary" sx={{ flex: 1, minWidth: 0 }}>
        {label}
      </Typography>
      {onRebuild && (
        <Tooltip title={t.statsRebuild}>
          {/* A disabled button swallows the tooltip's own events — the span
              keeps the hint readable while a rebuild runs. */}
          <span>
            <IconButton size="small" aria-label={t.statsRebuild} disabled={busy} onClick={run}>
              {busy ? <CircularProgress size={14} /> : <RefreshIcon fontSize="small" />}
            </IconButton>
          </span>
        </Tooltip>
      )}
      {warning && (
        <Typography variant="caption" color="text.secondary" sx={{ width: '100%' }}>
          {warning}
        </Typography>
      )}
      {result && (
        <Typography variant="caption" color="text.disabled" sx={{ width: '100%' }}>
          {result}
        </Typography>
      )}
    </Box>
  );
}

// A block never leaves the hand implicit: the numbers of one writer over
// another writer's occurrences would look exactly the same otherwise. Since
// the redesign the surrounding Panel already carries the block's title, so the
// header shrinks to the part the title does NOT say — which hand these numbers
// belong to.
const headingFor = (heading: string, handId: string | null): string =>
  handId ? fmt(de.admin.werkbank.statsHand, { hand: handId }) : heading;

// The one quiet warning line: the occurrences do not all name the same hand
// (e.g. once the Abb.-22 Schülerhand is harvested under its own id), so say
// WHICH hand's medians are on screen instead of mixing silently.
const mixedHandsWarning = (stats: StatsContext): string | null =>
  stats.handsMixed && stats.handId ? fmt(de.admin.werkbank.statsMixedHands, { hand: stats.handId }) : null;

// The status cases share one quiet line — nothing to inspect is not an error.
function statusCaption(status: StatsStatus): string | null {
  const t = de.admin.werkbank;
  if (status === 'loading') return t.statsLoading;
  if (status === 'no-hand') return t.statsNoHand;
  if (status === 'unavailable') return t.statsUnavailable;
  return null;
}

function QuietCaption({ text }: { text: string }) {
  return (
    <Typography variant="caption" color="text.disabled" sx={{ display: 'block' }}>
      {text}
    </Typography>
  );
}

// One median anchor together with the spread that belongs to IT.
interface SketchAnchor {
  x: number;
  y: number;
  // Mean of the two axes' MAD, template units; undefined where the aggregate
  // carries none (an absent spread is not a zero spread).
  mad?: number;
}

// Anchors zipped with `hull.anchor_mad` BEFORE any validity filtering: the MAD
// list is positional, so a dropped anchor has to take its own circle with it —
// indexing the spread with the FILTERED index slides every circle one anchor
// along.
function letterSketchAnchors(aggregate: AggregateOut): SketchAnchor[] {
  const mad = aggregate.hull.anchor_mad ?? [];
  return (aggregate.cluster_center ?? [])
    .map((point, i) => ({ point, spread: mad[i] }))
    .filter(({ point }) => isPoint(point))
    .map(({ point, spread }) => {
      const r = isPoint(spread) ? (spread[0] + spread[1]) / 2 : 0;
      return { x: point[0], y: point[1], mad: r > 0 ? r : undefined };
    });
}

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
function AggregateSketch({
  anchors,
  glyphKey,
  occurrences,
  laufform,
}: {
  anchors: SketchAnchor[];
  glyphKey: string;
  occurrences: number[][][];
  // The RENDERED running form (template variant 100), drawn dashed against the
  // median that would replace it. This is the whole "see the difference before
  // you overwrite it" view: two chains in one frame, no registration needed
  // because both live in the chart row's coordinates.
  laufform: number[][];
}) {
  const t = de.admin.werkbank;
  const points = anchors.map((a) => [a.x, a.y]);

  // The occurrence chains stretch the bounds too — clipping them would make
  // the spread look tighter than it is.
  const { minX, minY, w, h } = boundsOf([...points, ...occurrences.flat(), ...laufform], [0, 1]);
  const width = Math.max(24, (w / h) * SKETCH_H_LETTER);
  // One display pixel in template units — hairlines and dots stay the same
  // visual size across glyphs of very different extent.
  const u = h / SKETCH_H_LETTER;

  return (
    <svg
      width={width}
      height={SKETCH_H_LETTER}
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

export function LetterStats({
  glyphKey,
  aggregate,
  occurrences = [],
  stats,
  onRebuild,
}: {
  glyphKey: string;
  aggregate?: AggregateOut;
  // The stored occurrences of THIS glyph, drawn thin behind the median so the
  // spread is visible as a shape and not only as a MAD radius.
  occurrences?: InstanceOut[];
  stats: StatsContext;
  onRebuild?: RebuildFn;
}) {
  const t = de.admin.werkbank;
  const caption = statusCaption(stats.status);
  if (caption) return <QuietCaption text={caption} />;

  const meanStats = aggregate?.mean_stats ?? {};
  const rmse = meanStats.geo_rmse_px;
  const positions = Object.entries(meanStats.positions ?? {});
  const anchors = aggregate ? letterSketchAnchors(aggregate) : [];
  // Same validity rule as the median's own anchors — a JSONB row can carry
  // anything, and a NaN would silently blank the whole sketch.
  const occurrenceChains = occurrences
    .map((inst) => (inst.anchors ?? []).filter(isPoint))
    .filter((line) => line.length >= 2);
  // The rendered running form and its distance to the median. `dev === 0` is a
  // real answer ("what is written IS the median"), so the null check has to be
  // explicit — a falsy test would report a fresh Laufform as unknown.
  const laufform = (aggregate?.laufform_anchors ?? []).filter(isPoint);
  const dev = aggregate?.laufform_dev_xh ?? null;
  const freshness =
    aggregate == null
      ? null
      : dev === null
        ? laufform.length === 0
          ? { text: t.laufformNone, stale: false }
          : { text: t.laufformIncomparable, stale: false }
        : dev === 0
          ? { text: t.laufformCurrent, stale: false }
          : { text: fmt(t.laufformStale, { value: num(dev, 3) }), stale: true };

  return (
    <Box>
      <StatsHeader
        label={headingFor(t.statsLetterHeading, stats.handId)}
        warning={mixedHandsWarning(stats)}
        onRebuild={onRebuild}
      />
      {!aggregate ? (
        // Two different silences: the hand has no aggregates at all (the
        // rebuild button right above is the answer), or it has them and this
        // key stayed below the minimum occurrence count.
        <QuietCaption text={stats.layerEmpty ? t.statsNoRebuild : t.statsNoneLetter} />
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75, mt: 0.5 }}>
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            <Chip size="small" variant="outlined" label={fmt(t.statsInstances, { count: aggregate.n_instances })} />
            {meanStats.n_specimens !== undefined && (
              <Chip size="small" variant="outlined" label={specimenCount(meanStats.n_specimens)} />
            )}
            {rmse && (
              <Chip
                size="small"
                variant="outlined"
                label={fmt(t.statsRmse, { mean: num(rmse.mean, 2), max: num(rmse.max, 2) })}
              />
            )}
            {meanStats.xh_px_mean !== undefined && (
              <Chip size="small" variant="outlined" label={fmt(t.statsXh, { value: num(meanStats.xh_px_mean, 1) })} />
            )}
          </Box>
          {positions.length > 0 && (
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', alignItems: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                {`${t.statsPositionsLabel}:`}
              </Typography>
              {/* initial/medial/final are the documented termini technici of
                  the shaping layer and stay untranslated on purpose. */}
              {positions.map(([position, count]) => (
                <Chip key={position} size="small" variant="outlined" label={`${position} ${count}`} />
              ))}
            </Box>
          )}
          {/* Frame, sketch and legend appear together or not at all — a
              bordered empty box with a legend under it promises a drawing that
              is not there. */}
          {/* Freshness: is what the engine writes still what the statistics
              say? Read straight off the row (no rebuild needed to find out). */}
          {freshness && (
            <Chip
              size="small"
              variant="outlined"
              color={freshness.stale ? 'warning' : 'default'}
              label={freshness.text}
              sx={{ alignSelf: 'flex-start' }}
            />
          )}
          {anchors.length >= 2 && (
            <Box>
              <Box sx={SKETCH_FRAME}>
                <AggregateSketch
                  anchors={anchors}
                  glyphKey={glyphKey}
                  occurrences={occurrenceChains}
                  laufform={laufform}
                />
              </Box>
              <Typography variant="caption" color="text.disabled" sx={{ display: 'block' }}>
                {`${t.statsLetterSketch} — ${
                  occurrenceChains.length > 0 ? t.statsLetterSketchLegendWithOcc : t.statsLetterSketchLegend
                }${laufform.length >= 2 ? ` · ${t.statsLetterSketchLegendLaufform}` : ''}`}
              </Typography>
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
}

// Median transition over its occurrences. Everything drawn here lives in the
// SAME frame (template units relative to the left glyph's exit, baseline-
// locked, y up), so no registration is needed — and no `/write/word` overlay is
// attempted: the composed word lives in a different frame, so the comparison
// stays deliberately side-by-side (numbers, not a false superposition).
// The caller prepares median + occurrences (and owns the frame).
function PairConnectorSketch({
  aggregate,
  median,
  occurrences,
}: {
  aggregate: PairAggregateOut;
  median: number[][];
  occurrences: PairInstanceOut[];
}) {
  const t = de.admin.werkbank;
  const lines = occurrences
    .map((occ) => (occ.geometry?.connector ?? []).filter(isPoint))
    .filter((line) => line.length >= 2);
  const offset = aggregate.offset_center ?? [];
  const offsetMad = aggregate.hull.offset_mad;
  const hasOffset = isPoint(offset);

  // The origin is the left glyph's exit — always in view, it is the reference
  // everything else is measured from.
  const cloud = [[0, 0], ...median, ...lines.flat()];
  if (hasOffset) cloud.push(offset);
  const { minX, minY, w, h } = boundsOf(cloud, [0]);
  const width = Math.max(24, (w / h) * SKETCH_H);
  const u = h / SKETCH_H;

  return (
    <svg
      width={width}
      height={SKETCH_H}
      viewBox={`${minX} ${-(minY + h)} ${w} ${h}`}
      role="img"
      aria-label={fmt(t.statsPairSketchAria, { left: aggregate.left_key, right: aggregate.right_key })}
      style={{ display: 'block', background: '#fff', maxWidth: '100%', height: 'auto' }}
    >
      {/* y = 0 is the left glyph's exit height, not the writing baseline —
          the frame is baseline-locked, so it is the one honest reference line
          this sketch can draw. */}
      <line x1={minX} x2={minX + w} y1={0} y2={0} stroke={paper.sepiaFaint} strokeWidth={u} />
      {lines.map((line, i) => (
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
      <path
        d={pathOf(median)}
        fill="none"
        stroke={WERKBANK_COLORS.trace}
        strokeWidth={2 * u}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {hasOffset && isPoint(offsetMad) && (
        <g stroke={WERKBANK_COLORS.trace} strokeWidth={u} strokeOpacity={0.6}>
          <line x1={offset[0] - offsetMad[0]} x2={offset[0] + offsetMad[0]} y1={-offset[1]} y2={-offset[1]} />
          <line x1={offset[0]} x2={offset[0]} y1={-(offset[1] - offsetMad[1])} y2={-(offset[1] + offsetMad[1])} />
        </g>
      )}
      {hasOffset && <circle cx={offset[0]} cy={-offset[1]} r={2.2 * u} fill={WERKBANK_COLORS.trace} />}
    </svg>
  );
}

export function PairStats({
  aggregate,
  occurrences,
  stats,
  onRebuild,
}: {
  aggregate?: PairAggregateOut;
  occurrences: PairInstanceOut[];
  stats: StatsContext;
  onRebuild?: RebuildFn;
}) {
  const t = de.admin.werkbank;
  const caption = statusCaption(stats.status);
  if (caption) return <QuietCaption text={caption} />;

  const meanStats = aggregate?.mean_stats ?? {};
  const offset = aggregate?.offset_center;
  const offsetMad = aggregate?.hull.offset_mad;
  const kinds = Object.entries(meanStats.kinds ?? {});
  const median = (aggregate?.connector_center ?? []).filter(isPoint);
  // The rebuild skips a dissection whose letter fits were not clean (`fit_bad`)
  // — those occurrences never fed this median, and drawing them anyway stretches
  // the bounds and squashes exactly the geometry the sketch is about. They stay
  // in the occurrence LIST below, where their „Fit unsicher" flag is the point.
  const drawable = occurrences.filter((occ) => occ.measurements.fit_ok !== false);
  const hidden = occurrences.length - drawable.length;

  // Read in the order the doctrine triages: how far off the GENERATOR is
  // first, then how well the measurement itself stands.
  const numbers: string[] = [];
  if (aggregate) numbers.push(fmt(t.statsInstances, { count: aggregate.n_instances }));
  if (meanStats.n_specimens !== undefined) numbers.push(specimenCount(meanStats.n_specimens));
  if (meanStats.gen_chamfer) {
    numbers.push(
      fmt(t.statsGenChamfer, { mean: num(meanStats.gen_chamfer.mean, 3), max: num(meanStats.gen_chamfer.max, 3) }),
    );
  }
  if (meanStats.harvest_chamfer) {
    numbers.push(fmt(t.statsHarvestChamfer, { value: num(meanStats.harvest_chamfer.mean, 3) }));
  }
  if (meanStats.resid) {
    numbers.push(fmt(t.statsResid, { mean: num(meanStats.resid.mean, 3), max: num(meanStats.resid.max, 3) }));
  }
  if (meanStats.gap_ink_share !== undefined) {
    numbers.push(fmt(t.statsGapInk, { value: num(meanStats.gap_ink_share, 2) }));
  }
  if (isPoint(offset)) {
    // Without a stored MAD the ± clause is dropped entirely: an absent spread
    // printed as „± 0,00" would claim a measurement nobody made.
    numbers.push(
      isPoint(offsetMad)
        ? fmt(t.statsOffset, {
            x: num(offset[0], 2),
            y: num(offset[1], 2),
            madX: num(offsetMad[0], 2),
            madY: num(offsetMad[1], 2),
          })
        : fmt(t.statsOffsetNoMad, { x: num(offset[0], 2), y: num(offset[1], 2) }),
    );
  }

  return (
    <Box>
      <StatsHeader
        label={headingFor(t.statsPairHeading, stats.handId)}
        warning={mixedHandsWarning(stats)}
        onRebuild={onRebuild}
      />
      {!aggregate ? (
        <QuietCaption text={stats.layerEmpty ? t.statsNoRebuild : t.statsNonePair} />
      ) : (
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'flex-start', mt: 0.5 }}>
          {/* Frame, sketch and legend appear together or not at all. */}
          {median.length >= 2 && (
            <Box>
              <Box sx={SKETCH_FRAME}>
                <PairConnectorSketch aggregate={aggregate} median={median} occurrences={drawable} />
              </Box>
              <Typography variant="caption" color="text.disabled" sx={{ display: 'block' }}>
                {hidden > 0
                  ? `${t.statsPairSketchLegend} · ${fmt(t.statsPairSketchHidden, { count: hidden })}`
                  : t.statsPairSketchLegend}
              </Typography>
            </Box>
          )}
          <Box sx={{ flex: 1, minWidth: 160 }}>
            {numbers.map((line) => (
              <Typography key={line} variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                {line}
              </Typography>
            ))}
            {kinds.length > 0 && (
              <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', alignItems: 'center', mt: 0.25 }}>
                <Typography variant="caption" color="text.secondary">
                  {`${t.statsKindsLabel}:`}
                </Typography>
                {kinds.map(([kind, count]) => (
                  <Chip key={kind} size="small" variant="outlined" label={`${specimenKindLabel(kind)} ${count}`} />
                ))}
              </Box>
            )}
            <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mt: 0.25 }}>
              {t.statsPairReadOnly}
            </Typography>
          </Box>
        </Box>
      )}
    </Box>
  );
}
