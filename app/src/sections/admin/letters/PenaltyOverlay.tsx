// The Abzugs-Linse's drawing half: every located deduction of ONE letter,
// drawn over its Tafel-Ausschnitt in the crop's own pixels
// (optimierungs-werkbank.md §9).
//
// The frame is the CROP, not the written form, and that is a decision rather
// than a convenience (author decision 2026-09-23): the ruler measured the
// stored centreline against the binarized crop, while the Gleichzug renderer
// widens round bodies at render time — a mark drawn on the written a/e/o/u
// would sit beside the ink that was scored. So this is the Diagnose skeleton
// column's pattern (`diagnostics/DiagnosticView.tsx`): an absolutely placed
// `<svg viewBox="0 0 W H">` over the `<img>` of the same crop.
//
// Coordinates: the payload's crop pixels, the pixel in column c and row r
// centred on (c, r). The image draws pixel c over [c, c + 1], so every POINT
// is shifted by half a pixel (the `translate(0.5 0.5)` group) while a cell run
// `[x, y, w]` is the rect (x, y, w, 1) as it stands.
//
// Sizes are in SCREEN pixels, converted per render (`u` = crop px per screen
// px): a crop is drawn two to five times its size, and a mark or a touch
// target has to be the same on a small `i` as on a wide `M`.
//
// Everything here is POINTER SUGAR and says so to assistive tech: the same
// sites are a keyboard list beside the image (the pins and „Alle Stellen"),
// which is where a screen reader and the Tab key select them. A tap on a mark
// selects the same site in that list — the selection is one state, shown twice.

import { useId, useMemo } from 'react';

import type { PenaltyCategoryKey, PenaltyCategoryOut, PenaltyPathOut, PenaltySiteOut, PenaltySitesOut } from '@/lib/api';
import {
  isDrawn,
  isLocated,
  isPixelShape,
  magnitude,
  markWidth,
  maxPoints,
  PENALTY_CATEGORIES,
  placePins,
  siteKey,
  siteShape,
  verticalExaggeration,
  zoneRim,
  type MarkerShape,
} from '@/sections/admin/letters/penaltyLens';
import { garamond, penalty, strokeStyle, type StrokeStyle } from '@/styles/paper';

// Half of the 44 px touch floor (design-system.md §9.3), in screen pixels.
const HIT_RADIUS = 22;
// Screen-pixel geometry of the marks.
const SQUARE_HALF = 5;
const RING_R = 8;
const THIN = 1.25;
const PIN_R = 11;
const PIN_OFFSET = 20;
const PIN_FONT = 14; // the caption floor (design-system.md §9)
const SELECT_RING = 15;
const PATTERN = 6;

type Data = Required<Pick<PenaltySitesOut, 'pins'>> & {
  frame: NonNullable<PenaltySitesOut['frame']>;
  centerline: NonNullable<PenaltySitesOut['centerline']>;
  sites: NonNullable<PenaltySitesOut['sites']>;
};

export interface PenaltyOverlayProps {
  data: Data;
  /** Screen pixels per crop pixel. */
  scale: number;
  hidden: ReadonlySet<PenaltyCategoryKey>;
  selectedKey: string | null;
  onSelect: (category: PenaltyCategoryKey, index: number) => void;
}

type Located = { category: PenaltyCategoryKey; site: PenaltySiteOut & { x: number; y: number }; t: number };

