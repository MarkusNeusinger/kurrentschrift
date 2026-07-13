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

import { Box, CircularProgress } from '@mui/material';
import { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react';

import { CONFIG } from '@/global-config';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion';
import { useStrokeReveal } from '@/hooks/useStrokeReveal';
import { fetchRenderWord, type ComposedWordOut } from '@/lib/api';
import {
  allocateDurations,
  sequenceReveal,
  strokeTimeProfile,
  PEN_PAUSE_MS,
  SETTLE_MS,
  WORD_MAX_W,
  WORD_MIN_ITEM_MS,
  WORD_WRITE_MS,
} from '@/lib/strokeTiming';
import { InkBleedFilter, InkGuides, RevealMask, ReplayButton, inkGroupSx } from '@/components/inkReveal';
import { polylineToPathD, ringsToPathD } from '@/lib/svg';

// Composition happens server-side and is cached in the shared render cache
// (`@/lib/api/renderCache` → fetchRenderWord), so a replay, a re-mount or a
// second WrittenWord on the page never refetches — one cacheable request per
// text across the whole session.

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

export function WrittenWord({
  text,
  sourceId = CONFIG.sourceId,
  height = 160,
  durationMs = WORD_WRITE_MS,
  maxWidth = WORD_MAX_W,
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
    fetchRenderWord(sourceId, normalized)
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
    // keyframes per item) and isochrony allocates durations sublinearly. A short
    // pen-lift pause precedes only the items flagged as following an Absetzen.
    const profiles = items.map((it) => strokeTimeProfile(it.centerline));
    const durations = allocateDurations(
      profiles.map((p) => p.weight),
      durationMs,
      WORD_MIN_ITEM_MS,
    );
    const { timing, writeEndMs } = sequenceReveal(profiles, durations, {
      leadPause: (i) => (items[i].lift ? PEN_PAUSE_MS : 0),
    });
    return { minX, vbW, vbY, vbH, items, guides, timing, writeEndMs };
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
          <InkBleedFilter
            id={`${maskId}-bleed`}
            scale={0.016}
            inset={{ x: '-3%', y: '-5%', width: '106%', height: '110%' }}
          />
          <RevealMask
            id={maskId}
            bounds={{ x: minX, y: vbY, width: vbW, height: vbH }}
            strokes={items.map((it) => ({ centerline: it.centerline, maskWidth: it.mask_width }))}
            pathRefs={maskPathRefs}
            animate={animate}
            runKey={run}
          />
        </defs>

        {showLineature && guides && (
          <InkGuides minX={minX} width={vbW} baseline={guides.baseline} midband={guides.midband} />
        )}

        <Box
          component="g"
          key={`ink-${run}`}
          mask={`url(#${maskId})`}
          filter={`url(#${maskId}-bleed)`}
          sx={inkGroupSx({ animate, writeEndMs, settleMs: SETTLE_MS, inkColor, withStroke: true })}
        >
          {items.map((it, i) =>
            it.rings ? (
              // Glyph silhouette: filled (inherits group fill), never stroked.
              <path key={i} d={ringsToPathD(it.rings, true)} fillRule="evenodd" stroke="none" />
            ) : (
              // Connector: stroked capsule (inherits group stroke), never filled.
              <path
                key={i}
                d={polylineToPathD(it.centerline)}
                fill="none"
                strokeWidth={it.stroke_width}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            ),
          )}
        </Box>
      </svg>

      {animate && showReplay && <ReplayButton onClick={replay} />}
    </Box>
  );
}
