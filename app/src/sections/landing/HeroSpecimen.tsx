import { Box } from '@mui/material';
import { keyframes } from '@mui/system';
import { useState } from 'react';

import { de } from '@/locales';
import { garamond, inkState, paper, script } from '@/styles/paper';

// --- animations -----------------------------------------------------------
const writeIn = keyframes`from { clip-path: inset(0 100% 0 0); } to { clip-path: inset(0 0 0 0); }`;
// Iron-gall ink settle: the word is written in fresh blue-black (blauschwarz,
// the regulated German school ink) and settles toward the aged manuscript
// brown the rest of the page wears — decades compressed into seconds. The
// settle starts at 2.6s: a deliberate ~200ms breath after the write-in ends
// (0.5s delay + 1.9s writeIn) so the fresh ink registers before it ages.
const inkSettle = keyframes`from { fill: ${inkState.fresh}; } to { fill: ${paper.ink}; }`;
// Only a `to` rule: the draw-in starts from each line's own strokeDashoffset
// (set to SPECIMEN_VB.w below), so nothing here is coupled to the viewBox width.
const drawStroke = keyframes`to { stroke-dashoffset: 0; }`;
const fadeIn = keyframes`from { opacity: 0; } to { opacity: 1; }`;
const reduce = '@media (prefers-reduced-motion: reduce)';

// delayed fade-in for the specimen sub-line + caption
const fi = (delay: number) => ({
  opacity: 0,
  animation: `${fadeIn} 1s ease ${delay}s forwards`,
  [reduce]: { opacity: 1, animation: 'none' },
});

// Hero specimen — the word written onto a real German Kurrent lineature (four
// guide lines, three roughly equal bands). Coordinates are SVG viewBox units at
// font-size 100; the y-values come from GL-GermanCursive's own metrics (upm 1000):
// the ascenders of K and t top out at ~0.593em, so the Oberlinie sits one band
// (~0.6em) above the baseline and the t actually reaches it. The word advance is
// ~2.94em → ~294 units, so the lines hug the word instead of running off wide.
const SPECIMEN_VB = { w: 332, h: 100 }; // viewBox; lines use w as both dasharray and start offset
const SPECIMEN_BASELINE = 66; // y of the Grundlinie = the text baseline
const ruleLines = [
  { y: 7, delay: 0.15, color: paper.line, opacity: 0.95 }, // Oberlinie — ascenders (K, t) touch
  { y: 36, delay: 0.25, color: paper.sepiaFaint, opacity: 0.7 }, // Mittellinie — x-height (Mittellänge)
  { y: SPECIMEN_BASELINE, delay: 0.35, color: paper.line, opacity: 1 }, // Grundlinie — baseline
  { y: 96, delay: 0.45, color: paper.sepiaFaint, opacity: 0.7 }, // Unterlinie — descender band
];

// The word written onto a real Kurrent lineature. Rendered as SVG so the
// baseline is an exact coordinate and the ascenders land on the Oberlinie
// regardless of viewport/font box.
export function HeroSpecimen() {
  // Bumping this remounts the script word so its write-in animation replays.
  const [replayKey, setReplayKey] = useState(0);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', mt: { xs: 1, md: 0 } }}>
      <Box
        key={`word-${replayKey}`}
        component="svg"
        viewBox={`0 0 ${SPECIMEN_VB.w} ${SPECIMEN_VB.h}`}
        role="img"
        aria-label={de.landing.specimen.word}
        sx={{
          width: '100%',
          maxWidth: { xs: 360, md: 520 },
          height: 'auto',
          display: 'block',
          overflow: 'visible',
        }}
      >
        <defs>
          {/* Ink bleed: fibre-wicking displacement on the script word. viewBox
              units are ~pixels here (332×100), unlike WrittenGlyph's template
              units, hence the much larger scale/baseFrequency pair. */}
          <filter id="hero-ink-bleed" x="-5%" y="-15%" width="110%" height="130%">
            <feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="2" seed="7" result="noise" />
            <feDisplacementMap in="SourceGraphic" in2="noise" scale="1.1" xChannelSelector="R" yChannelSelector="G" />
          </filter>
        </defs>
        {ruleLines.map((l, i) => (
          <Box
            key={i}
            component="line"
            x1={0}
            y1={l.y}
            x2={SPECIMEN_VB.w}
            y2={l.y}
            sx={{
              stroke: l.color,
              strokeWidth: 1,
              opacity: l.opacity,
              strokeDasharray: SPECIMEN_VB.w,
              strokeDashoffset: SPECIMEN_VB.w,
              animation: `${drawStroke} .7s ease ${l.delay}s forwards`,
              [reduce]: { strokeDashoffset: 0, animation: 'none' },
            }}
          />
        ))}
        <Box
          component="text"
          x={14}
          y={SPECIMEN_BASELINE}
          filter="url(#hero-ink-bleed)"
          sx={{
            fontFamily: script,
            fontSize: 100,
            fill: inkState.fresh,
            clipPath: 'inset(0 100% 0 0)',
            animation: `${writeIn} 1.9s cubic-bezier(.6,.02,.2,1) .5s forwards, ${inkSettle} 2.5s ease 2.6s forwards`,
            [reduce]: { clipPath: 'none', animation: 'none', fill: paper.ink },
          }}
        >
          {de.landing.specimen.word}
        </Box>
      </Box>

      <Box
        sx={{
          fontFamily: script,
          fontSize: 'clamp(1.8rem, 4vw, 2.6rem)',
          color: paper.sepia,
          transform: 'rotate(-1.2deg)',
          mt: '0.9rem',
          ml: '0.4rem',
          ...fi(2.2),
        }}
      >
        {de.landing.specimen.subline}
      </Box>

      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.6rem',
          mt: '2rem',
          flexWrap: 'wrap',
          color: paper.sepia,
          fontStyle: 'italic',
          fontSize: '0.98rem',
          ...fi(2.5),
        }}
      >
        <Box component="span">{de.landing.specimen.caption}</Box>
        <Box
          component="button"
          onClick={() => setReplayKey((k) => k + 1)}
          sx={{
            cursor: 'pointer',
            border: `1px solid ${paper.line}`,
            bgcolor: 'transparent',
            color: paper.sepia,
            fontFamily: garamond,
            fontStyle: 'italic',
            fontSize: '0.92rem',
            px: '0.7rem',
            py: '0.25rem',
            borderRadius: '2px',
            transition: 'all .25s ease',
            '&:hover': { borderColor: paper.viridian, color: paper.viridian },
          }}
        >
          {de.landing.specimen.replay}
        </Box>
      </Box>
    </Box>
  );
}
