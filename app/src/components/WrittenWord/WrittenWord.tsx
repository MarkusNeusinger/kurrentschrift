// WrittenWord — writes an arbitrary word or line "as written": each glyph's
// filled Sütterlin silhouette plus the generated connecting strokes (Übergänge),
// revealed stroke-by-stroke in writing order across the whole word. The
// single-glyph sibling is `WrittenGlyph`; this one renders many.
//
// Composition happens SERVER-SIDE (GET /write/word → core/shaping.py +
// core/compose.py): shaping (long-s, ligatures incl. the decompose fallback),
// baseline placement and the generated connectors arrive as flat draw items in
// writing order — ONE cacheable request per text. This component measures,
// decides how many lines the text needs, and renders each line via
// `WrittenLine`: fill every silhouette + stroke every connector inside one
// group, then mask it with a wide path swept along each centerline via an
// animated `stroke-dashoffset`.
//
// Two things are measured rather than assumed (site audit 2026-09-02, finding
// 28): the frame's real width — the caller's `maxWidth` is an upper bound, not
// the truth, and computing the box from it left a 29-character sentence 22 px
// high inside a box three times that tall — and, from it, whether the text
// clears the legibility floor as one line. Below the floor it breaks into
// several lines (lib/lineWrap; owner decision 2026-09-04), each composed and
// written as its own continuous stroke run: "Zug um Zug" holds per LINE.

import { Box, CircularProgress } from '@mui/material';
import { useCallback, useEffect, useId, useMemo, useState } from 'react';

import { CONFIG } from '@/global-config';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion';
import { useAvailableWidth } from '@/hooks/useAvailableWidth';
import { de } from '@/locales';
import { fetchRenderWord, type ComposedWordOut } from '@/lib/api';
import {
  allocateDurations,
  sequenceReveal,
  strokeTimeProfile,
  LINE_BREAK_PAUSE_MS,
  PEN_PAUSE_MS,
  WORD_MAX_W,
  WORD_MIN_ITEM_MS,
  WORD_WRITE_MS,
} from '@/lib/strokeTiming';
import { planLines } from '@/lib/lineWrap';
import { ReplayButton } from '@/components/inkReveal';
import { replayGround } from '@/components/inkReveal/replayGround';
import { WrittenLine, type LineGeom } from './WrittenLine';

// Composition happens server-side and is cached in the shared render cache
// (`@/lib/api/renderCache` → fetchRenderWord), so a replay, a re-mount or a
// second WrittenWord on the page never refetches — one cacheable request per
// text across the whole session. A wrapped text costs one request per line on
// top of the one that measured it; both stay in that same cache.

// Leading between wrapped lines, in template units. Each line's viewBox already
// spans ascender to descender, so this is the air between those extremes; it
// scales with the writing, which is what keeps a phone's three lines reading as
// one hand rather than as three stacked pictures.
const LINE_GAP_UNITS = 0.3;

interface Props {
  text: string;
  sourceId?: string;
  // Target rendered height in px of ONE line (width follows the aspect, capped).
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
  // (empty = all rendered), how many strokes were placed, and when the write-in
  // ends (ms from reveal start, pen-lift pauses included; 0 when nothing
  // renders). Lets callers flag the letters, fall back, or time follow-up
  // decoration to the last stroke (the landing hero's flourish).
  onResolved?: (info: { missing: string[]; rendered: number; writeEndMs: number }) => void;
  // A fetch error (e.g. cold-start retries exhausted).
  onError?: (e: unknown) => void;
  // Accessible name of the rendered block. Defaults to the written text; the quiz
  // passes a neutral label so the image does not leak the solution word to the
  // DOM/screen reader before the answer.
  ariaLabel?: string;
  // Admin-only reload stamp (AdminContext.cropCacheBust). Moves the render
  // cache key AND the request, so „Neu laden" actually re-composes instead of
  // being answered by the client cache or the CDN. Public surfaces omit it.
  bust?: number;
}

// What a word starts out showing: nothing (the spinner) while its composition
// is fetched, or — for empty text, which the server 422s on — a settled empty
// composition, so a caller reads `missing: []` instead of waiting forever.
const startState = (normalized: string): ComposedWordOut | null =>
  normalized ? null : { text: '', items: [], bounds: { min_x: 0, max_x: 1, min_y: 0, max_y: 1 }, guides: null, missing: [] };

