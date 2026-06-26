// WrittenSheet — the "Geschrieben" alphabet laid out like a writing-practice
// sheet instead of separate boxes: full-width rows ruled with the four Lineatur
// lines (Ober-, Mittel-, Grund-, Unterlinie), and the synthesised letters
// written ON the lines, stroke by stroke, in the pen's order. The rows mirror
// the chart's own layout (same letters per row, in the same order —
// `markedRowsOf` clusters the marked bboxes by baseline); the letters sit at a
// uniform spacing. A marked-but-untraced letter keeps its slot as a gap.
//
// On load each glyph writes itself in (a gentle left-to-right cascade); clicking
// a glyph re-writes it in place — no modal. Technique per glyph (from
// WrittenGlyph): fill the silhouette, then reveal it with a wide mask swept
// along the centerlines via an animated stroke-dashoffset, lifting between pen
// strokes; the ink then settles fresh → oxidized. Coordinates: template space
// (baseline 0, y up), negated for SVG. Every row shares one viewBox width so the
// glyph scale stays constant; the four lines span the full width.

import { Box, Stack, Typography, keyframes } from '@mui/material';
import { useEffect, useId, useMemo, useRef, useState } from 'react';
import type { KeyboardEvent as ReactKeyboardEvent } from 'react';

import { CONFIG } from '@/global-config';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion';
import { ApiError, getDiagnostic, type DiagnosticData } from '@/lib/api';
import { ringsToPathD, type Ring } from '@/lib/svg';
import { de } from '@/locales';
import { inkState, paper, schulheft } from '@/styles/paper';
import type { MarkedSlot } from '@/sections/tafel/useGrundtafeln';

type Pt = [number, number];

// Cache the in-flight/resolved diagnostic per (source, glyph); a 404 (no
// canonical) resolves to null, never a throw.
const cache = new Map<string, Promise<DiagnosticData | null>>();
function fetchGlyph(key: string): Promise<DiagnosticData | null> {
  const id = `${CONFIG.sourceId}|${key}`;
  let p = cache.get(id);
  if (!p) {
    p = getDiagnostic(CONFIG.sourceId, key).catch((e) => {
      if (e instanceof ApiError && e.status === 404) return null;
      cache.delete(id); // a transient error shouldn't be cached — allow a retry
      throw e;
    });
    cache.set(id, p);
  }
  return p;
}

const CELL_W = 2.0; // fixed slot width (x-height units) so the ruling is stable from the first frame
const PAD_Y = 0.14; // vertical air above the ascender / below the descender
const RULE = schulheft.rulingBlueFaded;
const RULE_W = 1; // px — non-scaling so the rule stays a hairline at any row scale
const HOVER = 'rgba(64, 130, 109, 0.10)'; // faint viridian wash on hover/focus
const WRITE_MS = 1100; // per-glyph write-in duration
const PEN_PAUSE_MS = 130; // pause at a pen lift so an Absetzen reads as a lift
const SETTLE_MS = 1500; // iron-gall fresh → oxidized
const STAGGER_MS = 65; // per-glyph start offset for the load cascade
const STAGGER_CAP = 1300; // …capped so the last letter never waits too long

const reveal = keyframes`from { stroke-dashoffset: 1; } to { stroke-dashoffset: 0; }`;
const inkSettle = keyframes`from { fill: ${inkState.fresh}; } to { fill: ${inkState.oxidized}; }`;

// Template-space Lineatur levels from a style ratio. x-height (baseline→midband)
// is the unit (= Mittellänge); the Oberlänge/Unterlänge scale relative to it.
function guidesFromRatio(ratio: number[]): DiagnosticData['template_guides'] {
  const [ober = 1, mittel = 1, unter = 1] = ratio;
  const m = mittel || 1;
  return { baseline: 0, midband: 1, ascender: 1 + ober / m, descender: -(unter / m) };
}