export function PenaltyOverlay({ data, scale, hidden, selectedKey, onSelect }: PenaltyOverlayProps) {
  const u = 1 / scale;
  const ids = useId().replace(/[^a-zA-Z0-9_-]/g, '');
  const { frame, sites, centerline } = data;

  // What is drawn: the located sites that carry a part of their number. A site
  // apportioned 0.0000 adds nothing to the four places shown, and on a letter
  // like `M` there are dozens of them along the edge — the list counts them
  // („nicht gezeichnet") instead of the image burying the ones that matter.
  const located = useMemo(() => {
    const max = maxPoints(sites);
    const out: Located[] = [];
    for (const category of PENALTY_CATEGORIES) {
      for (const site of sites[category].sites) {
        if (isLocated(site) && isDrawn(site)) out.push({ category, site, t: magnitude(site.points_est, max) });
      }
    }
    return out;
  }, [sites]);

  // The Glätte band is as wide as each sample's share of the jerk, on ONE scale
  // for the whole letter so two segments compare.
  const bandMax = useMemo(() => {
    let max = 0;
    for (const site of sites.smoothness.sites) for (const path of site.paths) for (const v of path.values) max = Math.max(max, v);
    return max;
  }, [sites]);

  const shown = located.filter((entry) => !hidden.has(entry.category));
  const selected = located.find((entry) => siteKey(entry.category, entry.site.index) === selectedKey) ?? null;
  // Costliest last, so where two touch targets overlap the bigger deduction wins the tap.
  const hitOrder = [...shown].sort((a, b) => a.site.points_est - b.site.points_est);

  const drawSite = (entry: Located, emphasis: boolean) => (
    <SiteMark
      key={`${emphasis ? 'sel' : 'mark'}-${siteKey(entry.category, entry.site.index)}`}
      shape={siteShape(entry.category, entry.site)}
      site={entry.site}
      t={entry.t}
      emphasis={emphasis}
      patternId={(kind) => `url(#${ids}-${kind}-${emphasis ? 'selected' : 'mark'})`}
      u={u}
      bandMax={bandMax}
      unitPx={frame.unit_px}
    />
  );

  // Pixel marks (cells and edge dots) are areas and go first, under every
  // line, in the crop's own pixel grid; the band goes next and the centreline
  // over it, so the line the ruler measured stays readable through the heat it
  // carries.
  const cellFirst = isPixelShape;

  return (
    <svg
      width={frame.width * scale}
      height={frame.height * scale}
      viewBox={`0 0 ${frame.width} ${frame.height}`}
      style={{ position: 'absolute', inset: 0, overflow: 'visible' }}
      aria-hidden="true"
    >
      <defs>
        {(['mark', 'selected'] as const).map((colour) => {
          const stroke = penalty[colour];
          const size = PATTERN * u;
          return (
            <g key={colour}>
              <pattern id={`${ids}-hatch-${colour}`} patternUnits="userSpaceOnUse" width={size} height={size}>
                <path d={`M0,${size} L${size},0`} stroke={stroke} strokeWidth={1.25 * u} />
              </pattern>
              <pattern id={`${ids}-cross-${colour}`} patternUnits="userSpaceOnUse" width={size} height={size}>
                <path d={`M0,${size} L${size},0 M0,0 L${size},${size}`} stroke={stroke} strokeWidth={1 * u} />
              </pattern>
              <pattern id={`${ids}-stipple-${colour}`} patternUnits="userSpaceOnUse" width={size} height={size}>
                <circle cx={size / 2} cy={size / 2} r={1.1 * u} fill={stroke} />
              </pattern>
            </g>
          );
        })}
      </defs>

      {/* Context drawn AROUND the sites: the Doppelzug zone's rim. */}
      {!hidden.has('retrace') && <ZoneRim cells={sites.retrace.context_cells} u={u} />}

      {shown.filter((entry) => cellFirst(siteShape(entry.category, entry.site))).map((entry) => drawSite(entry, false))}

      <g transform="translate(0.5 0.5)">
        {shown.filter((entry) => siteShape(entry.category, entry.site) === 'band').map((entry) => drawSite(entry, false))}

        {/* The centreline the ruler measured: thin, solid, under the point marks. */}
        {centerline.map((stroke, i) => (
          <polyline
            key={`cl-${i}`}
            points={pointsAttr(stroke)}
            fill="none"
            stroke={penalty.centerline}
            strokeWidth={THIN * u}
            strokeLinejoin="round"
          />
        ))}

        {/* Glätte's corner windows — what lies there counts under Ecken. */}
        {!hidden.has('smoothness') &&
          sites.smoothness.context_paths.map((path, i) => (
            <Line key={`win-${i}`} path={path} colour={penalty.mark} width={2 * u} style={strokeStyle.dotted} />
          ))}
      </g>

      {/* Line and point marks — over the centreline. Cells were drawn above. */}
      <g transform="translate(0.5 0.5)">
        {shown
          .filter((entry) => {
            const shape = siteShape(entry.category, entry.site);
            return !cellFirst(shape) && shape !== 'band';
          })
          .map((entry) => drawSite(entry, false))}
      </g>

      {/* The selection: the same mark again in the state colour and wider,
          plus a ring round its place — a second channel, so the chosen site
          is found by shape, not by hue alone. */}
      {selected && !hidden.has(selected.category) && (
        <>
          {cellFirst(siteShape(selected.category, selected.site)) && drawSite(selected, true)}
          <g transform="translate(0.5 0.5)">
            {!cellFirst(siteShape(selected.category, selected.site)) && drawSite(selected, true)}
            <circle
              cx={selected.site.x}
              cy={selected.site.y}
              r={SELECT_RING * u}
              fill="none"
              stroke={penalty.selected}
              strokeWidth={2 * u}
            />
          </g>
        </>
      )}

      <g transform="translate(0.5 0.5)">
        {/* Touch targets, 44 px, costliest last so it wins an overlap. */}
        {hitOrder.map((entry) => (
          <circle
            key={`hit-${siteKey(entry.category, entry.site.index)}`}
            cx={entry.site.x}
            cy={entry.site.y}
            r={HIT_RADIUS * u}
            fill="transparent"
            aria-hidden="true"
            style={{ cursor: 'pointer' }}
            onClick={() => onSelect(entry.category, entry.site.index)}
          />
        ))}
      </g>
    </svg>
  );
}

