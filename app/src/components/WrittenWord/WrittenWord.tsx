// WrittenWord — writes an arbitrary word or line "as written": each glyph's
// filled Sütterlin silhouette plus the generated connecting strokes (Übergänge),
// revealed stroke-by-stroke in writing order across the whole word. The
// single-glyph sibling is `WrittenGlyph`; this one composes many.
//
// Pipeline: `shapeText` turns the string into glyph slots (positions, long-s,
// ligatures); we fetch each glyph's `DiagnosticData` (centerlines + silhouette
// rings + entry/exit); `composeWord` lays them along one baseline and generates
// the connectors; we fill every silhouette + stroke every connector inside one
// group, then mask it with a wide path swept along each centerline via an
// animated `stroke-dashoffset`. The group carries BOTH fill (glyph silhouettes)
// and stroke (connectors) so the iron-gall ink settle ages the whole word at
// once. Coordinates: template space (baseline = 0, y up); SVG y points down, so
// y is negated in the rendered data.

import ReplayIcon from '@mui/icons-material/Replay';
import { Box, CircularProgress, IconButton, keyframes } from '@mui/material';
import { useCallback, useEffect, useId, useMemo, useState } from 'react';

import { CONFIG } from '@/global-config';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion';
import { composeWord, type ComposedWord, type Point } from '@/domain/compose';
import { glyphKeysOf, shapeText } from '@/domain/shaping';
import { ApiError, getDiagnostic, type DiagnosticData } from '@/lib/api';
import { ringsToPathD } from '@/lib/svg';
import { de } from '@/locales';
import { inkState, schulheft } from '@/styles/paper';

const reveal = keyframes`from { stroke-dashoffset: 1; } to { stroke-dashoffset: 0; }`;
// Iron-gall settle: fresh blue-black → oxidized brown after the write-in ends.
const inkSettle = keyframes`
  from { fill: ${inkState.fresh}; stroke: ${inkState.fresh}; }
  to { fill: ${inkState.oxidized}; stroke: ${inkState.oxidized}; }
`;
const SETTLE_MS = 1800;
const PEN_PAUSE_MS = 110; // pause at a within-glyph Absetzen so a lift reads as a lift
const MIN_ITEM_MS = 120;

const GUIDE = schulheft.rulingBlueFaded;

// Diagnostics are a backend compute; cache the in-flight/resolved promise per
// (source, glyph) so a repeated letter — or a second WrittenWord on the page —
// never refetches. A 404 (no canonical) resolves to null, not a throw.
const cache = new Map<string, Promise<DiagnosticData | null>>();
function fetchGlyph(sourceId: string, key: string): Promise<DiagnosticData | null> {
  const id = `${sourceId}|${key}`;
  let p = cache.get(id);
  if (!p) {
    p = getDiagnostic(sourceId, key).catch((e) => {
      if (e instanceof ApiError && e.status === 404) return null;
      cache.delete(id); // a transient error shouldn't be cached — allow a retry
      throw e;
    });
    cache.set(id, p);
  }
  return p;
}

function chordLength(points: Point[]): number {
  let total = 0;
  for (let i = 1; i < points.length; i++) {
    total += Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]);
  }
  return total;
}

