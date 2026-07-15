// WrittenSheet — the "Geschrieben" alphabet laid out like a writing-practice
// sheet instead of separate boxes: full-width rows ruled with the four Lineatur
// lines (Ober-, Mittel-, Grund-, Unterlinie), and the synthesised letters
// written ON the lines, stroke by stroke, in the pen's order. The written
// letters are re-flowed into rows of LETTERS_PER_ROW at one fixed scale, in
// reading order; untraced letters are dropped (no gaps). Each letter keeps its
// own ink width and is flowed left-to-right with the gap measured from the END
// of one glyph to the START of the next (proportional spacing), so wide letters
// like m/w never crowd or overlap their neighbours. That gap is CONSTANT WITHIN
// A ROW ("gleich pro Zeile") and every full row is justified to fill the shared
// width, so rows span edge to edge; the gap may differ between rows. While the
// glyphs load, a "pen warming up" loader pulses centred in the ruling until the
// first letter starts.
//
// On load the diagnostics resolve together, then each glyph writes itself in
// (a gentle left-to-right cascade); clicking
// a glyph clears it, pauses, then re-writes it in place — no modal. Technique per glyph (from
// WrittenGlyph): fill the silhouette, then reveal it with a wide mask swept
// along the centerlines via stroke-dashoffset, lifting between pen strokes —
// driven by the shared kinematics pair (lib/strokeTiming + useStrokeReveal), so
// the pen slows in curves and stroke durations follow isochrony exactly like
// WrittenWord/WrittenGlyph, not a constant-speed sweep; the ink then settles
// fresh → oxidized. Coordinates: template space
// (baseline 0, y up), negated for SVG. Every row shares one viewBox width so the
// glyph scale stays constant; the four lines span the full width.

import { Box, Button, Stack, Typography, keyframes } from '@mui/material';
import { visuallyHidden } from '@mui/utils';
import { useEffect, useId, useMemo, useRef, useState } from 'react';
import type { KeyboardEvent as ReactKeyboardEvent } from 'react';

import { CONFIG } from '@/global-config';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion';
import { useStrokeReveal } from '@/hooks/useStrokeReveal';
import { fetchRenderGlyphs, type GlyphRenderData } from '@/lib/api';
import {
  allocateDurations,
  sequenceReveal,
  strokeTimeProfile,
  PEN_PAUSE_MS,
  SHEET_MIN_STROKE_MS,
  SHEET_SETTLE_MS,
  SHEET_WRITE_MS,
} from '@/lib/strokeTiming';
import { RevealMask, inkGroupSx } from '@/components/inkReveal';
import { ringsToPathD, type Ring } from '@/lib/svg';
import { de } from '@/locales';
import { paper, schulheft } from '@/styles/paper';
import type { MarkedSlot } from '@/sections/tafel/useGrundtafeln';

type Pt = [number, number];

const LETTERS_PER_ROW = 7; // re-flow the written letters into rows of this many (gaps dropped)
// Proportional layout: every letter keeps its own ink width and the SAME gap is
// left between the end of one glyph and the start of the next (x-height units),
// so wide letters (m, w) no longer crowd or overlap their neighbours the way a
// fixed centred cell let them. LEAD pads the row's left/right edges. The gap is
// generous so the width freed by fitting fewer letters per row becomes breathing
// room between the letters rather than a bigger glyph scale (rowW grows with GAP,
// so the per-row scale stays roughly constant as the count drops).
const GAP = 0.7;
const LEAD = 0.3;
const FALLBACK_ROW_W = (1.5 + GAP) * LETTERS_PER_ROW; // pre-load viewBox width (~avg letter)
const PAD_Y = 0.14; // vertical air above the ascender / below the descender
const RULE = schulheft.rulingBlueFaded;
const RULE_W = 1; // px — non-scaling so the rule stays a hairline at any row scale
const HOVER = 'rgba(64, 130, 109, 0.10)'; // faint viridian wash on hover/focus
// Per-glyph write-in target, per-stroke floor, pen-lift pause and settle come
// from lib/strokeTiming (SHEET_WRITE_MS / SHEET_MIN_STROKE_MS / PEN_PAUSE_MS /
// SHEET_SETTLE_MS). These three are the Schreibtafel-only cascade constants.
const STAGGER_MS = 65; // per-glyph start offset for the load cascade
const STAGGER_CAP = 1300; // …capped so the last letter never waits too long
const CLICK_PAUSE_MS = 420; // after a tap the glyph clears, then waits this long before re-writing

