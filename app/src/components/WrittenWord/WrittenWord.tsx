// WrittenWord — writes an arbitrary word or line "as written": each glyph's
// filled Sütterlin silhouette plus the generated connecting strokes (Übergänge),
// revealed stroke-by-stroke in writing order across the whole word. The
// single-glyph sibling is `WrittenGlyph`; this one renders many.
//
// Composition happens SERVER-SIDE (GET /write/word → core/shaping.py +
// core/compose.py): shaping (long-s, ligatures incl. the decompose fallback),
// baseline placement and the generated connectors arrive as flat draw items in
// writing order — ONE cacheable request per text. This component only renders:
// fill every silhouette + stroke every connector inside one group, then mask it
// with a wide path swept along each centerline via an animated
// `stroke-dashoffset`. The group carries BOTH fill (glyph silhouettes) and
// stroke (connectors) so the iron-gall ink settle ages the whole word at once.
// Coordinates: template space (baseline = 0, y up); SVG y points down, so y is
// negated in the rendered data.

import ReplayIcon from '@mui/icons-material/Replay';
import { Box, CircularProgress, IconButton, keyframes } from '@mui/material';
import { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react';

import { CONFIG } from '@/global-config';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion';
import { useStrokeReveal } from '@/hooks/useStrokeReveal';
import { getWriteWord, type ComposedWordOut } from '@/lib/api';
import { allocateDurations, strokeTimeProfile } from '@/lib/strokeTiming';
import { ringsToPathD } from '@/lib/svg';
import { de } from '@/locales';
import { inkState, schulheft } from '@/styles/paper';
// Iron-gall settle: fresh blue-black → oxidized brown after the write-in ends.
const inkSettle = keyframes`
  from { fill: ${inkState.fresh}; stroke: ${inkState.fresh}; }
  to { fill: ${inkState.oxidized}; stroke: ${inkState.oxidized}; }
`;
const SETTLE_MS = 1800;
const PEN_PAUSE_MS = 110; // pause at a within-glyph Absetzen so a lift reads as a lift
const MIN_ITEM_MS = 120;

const GUIDE = schulheft.rulingBlueFaded;

// Composing is a backend compute; cache the in-flight/resolved promise per
// (source, text) so a replay, a re-mount or a second WrittenWord on the page
// never refetches. Transient errors evict so a retry can succeed; the server
// also sets Cache-Control, so even a fresh page load hits the browser cache.
// Live typing on /federprobe produces many distinct intermediate texts, so the
// cache is FIFO-capped — evicted entries just refetch (usually straight from
// the browser cache).
const CACHE_MAX = 64;
const cache = new Map<string, Promise<ComposedWordOut>>();
function fetchComposed(sourceId: string, text: string): Promise<ComposedWordOut> {
  const id = `${sourceId}|${text}`;
  let p = cache.get(id);
  if (!p) {
    p = getWriteWord(sourceId, text, { retries: 3 }).catch((e) => {
      cache.delete(id);
      throw e;
    });
    if (cache.size >= CACHE_MAX) {
      cache.delete(cache.keys().next().value as string); // FIFO: drop the oldest entry
    }
    cache.set(id, p);
  }
  return p;
}

type Point = [number, number];

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
  // Solid ink colour override (fill + connector stroke). When set, the iron-gall
  // settle is skipped and the word holds one tone — the quiz comparison tints the
  // learner's wrong word red and the correct word near-black.
  inkColor?: string;
  // Whether to play the write-in (and settle). Defaults to true; false renders
  // the word already fully drawn (the post-answer comparison). ANDed with the
  // reduced-motion preference.
  animate?: boolean;
  // Draw the faint baseline + midband ruling under the word.
  showLineature?: boolean;
  // Show the replay button (bottom-right).
  showReplay?: boolean;
  // After the composed word arrives: the glyph_keys that had no canonical
  // (empty = all rendered) and how many strokes were placed. Lets callers flag
  // the letters or fall back.
  onResolved?: (info: { missing: string[]; rendered: number }) => void;
  // A fetch error (e.g. cold-start retries exhausted).
  onError?: (e: unknown) => void;
  // Accessible name of the rendered SVG. Defaults to the written text; the quiz
  // passes a neutral label so the image does not leak the solution word to the
  // DOM/screen reader before the answer.
  ariaLabel?: string;
}

const MAX_W = 640;