function chordLength(points: Pt[]): number {
  let total = 0;
  for (let i = 1; i < points.length; i++) {
    total += Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]);
  }
  return total;
}

// Polyline → SVG path, translated by tx and y-negated (template y up, SVG down).
function lineD(points: Pt[], tx: number): string {
  return points.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x + tx},${-y}`).join(' ');
}

// One stroke's rings → path, translated by tx (ringsToPathD y-negates).
function ringsD(stroke: Ring[], tx: number): string {
  return ringsToPathD(stroke.map((r) => r.map(([x, y]): Pt => [x + tx, y])), true);
}

interface GlyphGeom {
  strokes: Ring[][]; // per-stroke silhouette rings, template coords
  centerlines: Pt[][]; // per-stroke spine the reveal sweeps along
  maskWidth: number;
  minX: number;
  maxX: number;
}

// Per-stroke silhouette + centerlines + x-extent for one glyph. Prefers the
// capsule-union rings (`outline_paths`); falls back to the legacy ribbon
// polygons, then to the anchor span if a payload carries no silhouette at all.
function glyphGeom(data: DiagnosticData): GlyphGeom | null {
  const strokes: Ring[][] = data.outline_paths?.length
    ? data.outline_paths
    : data.outline_polygons?.length
      ? data.outline_polygons.filter((p) => p.length > 2).map((p) => [p])
      : data.outline_polygon && data.outline_polygon.length > 2
        ? [[data.outline_polygon]]
        : [];

  const centerlines: Pt[][] =
    data.centerlines_template && data.centerlines_template.length
      ? (data.centerlines_template as Pt[][])
      : [data.anchors_template as Pt[]];
  const maxHalf = data.half_widths_template.length ? Math.max(...data.half_widths_template) : 0.05;
  const maskWidth = Math.max(0.05, 2.2 * maxHalf);

  let minX = Infinity;
  let maxX = -Infinity;
  for (const stroke of strokes) {
    for (const ring of stroke) {
      for (const [x] of ring) {
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
      }
    }
  }
  if (!Number.isFinite(minX)) {
    const xs = data.anchors_template.map((a) => a[0]);
    if (!xs.length) return null;
    minX = Math.min(...xs) - maxHalf;
    maxX = Math.max(...xs) + maxHalf;
  }
  return { strokes, centerlines, maskWidth, minX, maxX };
}

interface SheetGlyphProps {
  geom: GlyphGeom;
  glyph: string;
  cellX: number; // left edge of this slot, template coords
  cellW: number;
  vbY: number;
  vbH: number;
  orderIndex: number; // reading-order index, for the load cascade
  reducedMotion: boolean;
}

// One written glyph inside the row SVG: the silhouette revealed by a mask swept
// along its centerlines. Owns a `run` counter — bumping it (a click/tap)
// remounts the mask + ink so the write-in replays, in place, with no modal.
function SheetGlyph({ geom, glyph, cellX, cellW, vbY, vbH, orderIndex, reducedMotion }: SheetGlyphProps) {
  const uid = useId();
  const [run, setRun] = useState(0);
  const animate = !reducedMotion;
  const tx = cellX + cellW / 2 - (geom.minX + geom.maxX) / 2;

  // Per-stroke timing: duration ∝ chord length, a pen pause between strokes.
  // The first stroke is offset by the cascade delay on the initial write only.
  const lengths = geom.centerlines.map(chordLength);
  const total = lengths.reduce((s, l) => s + l, 0) || 1;
  let cursor = run === 0 ? Math.min(orderIndex * STAGGER_MS, STAGGER_CAP) : 0;
  const timing = geom.centerlines.map((_, i) => {
    const dur = Math.max(180, (lengths[i] / total) * WRITE_MS);
    const delay = cursor;
    cursor += dur + PEN_PAUSE_MS;
    return { dur, delay };
  });
  const writeEnd = cursor;

  const maskId = `sheet-${uid.replace(/[^a-zA-Z0-9_-]/g, '_')}-${run}`;
  const bx = tx + geom.minX - 0.08;
  const bw = geom.maxX - geom.minX + 0.16;

  return (
    <Box
      component="g"
      role="button"
      tabIndex={0}
      aria-label={`${glyph} — ${de.tafel.replayHint}`}
      onClick={() => setRun((r) => r + 1)}
      onKeyDown={(e: ReactKeyboardEvent<SVGGElement>) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          setRun((r) => r + 1);
        }
      }}
      sx={{
        cursor: 'pointer',
        // no UA focus ring (SVG draws an ugly thick black/white box) — the cellbg
        // wash is the focus affordance instead
        outline: 'none',
        '& .cellbg': { fill: 'transparent', transition: 'fill 120ms' },
        '&:hover .cellbg, &:focus-visible .cellbg': { fill: HOVER },
      }}
    >
      <rect className="cellbg" x={cellX} y={vbY} width={cellW} height={vbH} rx={0.08} />
      <defs>
        <mask id={maskId} maskUnits="userSpaceOnUse" x={bx} y={vbY} width={bw} height={vbH}>
          <rect x={bx} y={vbY} width={bw} height={vbH} fill="black" />
          {geom.centerlines.map((line, i) => (
            <Box
              component="path"
              key={`${run}-${i}`}
              d={lineD(line, tx)}
              fill="none"
              stroke="#fff"
              strokeWidth={geom.maskWidth}
              strokeLinecap="round"
              strokeLinejoin="round"
              pathLength={1}
              strokeDasharray={1}
              sx={{
                strokeDashoffset: animate ? 1 : 0,
                animation: animate
                  ? `${reveal} ${timing[i].dur}ms linear ${timing[i].delay}ms forwards`
                  : undefined,
              }}
            />
          ))}
        </mask>
      </defs>
      <Box
        component="g"
        key={`ink-${run}`}
        mask={`url(#${maskId})`}
        pointerEvents="none"
        sx={{
          fill: animate ? inkState.fresh : inkState.oxidized,
          animation: animate ? `${inkSettle} ${SETTLE_MS}ms ease ${writeEnd}ms forwards` : undefined,
        }}
      >
        {geom.strokes.map((stroke, i) => (
          <path key={i} d={ringsD(stroke, tx)} fillRule="evenodd" />
        ))}
      </Box>
    </Box>
  );
}

