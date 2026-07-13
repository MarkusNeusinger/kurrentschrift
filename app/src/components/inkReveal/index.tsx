// Shared "as written" ink-reveal primitives. The three surfaces that render a
// canonical form "as the pen drew it" — WrittenGlyph (one glyph), WrittenWord
// (a whole word/line) and WrittenSheet (the Schreibtafel's ruled rows) — used
// to each reimplement the identical SVG technique: a filled silhouette masked
// by a wide path swept along its centerline via an animated stroke-dashoffset,
// with a fibre-wicking ink-bleed filter and an iron-gall settle. That technique
// now lives here once; the surfaces are thin consumers that supply their own
// outer shell (layout, viewBox, interaction) and hand these pieces the geometry.
//
// The reveal MASK (swept centerlines) and the SETTLE/kinematics timing pair
// (lib/strokeTiming + hooks/useStrokeReveal) are the shared core; a surface
// still owns its filled-ink group (glyph fills, word fills + strokes connectors,
// sheet fills) because what gets filled differs, but the settle sx is shared via
// `inkGroupSx`.

import ReplayIcon from '@mui/icons-material/Replay';
import { IconButton, keyframes, type SxProps, type Theme } from '@mui/material';
import type { MutableRefObject } from 'react';

import { de } from '@/locales';
import { inkState, schulheft } from '@/styles/paper';
import { polylineToPathD, type Ring } from '@/lib/svg';

// ── Ink-bleed filter ───────────────────────────────────────────────────────
// Fibre-wicking displacement on the silhouette group — deliberately active
// during the write-in too (ink wicks the moment it touches paper). The viewBox
// is in template units (x-height = 1), so `scale` must be tiny; pixel-space
// values would be wildly off. `inset` extends the filter region so the
// displaced edges are not clipped.
interface InkBleedFilterProps {
  id: string;
  scale: number;
  inset?: { x: string; y: string; width: string; height: string };
}

const DEFAULT_INSET = { x: '-5%', y: '-5%', width: '110%', height: '110%' };

export function InkBleedFilter({ id, scale, inset = DEFAULT_INSET }: InkBleedFilterProps) {
  return (
    <filter id={id} x={inset.x} y={inset.y} width={inset.width} height={inset.height}>
      <feTurbulence type="fractalNoise" baseFrequency="6" numOctaves="2" seed="7" result="noise" />
      <feDisplacementMap in="SourceGraphic" in2="noise" scale={scale} xChannelSelector="R" yChannelSelector="G" />
    </filter>
  );
}

// ── Reveal mask ────────────────────────────────────────────────────────────
// Black hides, the white sweep reveals the silhouette beneath. One <path> per
// pen-stroke; `useStrokeReveal` animates each path's stroke-dashoffset from 1
// (hidden) to 0 (drawn) along the non-linear kinematics table. A pen lift is a
// real gap because each stroke is its own centerline path.
export interface RevealStroke {
  // Centerline polyline in the surface's own coords (already translated); the
  // component y-negates it for SVG.
  centerline: Ring;
  // Sweep width — at least the full local ink width (2·half) everywhere.
  maskWidth: number;
}

interface RevealMaskProps {
  id: string;
  // The mask region (userSpaceOnUse) — the surface's viewBox or a glyph's box.
  bounds: { x: number; y: number; width: number; height: number };
  strokes: RevealStroke[];
  pathRefs: MutableRefObject<Array<SVGPathElement | null>>;
  animate: boolean;
  // Bumped on replay to remount the paths (restarts the reveal); also namespaces
  // the per-path React keys.
  runKey: string | number;
}