// Viewbox of one composed line in template units.
function lineGeom(composed: ComposedWordOut, showLineature: boolean): LineGeom {
  const { bounds, guides, items } = composed;
  const pad = 0.15;
  const yHi = showLineature && guides ? Math.max(guides.ascender, bounds.max_y) : bounds.max_y + pad;
  const yLo = showLineature && guides ? Math.min(guides.descender, bounds.min_y, 0) : bounds.min_y - pad;
  return {
    minX: bounds.min_x - pad,
    vbW: bounds.max_x - bounds.min_x + 2 * pad,
    vbY: -yHi,
    vbH: Math.max(0.5, yHi - yLo),
    items,
    guides,
  };
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
  bust,
}: Props) {
  const reducedMotion = usePrefersReducedMotion();
  const uid = useId();
  // Mirror the server's normalisation so equal words share one cache/URL entry.
  const normalized = useMemo(() => text.normalize('NFC').trim(), [text]);
  const [composed, setComposed] = useState<ComposedWordOut | null>(() => startState(normalized));
  const [run, setRun] = useState(0);

  // The frame's real width, not the caller's constant. `maxWidth` stays the
  // caller's upper bound (the hero wants a specific size); the frame decides
  // whether that bound is reachable at all.
  const [frameEl, setFrameEl] = useState<HTMLElement | null>(null);
  const frameW = useAvailableWidth(frameEl);
  const capPx = frameW > 0 ? Math.min(maxWidth, frameW) : maxWidth;

  // Drop the previous word's composition DURING RENDER instead of in the effect
  // below — React's "adjusting state when a prop changes"
  // (react-hooks/set-state-in-effect). The guard carries the effect's inputs, so
  // a word swap no longer paints one frame of the old ink before the spinner.
  const loadKey = `${sourceId} ${bust ?? ''} ${normalized}`;
  const [shownFor, setShownFor] = useState(loadKey);
  if (shownFor !== loadKey) {
    setShownFor(loadKey);
    setComposed(startState(normalized));
  }

  useEffect(() => {
    let cancelled = false;
    // Nothing to write (the server 422s on empty text): `startState` has already
    // settled on the empty composition, so callers see `missing: []` rather
    // than a spinner forever.
    if (!normalized) return;
    fetchRenderWord(sourceId, normalized, bust)
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
  }, [normalized, sourceId, bust]);

  // Does the text clear the legibility floor as ONE line in this frame? The
  // composition of the whole text is what answers it: its width in template
  // units per character is this hand's real advance, not an assumed average.
  const plan = useMemo(() => {
    if (!composed || !composed.items.length || !normalized) return [normalized];
    const { min_x, max_x } = composed.bounds;
    return planLines(normalized, { availPx: capPx, unitsPerChar: (max_x - min_x) / normalized.length });
  }, [composed, normalized, capPx]);
  // Identity of the split, so a one-pixel frame change that breaks the text the
  // same way does not restart the fetch below (or the animation with it).
  const planKey = plan.join('\n');

  // A wrapped text is composed line by line: each line then runs from its own
  // Anstrich to its own Auslauf (core/shaping.py assigns the word position per
  // slot), which is exactly what "one line = one continuous stroke run" means.
  const [wrapped, setWrapped] = useState<{ key: string; lines: ComposedWordOut[] } | null>(null);
  useEffect(() => {
    if (plan.length < 2) return;
    let cancelled = false;
    const key = `${loadKey}|${planKey}`;
    Promise.all(plan.map((line) => fetchRenderWord(sourceId, line, bust)))
      .then((lines) => {
        if (!cancelled) setWrapped({ key, lines });
      })
      .catch((e) => {
        if (!cancelled) onError?.(e);
      });
    return () => {
      cancelled = true;
    };
    // `plan` is `planKey`'s content and onError must not restart the fetch.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [planKey, loadKey, sourceId, bust]);

  // The compositions actually on screen: the whole text as one line, or the
  // wrapped set once it has arrived for THIS text and THIS split.
  const rendered = useMemo(() => {
    if (plan.length < 2) return composed && composed.items.length ? [composed] : null;
    return wrapped?.key === `${loadKey}|${planKey}` ? wrapped.lines : null;
  }, [composed, wrapped, plan.length, planKey, loadKey]);

  const layout = useMemo(() => {
    if (!rendered) return null;
    const lines = rendered.map((c) => lineGeom(c, showLineature)).filter((g) => g.items.length);
    if (!lines.length) return null;

    // ONE scale for the whole block, taken from its widest line — a hand keeps
    // its x-height across a paragraph, so sizing each line to its own width
    // (which would blow up a two-word last line) is the wrong picture. The
    // honest cost: a word too long to break drags the whole block under the
    // floor with it, because it is the widest line.
    const maxVbW = Math.max(...lines.map((g) => g.vbW));
    const maxVbH = Math.max(...lines.map((g) => g.vbH));
    const unitPx = Math.min(height / maxVbH, capPx / maxVbW);
    const sizes = lines.map((g) => ({ w: unitPx * g.vbW, h: unitPx * g.vbH }));
    const gap = unitPx * LINE_GAP_UNITS;

    // Human kinematics instead of a constant sweep (lib/strokeTiming): the
    // two-thirds power law slows the front in curves (non-linear dashoffset
    // keyframes per item) and isochrony allocates durations sublinearly. The
    // allocation runs over ALL lines at once, so `durationMs` stays the time the
    // whole text takes; a pen-lift pause precedes an item flagged as following
    // an Absetzen, and a longer beat marks the pen's travel back to the margin.
    const flat = lines.flatMap((g) => g.items);
    const lineStart = new Set<number>();
    let cursor = 0;
    for (const g of lines) {
      lineStart.add(cursor);
      cursor += g.items.length;
    }
    const profiles = flat.map((it) => strokeTimeProfile(it.centerline));
    const durations = allocateDurations(
      profiles.map((p) => p.weight),
      durationMs,
      WORD_MIN_ITEM_MS,
    );
    const { timing, writeEndMs } = sequenceReveal(profiles, durations, {
      leadPause: (i) => (i > 0 && lineStart.has(i) ? LINE_BREAK_PAUSE_MS : flat[i].lift ? PEN_PAUSE_MS : 0),
    });

    let at = 0;
    const perLine = lines.map((g, i) => {
      const slice = timing.slice(at, at + g.items.length);
      at += g.items.length;
      return { geom: g, timing: slice, ...sizes[i] };
    });
    return {
      lines: perLine,
      gap,
      writeEndMs,
      inkW: Math.max(...sizes.map((s) => s.w)),
      inkH: sizes.reduce((sum, s) => sum + s.h, 0) + gap * (sizes.length - 1),
    };
  }, [rendered, showLineature, durationMs, height, capPx]);

  useEffect(() => {
    // `layout` is derived from `rendered` in this same render, so reading it
    // here without listing it keeps "fires once per composition" semantics.
    if (rendered)
      onResolved?.({
        missing: [...new Set(rendered.flatMap((c) => c.missing))],
        rendered: rendered.reduce((sum, c) => sum + c.items.length, 0),
        writeEndMs: layout?.writeEndMs ?? 0,
      });
    else if (composed && !composed.items.length) onResolved?.({ missing: composed.missing, rendered: 0, writeEndMs: 0 });
    // onResolved intentionally omitted: report only when the composition changes,
    // not when a parent passes a fresh callback identity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rendered, composed]);

  const replay = useCallback(() => setRun((r) => r + 1), []);

  const animate = animateProp && !reducedMotion;
  // Exactly the condition the button itself renders under: a reader who prefers
  // reduced motion gets no replay button, so reserving ground for one would be
  // empty space with nothing in it.
  const hasReplay = animate && showReplay;
  const maskId = `word-${uid.replace(/[^a-zA-Z0-9_-]/g, '_')}`;

  // Ground for the ↺: the button hangs bottom-right inside this box, and a box
  // that hugs the writing hands it the last letters. `height` stays the floor
  // the caller asked for, so a short line keeps the room #517 reserved for it.
  // Only where the button exists — everywhere else the box goes on hugging the
  // writing, so no other surface's layout moves.
  const ground = hasReplay && layout ? replayGround(layout.inkW, layout.inkH, frameW) : null;

  return (
    <Box
      ref={setFrameEl}
      role={layout ? 'img' : undefined}
      aria-label={layout ? (ariaLabel ?? text) : undefined}
      sx={{
        position: 'relative',
        display: 'inline-flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        // Until the writing is there, the box holds the room the caller asked
        // for — the spinner used to do that on its own.
        ...(ground ? { width: ground.width, minHeight: Math.max(height, ground.minHeight ?? 0) } : layout ? {} : { minHeight: height }),
      }}
    >
      {layout ? (
        // Wrapped lines share a left margin, the way a hand does — a centred
        // stack of ragged lines reads as an inscription, not as writing. The
        // column hugs its widest line and the frame centres IT, so a single
        // line sits exactly where it always did.
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: `${layout.gap}px` }}>
          {layout.lines.map((line, i) => (
            <WrittenLine
              key={i}
              geom={line.geom}
              width={line.w}
              height={line.h}
              timing={line.timing}
              animate={animate}
              run={run}
              maskId={`${maskId}-${run}-${i}`}
              showLineature={showLineature}
              surfaceBg={surfaceBg}
              inkColor={inkColor}
              writeEndMs={layout.writeEndMs}
            />
          ))}
        </Box>
      ) : composed && !composed.items.length ? null : (
        <CircularProgress size={26} aria-label={de.common.writing} />
      )}

      {hasReplay && layout && <ReplayButton onClick={replay} />}
    </Box>
  );
}