// Loading "pen warming up" dots, shown centred in the ruling until the glyphs load.
const loaderPulse = keyframes`0%, 80%, 100% { opacity: 0.25; transform: scale(0.7); } 40% { opacity: 1; transform: scale(1); }`;

// Template-space Lineatur levels from a style ratio. x-height (baseline→midband)
// is the unit (= Mittellänge); the Oberlänge/Unterlänge scale relative to it.
function guidesFromRatio(ratio: number[]): GlyphRenderData['template_guides'] {
  const [ober = 1, mittel = 1, unter = 1] = ratio;
  const m = mittel || 1;
  return { baseline: 0, midband: 1, ascender: 1 + ober / m, descender: -(unter / m) };
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
function glyphGeom(data: GlyphRenderData): GlyphGeom | null {
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
  glyphX: number; // where this glyph's left ink edge (minX) lands, template coords
  cellX: number; // left edge of the hover/focus cell, template coords
  cellW: number;
  vbY: number;
  vbH: number;
  orderIndex: number; // reading-order index, for the load cascade
  reducedMotion: boolean;
}

// One written glyph inside the row SVG: the silhouette revealed by a mask swept
// along its centerlines. Owns a `run` counter — bumping it (a click/tap)
// remounts the mask + ink so the write-in replays, in place, with no modal.
function SheetGlyph({ geom, glyph, glyphX, cellX, cellW, vbY, vbH, orderIndex, reducedMotion }: SheetGlyphProps) {
  const uid = useId();
  const [run, setRun] = useState(0);
  const animate = !reducedMotion;
  // Left-align the ink so the gap to the previous glyph's end is constant.
  const tx = glyphX - geom.minX;

  // Per-stroke timing via the shared kinematics (lib/strokeTiming): the
  // two-thirds power law slows the sweep in curves, isochrony allocates stroke
  // durations sublinearly, a pen pause between strokes. The first stroke is
  // offset by the cascade delay on the initial write; on a tap (run > 0) the
  // remount instantly clears the ink (mask back to offset 1), then
  // CLICK_PAUSE_MS holds it blank before the pen starts re-writing.
  const { timing, writeEnd } = useMemo(() => {
    const profiles = geom.centerlines.map((cl) => strokeTimeProfile(cl));
    const durations = allocateDurations(
      profiles.map((p) => p.weight),
      SHEET_WRITE_MS,
      SHEET_MIN_STROKE_MS,
    );
    // First write: offset by the load cascade; a tap (run > 0) holds the cleared
    // glyph blank for CLICK_PAUSE_MS before the pen restarts. Each stroke lifts
    // to the next with the shared pen-lift pause.
    const start = run === 0 ? Math.min(orderIndex * STAGGER_MS, STAGGER_CAP) : CLICK_PAUSE_MS;
    const { timing: entries, writeEndMs } = sequenceReveal(profiles, durations, { start, trailPause: PEN_PAUSE_MS });
    return { timing: entries, writeEnd: writeEndMs };
  }, [geom, orderIndex, run]);

  // WAAPI drives the per-path dashoffset — the same element-scoped mechanism as
  // WrittenWord/WrittenGlyph, with no per-stroke Emotion @keyframes.
  const maskPathRefs = useRef<Array<SVGPathElement | null>>([]);
  useStrokeReveal(maskPathRefs, timing, animate, run);

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
        <RevealMask
          id={maskId}
          bounds={{ x: bx, y: vbY, width: bw, height: vbH }}
          strokes={geom.centerlines.map((line) => ({
            centerline: line.map(([x, y]): Pt => [x + tx, y]),
            maskWidth: geom.maskWidth,
          }))}
          pathRefs={maskPathRefs}
          animate={animate}
          runKey={run}
        />
      </defs>
      {/* No InkBleedFilter here by design: the Schreibtafel renders the whole
          alphabet at once (up to LETTERS_PER_ROW glyphs × several rows), so it
          deliberately skips the per-glyph feTurbulence/feDisplacementMap bleed
          the single-glyph/word surfaces use — many concurrent filters on a live,
          click-replayable sheet is a real cost for a whisper of edge wicking.
          The mask + settle are shared; the bleed is the one part it opts out of. */}
      <Box
        component="g"
        key={`ink-${run}`}
        mask={`url(#${maskId})`}
        pointerEvents="none"
        sx={inkGroupSx({ animate, writeEndMs: writeEnd, settleMs: SHEET_SETTLE_MS })}
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
  rowW: number; // shared template width (the widest row's content), keeps scale constant
  geomByKey: Map<string, GlyphGeom>;
  guides: GlyphRenderData['template_guides'];
  width: number; // rendered px width (sized exactly so the lines never distort)
  reducedMotion: boolean;
}

// One ruled row: the four full-width Lineatur lines + the row's written glyphs.
function SheetRow({ row, rowOffset, rowW, geomByKey, guides, width, reducedMotion }: RowProps) {
  const vbY = -(guides.ascender + PAD_Y);
  const vbH = guides.ascender - guides.descender + 2 * PAD_Y;
  const lines = [
    { y: guides.baseline, opacity: 1, dash: undefined }, // Grundlinie — the writing line
    { y: guides.midband, opacity: 0.65, dash: '4 3' }, // Mittellinie (dashes are px: non-scaling)
    { y: guides.ascender, opacity: 0.45, dash: undefined }, // Oberlinie
    { y: guides.descender, opacity: 0.45, dash: undefined }, // Unterlinie
  ];

  // "Gleich pro Zeile": every letter in a row is separated by the SAME gap, and
  // a full row is justified to fill the shared width — so the inter-letter gap is
  // constant within a row but differs between rows (a row of wide letters gets a
  // smaller gap than a row of narrow ones, and every full row spans edge to
  // edge). The final short row keeps the natural minimum GAP, left-aligned, so
  // its few letters are not stretched across the whole line.
  const placeable = row.filter((s): s is MarkedSlot & { key: string } => !!s.key && geomByKey.has(s.key));
  const n = placeable.length;
  let gap = GAP;
  if (n > 1 && n === LETTERS_PER_ROW) {
    const ink = placeable.reduce((sum, s) => {
      const g = geomByKey.get(s.key)!;
      return sum + (g.maxX - g.minX);
    }, 0);
    gap = Math.max(GAP, (rowW - 2 * LEAD - ink) / (n - 1));
  }

  // Lay each glyph by its left ink edge at the running cursor, advancing by the
  // glyph's own width + this row's gap.
  const placed: { slot: MarkedSlot; geom: GlyphGeom; glyphX: number; cellX: number; cellW: number; orderIndex: number }[] = [];
  let cursor = LEAD;
  row.forEach((slot, i) => {
    const geom = slot.key ? geomByKey.get(slot.key) : undefined;
    if (!slot.key || !geom) return; // gap (untraced) — no slot reserved
    const glyphW = geom.maxX - geom.minX;
    placed.push({
      slot,
      geom,
      glyphX: cursor,
      cellX: cursor - gap / 2, // hover cell spans the ink (lands at glyphX) + half a gap each side
      cellW: glyphW + gap,
      orderIndex: rowOffset + i,
    });
    cursor += glyphW + gap;
  });

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
      {placed.map((p) => (
        <SheetGlyph
          key={p.slot.key ?? p.orderIndex}
          geom={p.geom}
          glyph={p.slot.glyph}
          glyphX={p.glyphX}
          cellX={p.cellX}
          cellW={p.cellW}
          vbY={vbY}
          vbH={vbH}
          orderIndex={p.orderIndex}
          reducedMotion={reducedMotion}
        />
      ))}
    </Box>
  );
}