/**
 * The ①–⑤ pins, in their own layer measured in SCREEN pixels (no viewBox):
 * a numeral in the crop's user units would compute as a 4 px font — the
 * typo-floor sweep reads computed sizes — while rendering at 14. Each disc is
 * set off its point by a short leader so the mark it names stays visible
 * (`placePins` keeps the discs off each other). Mounted after the marks, so a
 * pin wins its tap; the layer itself lets every other tap through to them.
 */
export function PenaltyPins({ data, scale, hidden, selectedKey, onSelect }: PenaltyOverlayProps) {
  const { frame, pins } = data;
  const discs = useMemo(() => placePins(pins, scale, PIN_OFFSET, PIN_R), [pins, scale]);
  return (
    <svg
      width={frame.width * scale}
      height={frame.height * scale}
      style={{ position: 'absolute', inset: 0, overflow: 'visible', pointerEvents: 'none' }}
      aria-hidden="true"
    >
      {pins
        .filter((pin) => !hidden.has(pin.category))
        .map((pin) => {
          const isSelected = siteKey(pin.category, pin.index) === selectedKey;
          const disc = discs.find((d) => d.rank === pin.rank);
          // Pixel centres (+0.5), then screen pixels.
          const px = (pin.x + 0.5) * scale;
          const py = (pin.y + 0.5) * scale;
          const cx = ((disc?.x ?? pin.x) + 0.5) * scale;
          const cy = ((disc?.y ?? pin.y) + 0.5) * scale;
          return (
            <g
              key={`pin-${pin.rank}`}
              aria-hidden="true"
              style={{ cursor: 'pointer', pointerEvents: 'auto' }}
              onClick={() => onSelect(pin.category, pin.index)}
            >
              <line x1={px} y1={py} x2={cx} y2={cy} stroke={penalty.pin} strokeWidth={THIN} />
              <circle
                cx={cx}
                cy={cy}
                r={PIN_R}
                fill={penalty.pin}
                stroke={isSelected ? penalty.selected : '#fff'}
                strokeWidth={isSelected ? 3 : 1.5}
              />
              <text
                x={cx}
                y={cy}
                fill="#fff"
                fontFamily={garamond}
                fontSize={PIN_FONT}
                fontWeight={600}
                textAnchor="middle"
                dominantBaseline="central"
              >
                {pin.rank}
              </text>
              <circle cx={cx} cy={cy} r={HIT_RADIUS} fill="transparent" />
            </g>
          );
        })}
    </svg>
  );
}

interface SiteMarkProps {
  shape: MarkerShape;
  site: PenaltySiteOut & { x: number; y: number };
  /** The site's magnitude on the letter's one scale, [0, 1]. */
  t: number;
  /** Drawn as the selection: the state colour, 2 px wider. */
  emphasis: boolean;
  patternId: (kind: 'hatch' | 'cross' | 'stipple') => string;
  u: number;
  bandMax: number;
  /** The x-height in crop pixels — how far a Senkrechte run may swing. */
  unitPx: number;
}