export function RevealMask({ id, bounds, strokes, pathRefs, animate, runKey }: RevealMaskProps) {
  return (
    <mask id={id} maskUnits="userSpaceOnUse" x={bounds.x} y={bounds.y} width={bounds.width} height={bounds.height}>
      <rect x={bounds.x} y={bounds.y} width={bounds.width} height={bounds.height} fill="black" />
      {strokes.map((s, i) => (
        <path
          key={`${runKey}-${i}`}
          ref={(el) => {
            pathRefs.current[i] = el;
          }}
          d={polylineToPathD(s.centerline)}
          fill="none"
          stroke="#fff"
          strokeWidth={s.maskWidth}
          strokeLinecap="round"
          strokeLinejoin="round"
          pathLength={1}
          strokeDasharray={1}
          style={{ strokeDashoffset: animate ? 1 : 0 }}
        />
      ))}
    </mask>
  );
}

// ── Iron-gall settle ───────────────────────────────────────────────────────
// German school ink wrote blue-black and oxidized to near-black (Reichs-
// Tintenprüfung 1888/1912) — compressed here from weeks to seconds after the
// write-in completes. Knowingly expressive synthesis. Two keyframes: glyph/sheet
// age only their fill; a word also ages the stroke (its connectors are stroked).
const inkSettleFill = keyframes`from { fill: ${inkState.fresh}; } to { fill: ${inkState.oxidized}; }`;
const inkSettleFillStroke = keyframes`
  from { fill: ${inkState.fresh}; stroke: ${inkState.fresh}; }
  to { fill: ${inkState.oxidized}; stroke: ${inkState.oxidized}; }
`;

// The `sx` for the filled-ink group: hold the fresh (or fixed inkColor) tone,
// then play the settle once, `writeEndMs` after mount. A fixed `inkColor` (the
// quiz comparison's red/black) skips the settle and holds one tone.
export function inkGroupSx(opts: {
  animate: boolean;
  writeEndMs: number;
  settleMs: number;
  inkColor?: string;
  // Age the stroke too (word connectors), not just the fill.
  withStroke?: boolean;
}): SxProps<Theme> {
  const { animate, writeEndMs, settleMs, inkColor, withStroke } = opts;
  const tone = inkColor ?? (animate ? inkState.fresh : inkState.oxidized);
  const kf = withStroke ? inkSettleFillStroke : inkSettleFill;
  return {
    fill: tone,
    ...(withStroke ? { stroke: tone } : {}),
    animation: animate && !inkColor ? `${kf} ${settleMs}ms ease ${writeEndMs}ms forwards` : undefined,
  };
}

// ── Baseline + midband guides ──────────────────────────────────────────────
// A whisper of period ruling in the faint exercise-book blue (schulheft), so a
// glyph/word sits on context lines; the midband is the quieter of the two. Used
// by WrittenGlyph and WrittenWord (the Schreibtafel draws its own four-line
// Lineatur per row). Coords are template units, y-negated for SVG.
interface InkGuidesProps {
  minX: number;
  width: number;
  baseline: number;
  midband: number;
}

const GUIDE = schulheft.rulingBlueFaded;

export function InkGuides({ minX, width, baseline, midband }: InkGuidesProps) {
  return (
    <>
      <line x1={minX} y1={-baseline} x2={minX + width} y2={-baseline} stroke={GUIDE} strokeWidth={0.012} />
      <line
        x1={minX}
        y1={-midband}
        x2={minX + width}
        y2={-midband}
        stroke={GUIDE}
        strokeOpacity={0.55}
        strokeWidth={0.012}
        strokeDasharray="0.08 0.06"
      />
    </>
  );
}

// ── Replay control ─────────────────────────────────────────────────────────
// The faint bottom-right "write it again" button, byte-identical across the
// glyph and word surfaces.
export function ReplayButton({ onClick }: { onClick: () => void }) {
  return (
    <IconButton
      size="small"
      onClick={onClick}
      aria-label={de.common.writtenGlyph.replay}
      sx={{ position: 'absolute', bottom: 4, right: 4, color: 'text.disabled', '&:hover': { color: 'text.secondary' } }}
    >
      <ReplayIcon fontSize="small" />
    </IconButton>
  );
}