export function WrittenWord({
  text,
  sourceId = CONFIG.sourceId,
  height = 160,
  durationMs = 2600,
  maxWidth = MAX_W,
  surfaceBg = 'transparent',
  inkColor,
  animate: animateProp = true,
  showLineature = true,
  showReplay = false,
  onResolved,
  onError,
  ariaLabel,
}: Props) {
  const reducedMotion = usePrefersReducedMotion();
  const uid = useId();
  // Mirror the server's normalisation so equal words share one cache/URL entry.
  const normalized = useMemo(() => text.normalize('NFC').trim(), [text]);
  const [composed, setComposed] = useState<ComposedWordOut | null>(null);
  const [run, setRun] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setComposed(null);
    if (!normalized) {
      // Nothing to write (the server 422s on empty text) — settle on an empty
      // composition so callers see `missing: []` instead of a spinner forever.
      setComposed({ text: '', items: [], bounds: { min_x: 0, max_x: 1, min_y: 0, max_y: 1 }, guides: null, missing: [] });
      return;
    }
    fetchComposed(sourceId, normalized)
      .then((c) => {
        if (!cancelled) setComposed(c);
      })
      .catch((e) => {
        if (!cancelled) onError?.(e);
      });
    return () => {
      cancelled = true;
    };
    // onError intentionally omitted: a fresh closure each render must not refetch.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [normalized, sourceId]);

  useEffect(() => {
    if (composed) onResolved?.({ missing: composed.missing, rendered: composed.items.length });
    // onResolved intentionally omitted: report only when the composition changes,
    // not when a parent passes a fresh callback identity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [composed]);

  const geom = useMemo(() => {
    if (!composed || !composed.items.length) return null;
    const { bounds, guides, items } = composed;
    const pad = 0.15;
    const minX = bounds.min_x - pad;
    const vbW = bounds.max_x - bounds.min_x + 2 * pad;
    const yHi = showLineature && guides ? Math.max(guides.ascender, bounds.max_y) : bounds.max_y + pad;
    const yLo = showLineature && guides ? Math.min(guides.descender, bounds.min_y, 0) : bounds.min_y - pad;
    const vbY = -yHi;
    const vbH = Math.max(0.5, yHi - yLo);

    // Human kinematics instead of a constant sweep (lib/strokeTiming): the
    // two-thirds power law slows the front in curves (non-linear dashoffset
    // keyframes per item) and isochrony allocates durations sublinearly.
    const profiles = items.map((it) => strokeTimeProfile(it.centerline));
    const durations = allocateDurations(
      profiles.map((p) => p.weight),
      durationMs,
      MIN_ITEM_MS,
    );
    let cursor = 0;
    const timing = items.map((_, i) => {
      const dur = durations[i];
      const delay = cursor + (items[i].lift ? PEN_PAUSE_MS : 0);
      cursor = delay + dur;
      return { dur, delay, arcAtTime: profiles[i].arcAtTime };
    });
    return { minX, vbW, vbY, vbH, items, guides, timing, writeEndMs: cursor };
  }, [composed, showLineature, durationMs]);

  const replay = useCallback(() => setRun((r) => r + 1), []);

  const animate = animateProp && !reducedMotion;
  // WAAPI drives the per-path dashoffset (scoped to the elements, no global
  // @keyframes growth); hooks run unconditionally, before the early return.
  const maskPathRefs = useRef<Array<SVGPathElement | null>>([]);
  useStrokeReveal(maskPathRefs, geom?.timing ?? [], animate && !!geom, `${run}|${geom ? 'g' : ''}`);

  if (!composed || !geom) {
    return (
      <Box sx={{ display: 'inline-flex', minHeight: height, alignItems: 'center', justifyContent: 'center' }}>
        {composed && !composed.items.length ? null : <CircularProgress size={26} />}
      </Box>
    );
  }

  const { minX, vbW, vbY, vbH, items, guides, writeEndMs } = geom;
  let displayW = (height * vbW) / vbH;
  let finalH = height;
  if (displayW > maxWidth) {
    finalH = (maxWidth * vbH) / vbW;
    displayW = maxWidth;
  }
  const maskId = `word-${uid.replace(/[^a-zA-Z0-9_-]/g, '_')}-${run}`;

  return (
    <Box sx={{ position: 'relative', display: 'inline-flex' }}>
      <svg
        width={displayW}
        height={finalH}
        viewBox={`${minX} ${vbY} ${vbW} ${vbH}`}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label={ariaLabel ?? text}
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
              <path
                key={`${run}-${i}`}
                ref={(el) => {
                  maskPathRefs.current[i] = el;
                }}
                d={pathD(it.centerline)}
                fill="none"
                stroke="#fff"
                strokeWidth={it.mask_width}
                strokeLinecap="round"
                strokeLinejoin="round"
                pathLength={1}
                strokeDasharray={1}
                style={{ strokeDashoffset: animate ? 1 : 0 }}
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
            // A fixed inkColor (the comparison's red/black) skips the settle and
            // holds one tone; otherwise the iron-gall fresh→oxidized settle plays.
            fill: inkColor ?? (animate ? inkState.fresh : inkState.oxidized),
            stroke: inkColor ?? (animate ? inkState.fresh : inkState.oxidized),
            animation:
              animate && !inkColor ? `${inkSettle} ${SETTLE_MS}ms ease ${writeEndMs}ms forwards` : undefined,
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
                strokeWidth={it.stroke_width}
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