function pathD(points: Point[]): string {
  return points.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x},${-y}`).join(' ');
}

interface Props {
  text: string;
  sourceId?: string;
  // Target rendered height in px (width follows the word's aspect, capped).
  height?: number;
  // Total writing time across all strokes (excluding inter-stroke pauses).
  durationMs?: number;
  maxWidth?: number;
  surfaceBg?: string;
  // Draw the faint baseline + midband ruling under the word.
  showLineature?: boolean;
  // Show the replay button (bottom-right).
  showReplay?: boolean;
  // After fetch + compose: the glyph_keys that had no canonical (empty = all
  // rendered) and how many strokes were placed. Lets the hero fall back.
  onResolved?: (info: { missing: string[]; rendered: number }) => void;
  // A non-404 fetch error (e.g. cold-start retries exhausted).
  onError?: (e: unknown) => void;
}

const MAX_W = 640;

export function WrittenWord({
  text,
  sourceId = CONFIG.sourceId,
  height = 160,
  durationMs = 2600,
  maxWidth = MAX_W,
  surfaceBg = 'transparent',
  showLineature = true,
  showReplay = false,
  onResolved,
  onError,
}: Props) {
  const reducedMotion = usePrefersReducedMotion();
  const uid = useId();
  const slots = useMemo(() => shapeText(text), [text]);
  const [dataByKey, setDataByKey] = useState<Map<string, DiagnosticData | null> | null>(null);
  const [run, setRun] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setDataByKey(null);
    const keys = glyphKeysOf(slots);
    Promise.all(keys.map((k) => fetchGlyph(sourceId, k).then((d) => [k, d] as const)))
      .then((entries) => {
        if (cancelled) return;
        setDataByKey(new Map(entries));
      })
      .catch((e) => {
        if (!cancelled) onError?.(e);
      });
    return () => {
      cancelled = true;
    };
    // onError intentionally omitted: a fresh closure each render must not refetch.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slots, sourceId]);

  const composed: ComposedWord | null = useMemo(() => {
    if (!dataByKey) return null;
    return composeWord(slots.map((s) => ({ key: s.key, space: s.space, data: s.key ? dataByKey.get(s.key) ?? null : null })));
  }, [dataByKey, slots]);

  useEffect(() => {
    if (composed) onResolved?.({ missing: composed.missing, rendered: composed.items.length });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [composed]);

  const geom = useMemo(() => {
    if (!composed || !composed.items.length) return null;
    const { bounds, guides, items } = composed;
    const pad = 0.15;
    const minX = bounds.minX - pad;
    const vbW = bounds.maxX - bounds.minX + 2 * pad;
    const yHi = showLineature && guides ? Math.max(guides.ascender, bounds.maxY) : bounds.maxY + pad;
    const yLo = showLineature && guides ? Math.min(guides.descender, bounds.minY, 0) : bounds.minY - pad;
    const vbY = -yHi;
    const vbH = Math.max(0.5, yHi - yLo);

    const lengths = items.map((it) => chordLength(it.centerline));
    const total = lengths.reduce((s, l) => s + l, 0) || 1;
    let cursor = 0;
    const timing = items.map((_, i) => {
      const dur = Math.max(MIN_ITEM_MS, (lengths[i] / total) * durationMs);
      const delay = cursor + (items[i].lift ? PEN_PAUSE_MS : 0);
      cursor = delay + dur;
      return { dur, delay };
    });
    return { minX, vbW, vbY, vbH, items, guides, timing, writeEndMs: cursor };
  }, [composed, showLineature, durationMs]);

  const replay = useCallback(() => setRun((r) => r + 1), []);

  if (!composed || !geom) {
    return (
      <Box sx={{ display: 'inline-flex', minHeight: height, alignItems: 'center', justifyContent: 'center' }}>
        {composed && !composed.items.length ? null : <CircularProgress size={26} />}
      </Box>
    );
  }

  const { minX, vbW, vbY, vbH, items, guides, timing, writeEndMs } = geom;
  let displayW = (height * vbW) / vbH;
  let finalH = height;
  if (displayW > maxWidth) {
    finalH = (maxWidth * vbH) / vbW;
    displayW = maxWidth;
  }
  const maskId = `word-${uid.replace(/[^a-zA-Z0-9_-]/g, '_')}-${run}`;
  const animate = !reducedMotion;

  return (
    <Box sx={{ position: 'relative', display: 'inline-flex' }}>
      <svg
        width={displayW}
        height={finalH}
        viewBox={`${minX} ${vbY} ${vbW} ${vbH}`}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label={text}
        style={{ display: 'block', background: surfaceBg, maxWidth: '100%', overflow: 'visible' }}
      >
        <defs>
          <filter id={`${maskId}-bleed`} x="-3%" y="-5%" width="106%" height="110%">
            <feTurbulence type="fractalNoise" baseFrequency="6" numOctaves="2" seed="7" result="noise" />
            <feDisplacementMap in="SourceGraphic" in2="noise" scale="0.016" xChannelSelector="R" yChannelSelector="G" />
          </filter>
          <mask id={maskId} maskUnits="userSpaceOnUse" x={minX} y={vbY} width={vbW} height={vbH}>
            <rect x={minX} y={vbY} width={vbW} height={vbH} fill="black" />
            {items.map((it, i) => (
              <Box
                component="path"
                key={`${run}-${i}`}
                d={pathD(it.centerline)}
                fill="none"
                stroke="#fff"
                strokeWidth={it.maskWidth}
                strokeLinecap="round"
                strokeLinejoin="round"
                pathLength={1}
                strokeDasharray={1}
                sx={{
                  strokeDashoffset: animate ? 1 : 0,
                  animation: animate ? `${reveal} ${timing[i].dur}ms linear ${timing[i].delay}ms forwards` : undefined,
                }}
              />
            ))}
          </mask>
        </defs>

        {showLineature && guides && (
          <>
            <line x1={minX} y1={-guides.baseline} x2={minX + vbW} y2={-guides.baseline} stroke={GUIDE} strokeWidth={0.012} />
            <line
              x1={minX}
              y1={-guides.midband}
              x2={minX + vbW}
              y2={-guides.midband}
              stroke={GUIDE}
              strokeOpacity={0.55}
              strokeWidth={0.012}
              strokeDasharray="0.08 0.06"
            />
          </>
        )}

        <Box
          component="g"
          key={`ink-${run}`}
          mask={`url(#${maskId})`}
          filter={`url(#${maskId}-bleed)`}
          sx={{
            fill: animate ? inkState.fresh : inkState.oxidized,
            stroke: animate ? inkState.fresh : inkState.oxidized,
            animation: animate ? `${inkSettle} ${SETTLE_MS}ms ease ${writeEndMs}ms forwards` : undefined,
          }}
        >
          {items.map((it, i) =>
            it.rings ? (
              // Glyph silhouette: filled (inherits group fill), never stroked.
              <path key={i} d={ringsToPathD(it.rings, true)} fillRule="evenodd" stroke="none" />
            ) : (
              // Connector: stroked capsule (inherits group stroke), never filled.
              <path
                key={i}
                d={pathD(it.centerline)}
                fill="none"
                strokeWidth={it.strokeWidth}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            ),
          )}
        </Box>
      </svg>

      {animate && showReplay && (
        <IconButton
          size="small"
          onClick={replay}
          aria-label={de.common.writtenGlyph.replay}
          sx={{ position: 'absolute', bottom: 4, right: 4, color: 'text.disabled', '&:hover': { color: 'text.secondary' } }}
        >
          <ReplayIcon fontSize="small" />
        </IconButton>
      )}
    </Box>
  );
}