interface Props {
  rows: MarkedSlot[][]; // chart-row-grouped marked letters (gaps = null key)
  ratio: number[]; // style_ratio (Oberlänge:Mittellänge:Unterlänge)
}

export function WrittenSheet({ rows, ratio }: Props) {
  const reducedMotion = usePrefersReducedMotion();
  const [dataByKey, setDataByKey] = useState<Map<string, GlyphRenderData | null> | null>(null);
  // Batch fetch failed (after the cold-start retries): keep the empty ruling and
  // show a visible error + retry instead of a silently blank sheet. The nonce
  // re-runs the fetch effect on retry.
  const [loadError, setLoadError] = useState(false);
  const [fetchNonce, setFetchNonce] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerW, setContainerW] = useState(0);

  const keys = useMemo(
    () => rows.flat().map((s) => s.key).filter((k): k is string => !!k),
    [rows],
  );

  // Fetch every written letter's render payload — one batch request through the
  // shared render cache (gaps need no fetch, missing letters resolve to null).
  useEffect(() => {
    let cancelled = false;
    setDataByKey(null);
    setLoadError(false);
    fetchRenderGlyphs(CONFIG.sourceId, keys)
      .then((m) => {
        if (!cancelled) setDataByKey(m);
      })
      .catch(() => {
        if (!cancelled) {
          setDataByKey(new Map()); // only the lineature renders behind the notice
          setLoadError(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [keys, fetchNonce]);

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

  // Re-flow the written letters into uniform rows of LETTERS_PER_ROW: drop the
  // gaps (untraced letters) so the spacing is even with no holes, and ignore the
  // chart's own row breaks — every row holds the same count at the same scale.
  const sheetRows = useMemo(() => {
    const written = rows.flat().filter((s): s is MarkedSlot & { key: string } => s.key !== null);
    const chunks: MarkedSlot[][] = [];
    for (let i = 0; i < written.length; i += LETTERS_PER_ROW) {
      chunks.push(written.slice(i, i + LETTERS_PER_ROW));
    }
    return chunks;
  }, [rows]);

  // One shared template width for every row = the widest row's flowed content
  // (LEAD + Σ glyphW + gaps + LEAD), so all rows keep one constant glyph scale
  // and a short last row simply leaves trailing space. Until the glyph widths
  // resolve, fall back to a sensible average so the ruling draws immediately.
  const rowW = useMemo(() => {
    let max = 0;
    for (const row of sheetRows) {
      let ink = 0;
      let n = 0;
      for (const slot of row) {
        const geom = slot.key ? geomByKey.get(slot.key) : undefined;
        if (!geom) continue;
        ink += geom.maxX - geom.minX;
        n += 1;
      }
      if (n === 0) continue; // a row with no resolved glyph contributes nothing
      const w = 2 * LEAD + ink + (n - 1) * GAP; // LEAD + glyphs + gaps + LEAD
      if (w > max) max = w;
    }
    // Until any glyph geometry resolves, max stays 0 → keep the pre-load fallback
    // so the ruling draws at a sensible scale instead of collapsing.
    return max > 0 ? max : FALLBACK_ROW_W;
  }, [sheetRows, geomByKey]);
  const loading = dataByKey === null;

  return (
    <Box ref={containerRef} sx={{ width: '100%' }}>
      {sheetRows.length === 0 ? (
        <Typography sx={{ color: paper.inkSoft }}>{de.tafel.empty}</Typography>
      ) : (
        // The ruled rows render at once with the loader pulsing in the middle;
        // the diagnostics load together (one Promise.all), then every glyph
        // writes itself in at once in the staggered left-to-right cascade.
        containerW > 0 && (
          <Box sx={{ position: 'relative' }}>
            <Stack spacing={1}>
              {sheetRows.map((row, ri) => (
                <SheetRow
                  key={ri}
                  row={row}
                  rowOffset={ri * LETTERS_PER_ROW}
                  rowW={rowW}
                  geomByKey={geomByKey}
                  guides={guides}
                  width={containerW}
                  reducedMotion={reducedMotion}
                />
              ))}
            </Stack>
            {loadError && (
              // Fetch failed — say so in the ruling instead of leaving the sheet
              // silently blank, with a retry that re-runs the batch fetch.
              <Box
                role="alert"
                sx={{
                  position: 'absolute',
                  inset: 0,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 1.5,
                  textAlign: 'center',
                  px: 2,
                }}
              >
                <Typography variant="body2" sx={{ color: paper.inkSoft }}>
                  {de.tafel.loadError}
                </Typography>
                <Button variant="outlined" size="small" onClick={() => setFetchNonce((n) => n + 1)}>
                  {de.common.boot.retry}
                </Button>
              </Box>
            )}
            {loading && (
              <Box
                role="status"
                aria-live="polite"
                sx={{
                  position: 'absolute',
                  inset: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 1,
                  pointerEvents: 'none',
                }}
              >
                {/* visually-hidden text so the status region has a name SRs announce */}
                <Box component="span" sx={visuallyHidden}>
                  {de.tafel.loading}
                </Box>
                {[0, 1, 2].map((i) => (
                  <Box
                    key={i}
                    sx={{
                      width: 9,
                      height: 9,
                      borderRadius: '50%',
                      bgcolor: paper.viridian,
                      opacity: reducedMotion ? 0.7 : undefined,
                      animation: reducedMotion
                        ? undefined
                        : `${loaderPulse} 1.2s ease-in-out ${i * 0.16}s infinite`,
                    }}
                  />
                ))}
              </Box>
            )}
          </Box>
        )
      )}
    </Box>
  );
}
