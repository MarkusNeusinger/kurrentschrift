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

import { Alert, Box, CircularProgress } from '@mui/material';
import { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react';

import { CONFIG } from '@/global-config';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion';
import { fetchRenderGlyph, peekRenderGlyph, seedRenderGlyph, type GlyphRenderData } from '@/lib/api';
import { useStrokeReveal } from '@/hooks/useStrokeReveal';
import {
  allocateDurations,
  sequenceReveal,
  strokeTimeProfile,
  GLYPH_MAX_W,
  GLYPH_MIN_STROKE_MS,
  GLYPH_WRITE_MS,
  PEN_PAUSE_MS,
  SETTLE_MS,
} from '@/lib/strokeTiming';
import { InkBleedFilter, InkGuides, RevealMask, ReplayButton, inkGroupSx } from '@/components/inkReveal';
import { ringsToPathD, type Ring } from '@/lib/svg';
import { de } from '@/locales';

// Render payloads come from the shared render cache (`@/lib/api/renderCache`),
// so a glyph the quiz letter shows and a written word contains costs one fetch
// per session across ALL surfaces. Version stamps (`bust`) and externally
// supplied payloads (the admin dialog) are handled there too.

// Rendering colours of this work surface. The crop box is one of the neutral
// surfaces that deliberately opt out of the paper identity (style-guide §8) —
// this is a local rendering constant, not a theme token.
const SURFACE_BG = '#fff'; // neutral white crop ground (binding)

interface Props {
  glyphKey: string;
  // Source the glyph is rendered from. Defaults to the site-wide public source
  // (CONFIG.sourceId); admin callers pass their runtime-active source so seeded
  // and fetched payloads live under THAT source's cache keys — otherwise an
  // admin who switched sources would poison the public cache entries the quiz
  // and Tafel read in the same SPA session.
  sourceId?: string;
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
  // Already-fetched render payload — skips the internal fetch entirely (the
  // Diagnose dialog shares one diagnostic payload across its stages; the
  // admin's DiagnosticData is a structural superset of GlyphRenderData).
  data?: GlyphRenderData;
  // Background behind the SVG. Defaults to the neutral white work-surface ground;
  // public surfaces (the quiz) pass a paper tone — or `transparent` to inherit
  // their container's paper ground — so the fresh-ink render doesn't read as a
  // stark white box on the cream page.
  surfaceBg?: string;
  // Solid ink colour override. When set, the glyph is filled in this single
  // colour and the iron-gall settle (fresh blue-black → oxidized) is skipped —
  // used by the quiz comparison to tint the learner's wrong pick red and the
  // correct form near-black.
  inkColor?: string;
  // Whether to play the write-in (and settle). Defaults to true; pass false to
  // render the glyph already fully drawn (the post-answer comparison shows the
  // finished forms, not a second performance). ANDed with the reduced-motion
  // preference, so a static render is the floor either way.
  animate?: boolean;
  // Called if the glyph has no canonical yet (404) so the caller can fall back to
  // the static crop. The component itself renders nothing once unavailable.
  onUnavailable?: () => void;
}

export function WrittenGlyph({ glyphKey, sourceId = CONFIG.sourceId, durationMs = GLYPH_WRITE_MS, height = 220, tight = false, maxWidth, cacheBust, data: dataProp, onUnavailable, surfaceBg = SURFACE_BG, inkColor, animate: animateProp = true }: Props) {
  const reducedMotion = usePrefersReducedMotion();
  const uid = useId();
  const [fetched, setFetched] = useState<GlyphRenderData | null>(
    () => peekRenderGlyph(sourceId, glyphKey, cacheBust) ?? null,
  );
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
      // Externally supplied payload: seed the shared cache so other consumers
      // see the freshest canonical without refetching — under the CALLER's
      // source, so an admin payload never overwrites the public source's entry.
      seedRenderGlyph(sourceId, glyphKey, dataProp, cacheBust);
      return;
    }
    setFetched(peekRenderGlyph(sourceId, glyphKey, cacheBust) ?? null); // spinner while loading
    // Public surfaces render the site-wide source (the default), regardless of
    // which source the admin currently has active. A resolved `null` means no
    // canonical is traced yet → let the caller show the crop instead.
    fetchRenderGlyph(sourceId, glyphKey, cacheBust)
      .then((d) => {
        if (cancelled) return;
        if (d === null) {
          setUnavailable(true);
          onUnavailableRef.current?.();
        } else {
          setFetched(d);
        }
      })
      .catch((e) => {
        if (!cancelled) setError(String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [glyphKey, sourceId, cacheBust, dataProp]);

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
    const polygons = (
      data.outline_polygons ?? ((data.outline_polygon?.length ?? 0) > 2 ? [data.outline_polygon!] : [])
    ).filter((p) => p.length > 2);
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

    // Human kinematics instead of an even pace (lib/strokeTiming): the
    // two-thirds power law slows the sweep in curves via non-linear dashoffset
    // keyframes, isochrony allocates stroke durations sublinearly; each stroke
    // starts after the previous one finishes plus a short pen-lift pause. The
    // trailing pause is folded into writeEndMs so the settle starts one beat
    // after the last stroke, letting the lift register before the ink ages.
    const profiles = centerlines.map((cl) => strokeTimeProfile(cl as [number, number][]));
    const durations = allocateDurations(
      profiles.map((p) => p.weight),
      durationMs,
      GLYPH_MIN_STROKE_MS,
    );
    const { timing, writeEndMs } = sequenceReveal(profiles, durations, { trailPause: PEN_PAUSE_MS });

    return { tpl, minX, vbW, vbY, vbH, strokePaths, polygons, centerlines, maskWidth, timing, writeEndMs };
  }, [data, durationMs, tight]);

  const animate = animateProp && !reducedMotion;
  // WAAPI drives the per-path dashoffset (scoped, no global @keyframes growth);
  // hooks run unconditionally, before the early returns.
  const maskPathRefs = useRef<Array<SVGPathElement | null>>([]);
  useStrokeReveal(maskPathRefs, geom?.timing ?? [], animate && !!geom, `${run}|${geom ? 'g' : ''}`);

  if (unavailable) return null;
  if (error) {
    return <Alert severity="error" sx={{ width: '100%' }}>{error}</Alert>;
  }
  if (!data || !geom) {
    return <CircularProgress size={28} />;
  }

  const { tpl, minX, vbW, vbY, vbH, strokePaths, polygons, centerlines, maskWidth, writeEndMs } = geom;
  const displayH = height;
  const maxW = maxWidth ?? GLYPH_MAX_W;
  let displayW = (displayH * vbW) / vbH;
  let finalH = displayH;
  if (displayW > maxW) {
    finalH = (maxW * vbH) / vbW;
    displayW = maxW;
  }
  // useId() namespaces the mask per component instance so two WrittenGlyphs with
  // the same glyph_key on screen at once can't collide on `url(#id)`.
  const maskId = `written-${uid.replace(/[^a-zA-Z0-9_-]/g, '_')}-${run}`;

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
        style={{ display: 'block', background: surfaceBg, maxWidth: '100%' }}
      >
        <defs>
          <InkBleedFilter id={`${maskId}-bleed`} scale={0.018} />
          <RevealMask
            id={maskId}
            bounds={{ x: minX, y: vbY, width: vbW, height: vbH }}
            strokes={centerlines.map((line) => ({ centerline: line, maskWidth }))}
            pathRefs={maskPathRefs}
            animate={animate}
            runKey={run}
          />
        </defs>

        {/* Faint Lineatur (baseline + midband) for reading context. */}
        <InkGuides minX={minX} width={vbW} baseline={tpl.baseline} midband={tpl.midband} />

        {/* Filled silhouette, revealed by the swept mask. The group carries the
            fill so the iron-gall settle (fresh blue-black → oxidized) animates
            all strokes at once after the last pen lift; keyed by run so the
            replay button restarts it together with the write-in. */}
        <Box
          component="g"
          key={`ink-${run}`}
          mask={`url(#${maskId})`}
          filter={`url(#${maskId}-bleed)`}
          sx={inkGroupSx({ animate, writeEndMs, settleMs: SETTLE_MS, inkColor })}
        >
          {strokePaths
            ? strokePaths.map((rings, i) => <path key={i} d={ringsToPathD(rings, true)} fillRule="evenodd" />)
            : polygons.map((poly, i) => <polygon key={i} points={poly.map(([x, y]) => `${x},${-y}`).join(' ')} />)}
        </Box>
      </svg>

      {animate && <ReplayButton onClick={replay} />}
    </Box>
  );
}