interface RowProps {
  row: MarkedSlot[];
  rowOffset: number; // reading-order index of this row's first slot
  cellW: number;
  rowW: number; // shared full template width (maxRowLength · cellW)
  geomByKey: Map<string, GlyphGeom>;
  guides: DiagnosticData['template_guides'];
  width: number; // rendered px width (sized exactly so the lines never distort)
  reducedMotion: boolean;
}

// One ruled row: the four full-width Lineatur lines + the row's written glyphs.
function SheetRow({ row, rowOffset, cellW, rowW, geomByKey, guides, width, reducedMotion }: RowProps) {
  const vbY = -(guides.ascender + PAD_Y);
  const vbH = guides.ascender - guides.descender + 2 * PAD_Y;
  const lines = [
    { y: guides.baseline, opacity: 1, dash: undefined }, // Grundlinie — the writing line
    { y: guides.midband, opacity: 0.65, dash: '4 3' }, // Mittellinie (dashes are px: non-scaling)
    { y: guides.ascender, opacity: 0.45, dash: undefined }, // Oberlinie
    { y: guides.descender, opacity: 0.45, dash: undefined }, // Unterlinie
  ];

  return (
    <Box
      component="svg"
      viewBox={`0 ${vbY} ${rowW} ${vbH}`}
      width={width}
      height={(width * vbH) / rowW}
      preserveAspectRatio="xMidYMid meet"
      sx={{ display: 'block' }}
    >
      {lines.map((l, i) => (
        <line
          key={i}
          x1={0}
          x2={rowW}
          y1={-l.y}
          y2={-l.y}
          stroke={RULE}
          strokeOpacity={l.opacity}
          strokeWidth={RULE_W}
          strokeDasharray={l.dash}
          vectorEffect="non-scaling-stroke"
        />
      ))}
      {row.map((slot, i) => {
        const geom = slot.key ? geomByKey.get(slot.key) : undefined;
        if (!slot.key || !geom) return null; // gap
        return (
          <SheetGlyph
            key={i}
            geom={geom}
            glyph={slot.glyph}
            cellX={i * cellW}
            cellW={cellW}
            vbY={vbY}
            vbH={vbH}
            orderIndex={rowOffset + i}
            reducedMotion={reducedMotion}
          />
        );
      })}
    </Box>
  );
}