/** One site's mark — the shape says the category, the width its size. */
function SiteMark({ shape, site, t, emphasis, patternId, u, bandMax, unitPx }: SiteMarkProps) {
  const path = (role: string) => site.paths.find((p) => p.role === role);
  const colour = emphasis ? penalty.selected : penalty.mark;
  const bonus = emphasis ? 2 : 0;
  // Stroke width in crop pixels: the magnitude channel, in screen pixels, times u.
  const width = (markWidth(t) + bonus) * u;
  switch (shape) {
    case 'hatch':
    case 'stipple':
    case 'crosshatch': {
      // The pixel count IS the magnitude for a pixel term (each missed pixel is
      // one equal piece of it), so the area says the size; no width needed.
      const paint = patternId(shape === 'crosshatch' ? 'cross' : shape);
      return (
        <g>
          {site.cells.map(([x, y, w], i) => (
            <rect key={i} x={x} y={y} width={w} height={1} fill={paint} />
          ))}
        </g>
      );
    }
    case 'edgeDots':
      // Boundary pixels as dots — „Randpunkte": the Chamfer part lives on the
      // edge, and a dotted edge reads as an edge rather than as an area. Drawn
      // in the pixel grid, hence the explicit half-pixel centre.
      return (
        <g>
          {site.cells.flatMap(([x, y, w]) =>
            Array.from({ length: w }, (_, k) => (
              <circle key={`${x + k},${y}`} cx={x + k + 0.5} cy={y + 0.5} r={(0.6 + 1.0 * t + bonus / 2) * u} fill={colour} />
            )),
          )}
        </g>
      );
    case 'band': {
      // The Glätte heat band: per step as wide as the two samples' share of the
      // jerk, on the letter's one band scale.
      const segment = path('segment');
      if (!segment || segment.points.length < 2) return null;
      return (
        <g>
          {segment.points.slice(1).map(([x, y], i) => {
            const [x0, y0] = segment.points[i];
            const share = bandMax > 0 ? ((segment.values[i] ?? 0) + (segment.values[i + 1] ?? 0)) / 2 / bandMax : 0;
            return (
              <line
                key={i}
                x1={x0}
                y1={y0}
                x2={x}
                y2={y}
                stroke={colour}
                strokeWidth={(1 + 7 * share + bonus) * u}
                strokeLinecap="round"
              />
            );
          })}
        </g>
      );
    }
    case 'bracket': {
      const run = path('run');
      const ideal = path('ideal');
      if (!run || run.points.length < 2) return null;
      const xIdeal = ideal?.points[0]?.[0] ?? site.x;
      const factor = verticalExaggeration(run.values, unitPx);
      const blown = run.points.map(([, y], i): [number, number] => [xIdeal + factor * (run.values[i] ?? 0), y]);
      const ys = run.points.map(([, y]) => y);
      const top = Math.min(...ys);
      const bottom = Math.max(...ys);
      const left = Math.min(...blown.map(([x]) => x), ...run.points.map(([x]) => x)) - 7 * u;
      const tick = 4 * u;
      return (
        <g fill="none" stroke={colour}>
          {ideal && <Line path={ideal} colour={colour} width={THIN * u} style={strokeStyle.dashed} />}
          <polyline points={pointsAttr(blown)} strokeWidth={width} strokeLinejoin="round" />
          <polyline
            points={pointsAttr([
              [left + tick, top],
              [left, top],
              [left, bottom],
              [left + tick, bottom],
            ])}
            strokeWidth={width}
          />
        </g>
      );
    }
    case 'square': {
      const half = SQUARE_HALF * u;
      return (
        <g fill="none" stroke={colour}>
          {(['approach_in', 'approach_out'] as const).map((role) => {
            const p = path(role);
            return p ? <Line key={role} path={p} colour={colour} width={THIN * u} style={strokeStyle.solid} /> : null;
          })}
          {(['chord_in', 'chord_out'] as const).map((role) => {
            const p = path(role);
            return p ? <Line key={role} path={p} colour={colour} width={THIN * u} style={strokeStyle.dashed} /> : null;
          })}
          {(['peak_in', 'peak_out'] as const).map((role) => {
            const point = path(role)?.points[0];
            return point ? <circle key={role} cx={point[0]} cy={point[1]} r={2.25 * u} fill={colour} stroke="none" /> : null;
          })}
          <rect x={site.x - half} y={site.y - half} width={half * 2} height={half * 2} strokeWidth={width} />
        </g>
      );
    }
    case 'ring':
      return (
        <g fill="none" stroke={colour}>
          {(['line_before', 'line_after'] as const).map((role) => {
            const p = path(role);
            return p ? <Line key={role} path={p} colour={colour} width={THIN * 1.5 * u} style={strokeStyle.solid} /> : null;
          })}
          <circle cx={site.x} cy={site.y} r={RING_R * u} strokeWidth={width} />
        </g>
      );
    case 'whiskers':
      // A feeler from each off-skeleton sample to the nearest skeleton pixel.
      return (
        <g stroke={colour}>
          {site.paths
            .filter((p) => p.role === 'whisker' && p.points.length === 2)
            .map((p, i) => {
              const [[x0, y0], [x1, y1]] = p.points;
              return (
                <g key={i}>
                  <line x1={x0} y1={y0} x2={x1} y2={y1} strokeWidth={Math.max(THIN * u, width * 0.6)} strokeLinecap="round" />
                  <circle cx={x1} cy={y1} r={1.5 * u} fill={colour} stroke="none" />
                </g>
              );
            })}
        </g>
      );
    default:
      return null;
  }
}

