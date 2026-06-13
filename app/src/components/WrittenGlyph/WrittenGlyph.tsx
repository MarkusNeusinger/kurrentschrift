// WrittenGlyph — renders a canonical glyph "as written": the filled Schwellzug
// silhouette (from the Loth-derived ductus) revealed stroke-by-stroke in the
// order the pen drew it. Used as the quiz prompt instead of a static crop.
//
// Technique: the backend (`core.pipeline.diagnostic_for_glyph`) gives us, per
// pen-stroke, the filled silhouette — preferred `outline_paths` (capsule-union
// rings: exterior + holes, drawn as one evenodd path so loop counters stay
// open; legacy ribbon `outline_polygons` as fallback) — AND the matching
// `centerlines_template` (the spine of each silhouette, in writing order). We
// fill the silhouettes, then mask them with a wide stroked path swept along
// each centerline via an animated `stroke-dashoffset` — so the ink appears
// along the actual pen path, lifting between strokes (no bar bridging an
// Absetzen). A pen lift is a real gap because each stroke is its own
// silhouette + its own centerline.
//
// Coordinates: template space (baseline=0, midband=1, y up). SVG y points down,
// so we negate y in the rendered data (rather than a flipped <g>) to keep the
// mask coordinates aligned with the filled polygons without a nested transform.

import ReplayIcon from '@mui/icons-material/Replay';
import { Alert, Box, CircularProgress, IconButton, keyframes } from '@mui/material';
import { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react';

import { CONFIG } from '@/global-config';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion';
import { ApiError, getDiagnostic, type DiagnosticData } from '@/lib/api';
import { ringsToPathD, type Ring } from '@/lib/svg';
import { de } from '@/locales';
import { inkState, schulheft } from '@/styles/paper';

// Reveal a dashed path (pathLength=1, dasharray=1): offset 1 hides it, 0 draws it.
const reveal = keyframes`from { stroke-dashoffset: 1; } to { stroke-dashoffset: 0; }`;

// Iron-gall ink settle: German school ink wrote blue-black and oxidized to
// near-black (Reichs-Tintenprüfung 1888/1912) — compressed here from weeks to
// seconds after the write-in completes. Knowingly expressive synthesis.
const inkSettle = keyframes`from { fill: ${inkState.fresh}; } to { fill: ${inkState.oxidized}; }`;
const SETTLE_MS = 1800;

// Rendering colours of this work surface. The crop box is one of the neutral
// surfaces that deliberately opt out of the paper identity (style-guide §8) —
// these are local rendering constants, not theme tokens.
const SURFACE_BG = '#fff'; // neutral white crop ground (binding)
// Context guides in the faint exercise-book blue (schulheft tokens) so the
// glyph sits on a whisper of period ruling, matching the fresh-ink narrative
// of this surface; the midband stays the quieter of the two via opacity.
const GUIDE_BASELINE = schulheft.rulingBlueFaded;
const GUIDE_MIDBAND = schulheft.rulingBlueFaded;
const GUIDE_MIDBAND_OPACITY = 0.55;

// Diagnostics are a backend compute (skeleton extraction); cache per glyph so
// replays and repeat questions don't refetch. One entry per glyph, stamped
// with the canonical version (`bust`) it was fetched under: a mismatching
// version overwrites the entry instead of forking the key, so the quiz
// benefits from the admin's fresh fetch and stale payloads can't accumulate.
// `data: null` records a 404 (no ductus).
interface CacheEntry {
  bust: number | null;
  data: DiagnosticData | null;
}
const cache = new Map<string, CacheEntry>();

// A caller without a version accepts whatever is cached; a versioned caller
// (the admin dialog after a re-trace) requires its exact version.
function cachedEntry(glyphKey: string, bust?: number): CacheEntry | undefined {
  const entry = cache.get(glyphKey);
  if (entry === undefined || (bust != null && entry.bust !== bust)) return undefined;
  return entry;
}

function chordLength(points: Array<[number, number]>): number {
  let total = 0;
  for (let i = 1; i < points.length; i++) {
    total += Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]);
  }
  return total;
}