interface Props {
  rows: MarkedSlot[][]; // chart-row-grouped marked letters (gaps = null key)
  ratio: number[]; // style_ratio (Oberlänge:Mittellänge:Unterlänge)
}

export function WrittenSheet({ rows, ratio }: Props) {
  const reducedMotion = usePrefersReducedMotion();
  const [dataByKey, setDataByKey] = useState<Map<string, DiagnosticData | null> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerW, setContainerW] = useState(0);

  const keys = useMemo(
    () => rows.flat().map((s) => s.key).filter((k): k is string => !!k),
    [rows],
  );

  // Fetch a diagnostic for each written letter (gaps need no fetch).
  useEffect(() => {
    let cancelled = false;
    setDataByKey(null);
    Promise.all(keys.map((k) => fetchGlyph(k).then((d) => [k, d] as const)))
      .then((entries) => {
        if (!cancelled) setDataByKey(new Map(entries));
      })
      .catch(() => {
        if (!cancelled) setDataByKey(new Map()); // render only the lineature on error
      });
    return () => {
      cancelled = true;
    };
  }, [keys]);

  // Track the available width so the rendered px size adapts to the viewport.
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const measure = () => setContainerW(el.clientWidth);
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const geomByKey = useMemo(() => {
    const m = new Map<string, GlyphGeom>();
    if (dataByKey) {
      for (const [key, data] of dataByKey) {
        const g = data && glyphGeom(data);
        if (g) m.set(key, g);
      }
    }
    return m;
  }, [dataByKey]);

  // Lineature levels straight from the style ratio (Oberlänge:Mittellänge:
  // Unterlänge), so the ruling draws before any glyph loads. x-height
  // (baseline→midband) is the unit; each glyph's own baseline is 0, so the
  // written letters land on these lines exactly.
  const guides = useMemo(() => guidesFromRatio(ratio), [ratio]);

  const maxRow = useMemo(() => rows.reduce((m, r) => Math.max(m, r.length), 0), [rows]);
  const rowW = CELL_W * Math.max(1, maxRow);

  // Reading-order offset of each row's first slot (for the load cascade).
  const rowOffsets = useMemo(() => {
    const offs: number[] = [];
    let acc = 0;
    for (const r of rows) {
      offs.push(acc);
      acc += r.length;
    }
    return offs;
  }, [rows]);

  return (
    <Box ref={containerRef} sx={{ width: '100%' }}>
      {rows.length === 0 ? (
        <Typography sx={{ color: paper.inkSoft }}>{de.tafel.empty}</Typography>
      ) : (
        // The ruled rows render at once; each glyph writes itself in as its
        // diagnostic resolves (geomByKey fills in), so the lines are there first.
        containerW > 0 && (
          <Stack spacing={0.75}>
            {rows.map((row, ri) => (
              <SheetRow
                key={ri}
                row={row}
                rowOffset={rowOffsets[ri]}
                cellW={CELL_W}
                rowW={rowW}
                geomByKey={geomByKey}
                guides={guides}
                width={containerW}
                reducedMotion={reducedMotion}
              />
            ))}
          </Stack>
        )
      )}
    </Box>
  );
}