/** A polyline in one taught stroke style — the whole token, pattern AND cap. */
function Line({ path, colour, width, style }: { path: PenaltyPathOut; colour: string; width: number; style: StrokeStyle }) {
  return (
    <polyline
      points={pointsAttr(path.points)}
      fill="none"
      stroke={colour}
      strokeWidth={width}
      strokeLinecap={style.cap}
      strokeLinejoin="round"
      strokeDasharray={style.dash ? style.dash.map((d) => d * width).join(' ') : undefined}
    />
  );
}

/**
 * The Doppelzug zone's rim, as dots on its boundary pixels: the zone is where
 * the retrace term looks for ink at all, so the missed ink inside it only
 * reads against its outline.
 */
function ZoneRim({ cells, u }: { cells: PenaltyCategoryOut['context_cells']; u: number }) {
  const rim = useMemo(() => zoneRim(cells), [cells]);
  if (rim.length === 0) return null;
  return (
    <g>
      {rim.map(([x, y]) => (
        <circle key={`${x},${y}`} cx={x + 0.5} cy={y + 0.5} r={0.9 * u} fill={penalty.mark} />
      ))}
    </g>
  );
}

const pointsAttr = (points: ReadonlyArray<readonly [number, number]>): string =>
  points.map(([x, y]) => `${x},${y}`).join(' ');

/**
 * The legend's swatch: a category's shape, small, in the mark colour — so a
 * chip names the category AND shows the mark it draws (colour is never the
 * only channel; here it is not a channel at all).
 */
export function PenaltyShapeIcon({ shape, size = 18 }: { shape: MarkerShape; size?: number }) {
  const c = penalty.mark;
  const id = useId().replace(/[^a-zA-Z0-9_-]/g, '');
  const body = (() => {
    switch (shape) {
      case 'band':
        return <path d="M2,11 C6,4 12,4 16,9" fill="none" stroke={c} strokeWidth={3.5} strokeLinecap="round" />;
      case 'bracket':
        return (
          <g fill="none" stroke={c} strokeWidth={1.75}>
            <polyline points="7,2 4,2 4,16 7,16" />
            <line x1={12} y1={2} x2={12} y2={16} strokeDasharray="3 2" />
          </g>
        );
      case 'square':
        return <rect x={4} y={4} width={10} height={10} fill="none" stroke={c} strokeWidth={2} />;
      case 'ring':
        return (
          <g fill="none" stroke={c} strokeWidth={1.75}>
            <circle cx={9} cy={9} r={5} />
            <line x1={1} y1={15} x2={17} y2={3} />
          </g>
        );
      case 'crosshatch':
        return (
          <g>
            <rect x={2} y={2} width={14} height={14} fill={`url(#${id}-x)`} stroke={c} strokeWidth={0.75} />
          </g>
        );
      case 'hatch':
        return <rect x={2} y={2} width={14} height={14} fill={`url(#${id}-h)`} stroke={c} strokeWidth={0.75} />;
      case 'stipple':
        return <rect x={2} y={2} width={14} height={14} fill={`url(#${id}-s)`} stroke={c} strokeWidth={0.75} />;
      case 'edgeDots':
        return (
          <g fill={c}>
            {[3, 7, 11, 15].map((x) => (
              <circle key={x} cx={x} cy={9} r={1.3} />
            ))}
          </g>
        );
      case 'whiskers':
        return (
          <g stroke={c} strokeWidth={1.5}>
            <line x1={3} y1={14} x2={6} y2={4} />
            <line x1={9} y1={14} x2={11} y2={4} />
            <line x1={15} y1={14} x2={15} y2={4} />
          </g>
        );
      default:
        return null;
    }
  })();
  return (
    <svg width={size} height={size} viewBox="0 0 18 18" aria-hidden="true" style={{ display: 'block', flexShrink: 0 }}>
      <defs>
        <pattern id={`${id}-h`} patternUnits="userSpaceOnUse" width={4} height={4}>
          <path d="M0,4 L4,0" stroke={c} strokeWidth={1.1} />
        </pattern>
        <pattern id={`${id}-x`} patternUnits="userSpaceOnUse" width={4} height={4}>
          <path d="M0,4 L4,0 M0,0 L4,4" stroke={c} strokeWidth={0.9} />
        </pattern>
        <pattern id={`${id}-s`} patternUnits="userSpaceOnUse" width={4} height={4}>
          <circle cx={2} cy={2} r={0.9} fill={c} />
        </pattern>
      </defs>
      {body}
    </svg>
  );
}