// Polyline as an SVG path `d`, negating y (template y is up, SVG y is down).
function pathD(points: Array<[number, number]>): string {
  return points.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x},${-y}`).join(' ');
}

interface Props {
  glyphKey: string;
  // Total writing time across all strokes (excluding inter-stroke pauses).
  durationMs?: number;
  // Target rendered height in px (width follows the glyph's aspect, capped).
  height?: number;
  // Frame the viewBox to the glyph's own ink extent instead of the full
  // ascender..descender lineature, so a lowercase letter fills the box (the
  // comparison view renders it the same size as the tight chart crop).
  tight?: boolean;
  // Override the rendered-width cap (default MAX_W). Pass a large value to let
  // height drive the size unconditionally (the comparison view wants big, equal
  // sizes regardless of glyph aspect).
  maxWidth?: number;
  // Canonical version stamp: require a cache entry of exactly this version,
  // refetching otherwise (the admin dialog after a re-trace). The quiz never
  // passes it and accepts any cached entry.
  cacheBust?: number;
  // Already-fetched diagnostic payload — skips the internal fetch entirely
  // (the Diagnose dialog shares one payload across its stages).
  data?: DiagnosticData;
  // Called if the glyph has no canonical yet (404) so the caller can fall back to
  // the static crop. The component itself renders nothing once unavailable.
  onUnavailable?: () => void;
}

const PEN_PAUSE_MS = 150; // pause at each Absetzen so the lift reads as a lift
const MAX_W = 300;

export function WrittenGlyph({ glyphKey, durationMs = 1500, height = 220, tight = false, maxWidth, cacheBust, data: dataProp, onUnavailable }: Props) {
  const reducedMotion = usePrefersReducedMotion();
  const uid = useId();
  const [fetched, setFetched] = useState<DiagnosticData | null>(() => cachedEntry(glyphKey, cacheBust)?.data ?? null);
  const data = dataProp ?? fetched;
  const [error, setError] = useState<string | null>(null);
  // True once a glyph turns out to have no canonical (404): the component then
  // renders nothing and the caller (onUnavailable) swaps in the crop.
  const [unavailable, setUnavailable] = useState(false);
  // Animation run counter — bumping it remounts the mask paths so the CSS
  // animation restarts (replay button / new mount).
  const [run, setRun] = useState(0);
  const onUnavailableRef = useRef(onUnavailable);
  onUnavailableRef.current = onUnavailable;

  useEffect(() => {
    let cancelled = false;
    // Reset transient state so a stale error/unavailable from a previous glyph
    // can't stick when the same instance is reused for a different glyph_key.
    setError(null);
    setUnavailable(false);
    if (dataProp) {
      // Externally supplied payload: sync the shared cache so other consumers
      // (the quiz) see the freshest canonical without refetching.
      cache.set(glyphKey, { bust: cacheBust ?? null, data: dataProp });
      return;
    }
    const entry = cachedEntry(glyphKey, cacheBust);
    if (entry !== undefined) {
      if (entry.data === null) {
        setUnavailable(true);
        onUnavailableRef.current?.();
      } else {
        setFetched(entry.data);
      }
      return;
    }
    setFetched(null); // spinner while the new glyph loads
    // Public surfaces always render the site-wide source, regardless of which
    // source the admin currently has active.
    getDiagnostic(CONFIG.sourceId, glyphKey)
      .then((d) => {
        if (cancelled) return;
        cache.set(glyphKey, { bust: cacheBust ?? null, data: d });
        setFetched(d);
      })
      .catch((e) => {
        if (e instanceof ApiError && e.status === 404) {
          // No canonical traced yet → let the caller show the crop instead.
          cache.set(glyphKey, { bust: cacheBust ?? null, data: null });
          if (!cancelled) {
            setUnavailable(true);
            onUnavailableRef.current?.();
          }
        } else if (!cancelled) {
          setError(String(e));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [glyphKey, cacheBust, dataProp]);

  const replay = useCallback(() => setRun((r) => r + 1), []);

  const geom = useMemo(() => {
    if (!data) return null;
    const tpl = data.template_guides;
    // Template x has its origin at the ductus' FIRST sample (pipeline x_origin),
    // so a glyph drawn from the right (e.g. K) lies entirely in negative x. Span
    // the viewBox over the real anchor extent instead of assuming [0, advance].
    const xs = data.anchors_template.map((a) => a[0]);
    const ys = data.anchors_template.map((a) => a[1]);
    const hwMax = data.half_widths_template.length ? Math.max(...data.half_widths_template) : 0.05;
    let minX: number;
    let vbW: number;
    let vbY: number;
    let vbH: number;
    if (tight && xs.length) {
      // Tight: frame the glyph's own ink extent (+ a hairline of padding and the
      // baseline) so the letter fills the box at roughly the same scale as the
      // tightly-cropped chart image beside it.
      const pad = hwMax + 0.06;
      const xlo = Math.min(...xs) - pad;
      const xhi = Math.max(...xs) + pad;
      const ylo = Math.min(0, ...ys) - pad;
      const yhi = Math.max(...ys) + pad;
      minX = xlo;
      vbW = xhi - xlo;
      vbY = -yhi;
      vbH = yhi - ylo;
    } else {
      minX = (xs.length ? Math.min(0, ...xs) : 0) - 0.5;
      vbW = (xs.length ? Math.max(0.5, ...xs) : 0.5) + 0.5 - minX;
      vbY = -tpl.ascender - 0.3;
      vbH = tpl.ascender - tpl.descender + 0.6;
    }

    // Preferred: capsule-union rings per stroke (loop counters stay open via
    // evenodd). Legacy ribbon polygons as fallback for older payloads.
    const strokePaths: Ring[][] | null = data.outline_paths?.length ? data.outline_paths : null;
    const polygons = (data.outline_polygons ?? (data.outline_polygon?.length > 2 ? [data.outline_polygon] : [])).filter(
      (p) => p.length > 2,
    );
    // Fall back to a single centerline through all anchors if an older payload
    // carries no per-stroke centerlines.
    const centerlines =
      data.centerlines_template && data.centerlines_template.length
        ? data.centerlines_template
        : [data.anchors_template];

    const maxHalfWidth = data.half_widths_template.length ? Math.max(...data.half_widths_template) : 0.05;
    // Sweep stroke must be at least the full local width (2·half) everywhere; a
    // little extra + round caps cover the spline-normal seams and pen-nib tip.
    const maskWidth = Math.max(0.05, 2.2 * maxHalfWidth);

    // Per-stroke durations proportional to path length so the pen moves at a
    // roughly even pace; each stroke starts after the previous one finishes plus
    // a short pen-lift pause.
    const lengths = centerlines.map(chordLength);
    const totalLen = lengths.reduce((s, l) => s + l, 0) || 1;
    let cursor = 0;
    const timing = centerlines.map((_, i) => {
      const dur = Math.max(250, (lengths[i] / totalLen) * durationMs);
      const delay = cursor;
      cursor += dur + PEN_PAUSE_MS;
      return { dur, delay };
    });

    // End of the writing performance. Includes the trailing PEN_PAUSE_MS on
    // purpose: the settle starts one pen-pause beat after the last stroke
    // finishes, so the lift registers before the ink begins to age.
    const writeEndMs = cursor;

    return { tpl, minX, vbW, vbY, vbH, strokePaths, polygons, centerlines, maskWidth, timing, writeEndMs };
  }, [data, durationMs, tight]);

  if (unavailable) return null;
  if (error) {
    return <Alert severity="error" sx={{ width: '100%' }}>{error}</Alert>;
  }
  if (!data || !geom) {
    return <CircularProgress size={28} />;
  }

  const { tpl, minX, vbW, vbY, vbH, strokePaths, polygons, centerlines, maskWidth, timing, writeEndMs } = geom;
  const displayH = height;
  const maxW = maxWidth ?? MAX_W;
  let displayW = (displayH * vbW) / vbH;
  let finalH = displayH;
  if (displayW > maxW) {
    finalH = (maxW * vbH) / vbW;
    displayW = maxW;
  }
  // useId() namespaces the mask per component instance so two WrittenGlyphs with
  // the same glyph_key on screen at once can't collide on `url(#id)`.
  const maskId = `written-${uid.replace(/[^a-zA-Z0-9_-]/g, '_')}-${run}`;
  const animate = !reducedMotion;

  return (
    <Box sx={{ position: 'relative', display: 'inline-flex' }}>
      <svg
        width={displayW}
        height={finalH}
        viewBox={`${minX} ${vbY} ${vbW} ${vbH}`}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label={de.common.writtenGlyph.ariaLabel}
        // maxWidth lets a wide glyph scale down to a narrow container (mobile /
        // the comparison view's uncapped width) instead of overflowing; the
        // viewBox + preserveAspectRatio shrink the content to fit, centered.
        style={{ display: 'block', background: SURFACE_BG, maxWidth: '100%' }}
      >
        <defs>
          {/* Ink bleed: fibre-wicking displacement on the silhouette group —
              deliberately active during the write-in too (ink wicks the moment
              it touches paper). The viewBox is in template units (x-height = 1),
              so the displacement scale must be tiny — pixel-space example
              values would be wildly off. */}
          <filter id={`${maskId}-bleed`} x="-5%" y="-5%" width="110%" height="110%">
            <feTurbulence type="fractalNoise" baseFrequency="6" numOctaves="2" seed="7" result="noise" />
            <feDisplacementMap in="SourceGraphic" in2="noise" scale="0.018" xChannelSelector="R" yChannelSelector="G" />
          </filter>
          <mask id={maskId} maskUnits="userSpaceOnUse" x={minX} y={vbY} width={vbW} height={vbH}>
            {/* Black hides; the white sweep reveals the silhouette beneath it. */}
            <rect x={minX} y={vbY} width={vbW} height={vbH} fill="black" />
            {centerlines.map((line, i) => (
              <Box
                component="path"
                key={`${run}-${i}`}
                d={pathD(line)}
                fill="none"
                stroke="#fff"
                strokeWidth={maskWidth}
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

        {/* Faint Lineatur (baseline + midband) for reading context. */}
        <line x1={minX} y1={-tpl.baseline} x2={minX + vbW} y2={-tpl.baseline} stroke={GUIDE_BASELINE} strokeWidth={0.012} />
        <line
          x1={minX}
          y1={-tpl.midband}
          x2={minX + vbW}
          y2={-tpl.midband}
          stroke={GUIDE_MIDBAND}
          strokeOpacity={GUIDE_MIDBAND_OPACITY}
          strokeWidth={0.012}
          strokeDasharray="0.08 0.06"
        />

        {/* Filled silhouette, revealed by the swept mask. The group carries the
            fill so the iron-gall settle (fresh blue-black → oxidized) animates
            all strokes at once after the last pen lift; keyed by run so the
            replay button restarts it together with the write-in. */}
        <Box
          component="g"
          key={`ink-${run}`}
          mask={`url(#${maskId})`}
          filter={`url(#${maskId}-bleed)`}
          sx={{
            fill: animate ? inkState.fresh : inkState.oxidized,
            animation: animate ? `${inkSettle} ${SETTLE_MS}ms ease ${writeEndMs}ms forwards` : undefined,
          }}
        >
          {strokePaths
            ? strokePaths.map((rings, i) => <path key={i} d={ringsToPathD(rings, true)} fillRule="evenodd" />)
            : polygons.map((poly, i) => <polygon key={i} points={poly.map(([x, y]) => `${x},${-y}`).join(' ')} />)}
        </Box>
      </svg>

      {animate && (
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
