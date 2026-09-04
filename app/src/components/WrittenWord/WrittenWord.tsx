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
import { MIN_XHEIGHT_PX, planParagraphs, type PlannedLine } from '@/lib/lineWrap';
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

// A typed blank row is worth one EXTRA leading — a paragraph gap is a doubled
// line gap, the way a hand skips a row. More than that and a two-paragraph
// postcard reads as two pictures again (owner decision 2026-09-04).
const PARAGRAPH_GAP_FACTOR = 2;

// The composer's own per-request cap (`MAX_TEXT_LEN`, api/routers/write.py).
// The lines that get WRITTEN are far shorter than this (lib/lineWrap's
// `MAX_CHARS_PER_LINE`); what can exceed it is the one request that asks the
// whole text "how wide does this hand run?" — so that one carries a
// word-boundary prefix instead. An average measured over 160 characters of the
// text is the same kind of estimate as one measured over 480.
const MAX_COMPOSE_CHARS = 160;

// Air the viewBox keeps at each end of a line so the first Anstrich and the
// last Auslauf are not clipped. It is part of what the frame has to hold, so
// the line plan spends it before it spends characters (lib/lineWrap).
const VIEWBOX_PAD_UNITS = 0.15;

interface Props {
  text: string;
  sourceId?: string;
  // Target rendered height in px of ONE line (width follows the aspect, capped).
  height?: number;
  // Write at THIS x-height instead — px per template unit, the Federprobe's
  // size ladder (sections/scribe/size.ts). It replaces `height` as the scale:
  // the block is then as tall as the text needs, not as tall as the caller
  // guessed, and the line breaks are planned for the same number. Omitted
  // everywhere else, where `height` goes on setting the size exactly as before.
  targetXHeightPx?: number;
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
  const pad = VIEWBOX_PAD_UNITS;
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
  targetXHeightPx,
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
  // Whitespace RUNS collapse on top of it: a typed newline is whitespace, and
  // it must never reach `/write/word`, which reads one as an ordinary space and
  // would write the break into the middle of a line (lib/lineWrap).
  const normalized = useMemo(() => text.normalize('NFC').replace(/\s+/g, ' ').trim(), [text]);
  // The text the MEASURING request carries: the whole thing, or — for a
  // postcard longer than the composer takes — as many whole words as fit.
  const measured = useMemo(() => {
    if (normalized.length <= MAX_COMPOSE_CHARS) return normalized;
    const cut = normalized.slice(0, MAX_COMPOSE_CHARS);
    const lastSpace = cut.lastIndexOf(' ');
    return lastSpace > 0 ? cut.slice(0, lastSpace) : cut;
  }, [normalized]);
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
    fetchRenderWord(sourceId, measured, bust)
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
  }, [normalized, measured, sourceId, bust]);

  // The size the block aims for: the chosen x-height, or the floor where no
  // step was chosen. It is what the split is planned for AND what the
  // measurement below is judged against.
  const aimPx = targetXHeightPx ?? MIN_XHEIGHT_PX;

  // What one character of THIS text runs, in template units — a real advance
  // from the text's own composition rather than an assumed average.
  const unitsPerChar = useMemo(() => {
    if (!composed || !composed.items.length || !measured) return 0;
    const { min_x, max_x } = composed.bounds;
    return (max_x - min_x) / measured.length;
  }, [composed, measured]);

  // What a line costs BESIDES its characters, in template units, and therefore
  // comes off the budget before a single character is bought.
  //
  // Two units of it are known up front: the viewBox air at both ends. The rest
  // is learned, because it cannot be estimated from the whole text — a line
  // pays for its own Anstrich and Auslauf, which a character in the middle of
  // one long composition never does, and a line that happens to collect the
  // wide letters costs more than the average promised. `extraPad` carries what
  // a composed line has since shown and only ever grows (below), so the re-plan
  // it triggers terminates: a larger pad means a smaller character budget, and
  // the budget is bounded below.
  //
  // It is a PAD and not a bigger per-character rate on purpose: what a line
  // pays for its own ends does not depend on how many characters stand between
  // them, and charging it per character taxes a long line harder than a short
  // one — the one place the estimate must not bend, since the whole question
  // is how many characters a line can hold.
  //
  // The key carries the aim: what a block of short lines costs per line says
  // nothing about a block of long ones, and keeping it would leave the smaller
  // step rendering differently after a visit to the larger one.
  const denserKey = `${loadKey}|${aimPx}`;
  const [extraPad, setExtraPad] = useState({ key: denserKey, units: 0 });
  const padUnits = 2 * VIEWBOX_PAD_UNITS + (extraPad.key === denserKey ? extraPad.units : 0);

  // Where the text breaks: at the writer's own typed breaks always, and inside
  // each paragraph wherever the chosen x-height (or, by default, the floor)
  // runs out of frame.
  const plan = useMemo(
    () =>
      planParagraphs(text, {
        availPx: capPx,
        unitsPerChar,
        padUnits,
        targetXHeightPx: aimPx,
      }),
    [text, capPx, unitsPerChar, padUnits, aimPx],
  );
  // Identity of the split, so a one-pixel frame change that breaks the text the
  // same way does not restart the fetch below (or the animation with it).
  const planKey = plan.map((l) => (l.paragraphBreak ? `¶${l.text}` : l.text)).join('\n');

  // Whether the block is composed per line rather than in one piece. Several
  // lines obviously are; so is a single line the measuring request could only
  // sample (a text past the composer's cap that has nowhere to break — one
  // enormous word), because `composed` then holds a PREFIX and drawing it would
  // silently write less than was typed.
  const splitIntoLines = plan.length > 1 || (plan.length === 1 && plan[0].text !== measured);
  // Whether the split is planned from a real advance yet, or still from the
  // "leave it alone" placeholder every paragraph starts as.
  const isMeasured = unitsPerChar > 0;

  // A wrapped text is composed line by line: each line then runs from its own
  // Anstrich to its own Auslauf (core/shaping.py assigns the word position per
  // slot), which is exactly what "one line = one continuous stroke run" means.
  const [wrapped, setWrapped] = useState<{ key: string; lines: ComposedWordOut[] } | null>(null);
  useEffect(() => {
    // Not before the text has been measured: until then `planLines` leaves
    // every paragraph whole by design ("nothing measured yet"), and a whole
    // postcard is longer than one composition request may carry.
    if (!splitIntoLines || !isMeasured) return;
    let cancelled = false;
    const key = `${loadKey}|${planKey}`;
    Promise.all(plan.map((line) => fetchRenderWord(sourceId, line.text, bust)))
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
  }, [planKey, splitIntoLines, isMeasured, loadKey, sourceId, bust]);

  // The compositions actually on screen: the whole text as one line, or the
  // wrapped set once it has arrived for THIS text and THIS split.
  const rendered = useMemo(() => {
    if (!splitIntoLines) return composed && composed.items.length ? [composed] : null;
    return wrapped?.key === `${loadKey}|${planKey}` ? wrapped.lines : null;
  }, [composed, wrapped, splitIntoLines, planKey, loadKey]);

  // The plan each rendered composition came from, kept beside it: the floor
  // check below needs to know how many words a line holds before it can say
  // whether breaking it again is even possible, and the layout needs to know
  // which lines open a paragraph.
  const planned = useMemo<PlannedLine[]>(
    () => (splitIntoLines ? plan : [{ text: normalized, paragraphBreak: false }]),
    [splitIntoLines, plan, normalized],
  );

  const layout = useMemo(() => {
    if (!rendered) return null;
    const lines = rendered
      .map((c, i) => ({
        ...lineGeom(c, showLineature),
        text: planned[i]?.text ?? '',
        paragraphBreak: planned[i]?.paragraphBreak ?? false,
        // The line's own composed width — what the split only estimated.
        spanUnits: c.bounds.max_x - c.bounds.min_x,
      }))
      .filter((g) => g.items.length);
    if (!lines.length) return null;

    // ONE scale for the whole block, taken from its widest line — a hand keeps
    // its x-height across a paragraph, so sizing each line to its own width
    // (which would blow up a two-word last line) is the wrong picture. The
    // honest cost: a word too long to break drags the whole block under the
    // floor with it, because it is the widest line.
    const maxVbW = Math.max(...lines.map((g) => g.vbW));
    const maxVbH = Math.max(...lines.map((g) => g.vbH));
    // Either the caller's box sets the size (everywhere but the Federprobe) or
    // the chosen x-height does; the frame caps both, because ink that leaves
    // the card is not a size, it is a bug.
    const unitPx = Math.min(targetXHeightPx ?? height / maxVbH, capPx / maxVbW);
    const sizes = lines.map((g) => ({ w: unitPx * g.vbW, h: unitPx * g.vbH }));
    const gap = unitPx * LINE_GAP_UNITS;
    // Leading BEFORE each line: none before the first, one gap between lines of
    // a paragraph, a doubled one where the writer left a row empty.
    const leads = lines.map((g, i) => (i === 0 ? 0 : gap * (g.paragraphBreak ? PARAGRAPH_GAP_FACTOR : 1)));

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
      return { geom: g, timing: slice, lead: leads[i], ...sizes[i] };
    });
    return {
      lines: perLine,
      unitPx,
      // The line the shared scale comes from: if it is still under the floor,
      // this is the only line whose break would lift the whole block.
      widest: lines.reduce((a, b) => (b.vbW > a.vbW ? b : a)),
      writeEndMs,
      inkW: Math.max(...sizes.map((s) => s.w)),
      inkH: sizes.reduce((sum, s) => sum + s.h, 0) + leads.reduce((sum, l) => sum + l, 0),
    };
  }, [rendered, planned, showLineature, durationMs, height, targetXHeightPx, capPx]);

  // The aim is a statement about the RESULT, not about the estimate that got
  // there. The split is planned from the whole text's AVERAGE advance, so a
  // line that collected the wide letters — or simply paid for its own Anstrich
  // and Auslauf — comes back smaller than aimed at even though it holds several
  // words: the estimate was fine, the line was denser. Then the measurement
  // replaces the estimate and the text is re-planned; adjusting state during
  // render is React's own "adjusting state when a prop changes", and the guards
  // make it a one-shot per split (a re-plan that does not move the split yields
  // the same measurement, which no longer passes `>`). What stays under the aim
  // after that is the case no break can fix: a word wider than the frame, which
  // is also the widest line and so sets the scale for the whole block — under
  // the chosen SIZE that is honest, under the FLOOR it is the Tintenboden's one
  // documented exception (lib/lineWrap).
  if (extraPad.key !== denserKey) {
    setExtraPad({ key: denserKey, units: 0 });
  } else if (layout && layout.unitPx < aimPx) {
    const { text, spanUnits } = layout.widest;
    // What this line cost beyond what its characters promised — its own
    // Anstrich and Auslauf, plus whatever the letter mix added.
    const over = spanUnits - text.length * unitsPerChar;
    if (/\s/.test(text.trim()) && over > extraPad.units) setExtraPad({ key: denserKey, units: over });
  }

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
        //
        // The image role sits HERE and not on the frame: `role="img"` makes its
        // subtree one graphic to assistive tech, and the frame also holds the ↺
        // — which a screen reader would then never reach.
        <Box
          role="img"
          aria-label={ariaLabel ?? text}
          // The leading sits on the LINE, not on the column: a paragraph gap is
          // a doubled one, and a flex `gap` can only be one number.
          sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}
        >
          {layout.lines.map((line, i) => (
            <WrittenLine
              key={i}
              geom={line.geom}
              width={line.w}
              height={line.h}
              marginTop={line.lead}
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
