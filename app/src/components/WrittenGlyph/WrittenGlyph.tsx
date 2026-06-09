// WrittenGlyph — renders a canonical glyph "as written": the filled Schwellzug
// silhouette (from the Loth-derived ductus) revealed stroke-by-stroke in the
// order the pen drew it. Used as the quiz prompt instead of a static crop.
//
// Technique: the backend (`core.pipeline.diagnostic_for_glyph`) gives us, per
// pen-stroke, the filled `outline_polygons` AND the matching `centerlines_template`
// (the spine of each polygon, in writing order). We fill the polygons, then mask
// them with a wide stroked path swept along each centerline via an animated
// `stroke-dashoffset` — so the ink appears along the actual pen path, lifting
// between strokes (no bar bridging an Absetzen). A pen lift is a real gap because
// each stroke is its own polygon + its own centerline.
//
// Coordinates: template space (baseline=0, midband=1, y up). SVG y points down,
// so we negate y in the rendered data (rather than a flipped <g>) to keep the
// mask coordinates aligned with the filled polygons without a nested transform.

import ReplayIcon from '@mui/icons-material/Replay';
import { Alert, Box, CircularProgress, IconButton, keyframes } from '@mui/material';
import { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react';

import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion';
import { ApiError, getDiagnostic, type DiagnosticData } from '@/lib/api';
import { de } from '@/locales';

// Reveal a dashed path (pathLength=1, dasharray=1): offset 1 hides it, 0 draws it.
const reveal = keyframes`from { stroke-dashoffset: 1; } to { stroke-dashoffset: 0; }`;

// Diagnostics are a backend compute (skeleton extraction); cache per glyph_key so
// replays and repeat questions don't refetch. `null` records a 404 (no ductus).
const cache = new Map<string, DiagnosticData | null>();

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
  // Called if the glyph has no canonical yet (404) so the caller can fall back to
  // the static crop. The component itself renders nothing once unavailable.
  onUnavailable?: () => void;
}

const PEN_PAUSE_MS = 150; // pause at each Absetzen so the lift reads as a lift
const MAX_W = 300;

export function WrittenGlyph({ glyphKey, durationMs = 1500, height = 220, onUnavailable }: Props) {
  const reducedMotion = usePrefersReducedMotion();
  const uid = useId();
  const [data, setData] = useState<DiagnosticData | null>(() => cache.get(glyphKey) ?? null);
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
    const cached = cache.get(glyphKey);
    if (cached !== undefined) {
      if (cached === null) {
        setUnavailable(true);
        onUnavailableRef.current?.();
      } else {
        setData(cached);
      }
      return;
    }
    setData(null); // spinner while the new glyph loads
    getDiagnostic(glyphKey)
      .then((d) => {
        if (cancelled) return;
        cache.set(glyphKey, d);
        setData(d);
      })
      .catch((e) => {
        if (e instanceof ApiError && e.status === 404) {
          // No canonical traced yet → let the caller show the crop instead.
          cache.set(glyphKey, null);
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
  }, [glyphKey]);

  const replay = useCallback(() => setRun((r) => r + 1), []);

  const geom = useMemo(() => {
    if (!data) return null;
    const tpl = data.template_guides;
    const xs = data.anchors_template.map((a) => a[0]);
    const advance = xs.length ? Math.max(0.5, ...xs) - Math.min(0, ...xs) : 1;
    const minX = -0.5;
    const vbW = advance + 1.0;
    const vbY = -tpl.ascender - 0.3;
    const vbH = tpl.ascender - tpl.descender + 0.6;

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

    return { tpl, minX, vbW, vbY, vbH, polygons, centerlines, maskWidth, timing };
  }, [data, durationMs]);

  if (unavailable) return null;
  if (error) {
    return <Alert severity="error" sx={{ width: '100%' }}>{error}</Alert>;
  }
  if (!data || !geom) {
    return <CircularProgress size={28} />;
  }

  const { tpl, minX, vbW, vbY, vbH, polygons, centerlines, maskWidth, timing } = geom;
  const displayH = height;
  let displayW = (displayH * vbW) / vbH;
  let finalH = displayH;
  if (displayW > MAX_W) {
    finalH = (MAX_W * vbH) / vbW;
    displayW = MAX_W;
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
        style={{ display: 'block', background: '#fff' }}
      >
        <defs>
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
        <line x1={minX} y1={-tpl.baseline} x2={minX + vbW} y2={-tpl.baseline} stroke="#ddd" strokeWidth={0.012} />
        <line
          x1={minX}
          y1={-tpl.midband}
          x2={minX + vbW}
          y2={-tpl.midband}
          stroke="#ebebeb"
          strokeWidth={0.012}
          strokeDasharray="0.08 0.06"
        />

        {/* Filled silhouette, revealed by the swept mask. */}
        <g mask={`url(#${maskId})`}>
          {polygons.map((poly, i) => (
            <polygon key={i} points={poly.map(([x, y]) => `${x},${-y}`).join(' ')} fill="#1b1b1b" />
          ))}
        </g>
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
