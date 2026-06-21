import { Box } from '@mui/material';
import { keyframes } from '@mui/system';
import { useCallback, useState } from 'react';

import { WrittenWord } from '@/components/WrittenWord';
import { de } from '@/locales';
import { garamond, inkState, paper, script } from '@/styles/paper';

// The word the hero writes live with the real ductus engine (Sütterlin). Chosen
// lowercase + from the §9 anchor set (l·e·ſ·e·n) so it reliably resolves to
// curated canonicals, and because it echoes the specimen subline ("leſen …").
// Easy to swap once more Sütterlin glyphs are curated.
const HERO_WORD = 'lesen';

// --- fallback (font specimen) animations -----------------------------------
const writeIn = keyframes`from { clip-path: inset(0 100% 0 0); } to { clip-path: inset(0 0 0 0); }`;
const inkSettle = keyframes`from { fill: ${inkState.fresh}; } to { fill: ${paper.ink}; }`;
const drawStroke = keyframes`to { stroke-dashoffset: 0; }`;
const fadeIn = keyframes`from { opacity: 0; } to { opacity: 1; }`;
const reduce = '@media (prefers-reduced-motion: reduce)';

const fi = (delay: number) => ({
  opacity: 0,
  animation: `${fadeIn} 1s ease ${delay}s forwards`,
  [reduce]: { opacity: 1, animation: 'none' },
});

// Fallback specimen — the word set in the Kurrent font on a four-line lineature.
// Shown while the engine loads and if it can't fully render the word (missing
// canonical / API cold start), so the hero never reads as broken.
const SPECIMEN_VB = { w: 332, h: 100 };
const SPECIMEN_BASELINE = 66;
const ruleLines = [
  { y: 7, delay: 0.15, color: paper.line, opacity: 0.95 },
  { y: 36, delay: 0.25, color: paper.sepiaFaint, opacity: 0.7 },
  { y: SPECIMEN_BASELINE, delay: 0.35, color: paper.line, opacity: 1 },
  { y: 96, delay: 0.45, color: paper.sepiaFaint, opacity: 0.7 },
];

function FontSpecimen() {
  return (
    <Box
      component="svg"
      viewBox={`0 0 ${SPECIMEN_VB.w} ${SPECIMEN_VB.h}`}
      role="img"
      aria-label={HERO_WORD}
      sx={{ width: '100%', maxWidth: { xs: 360, md: 520 }, height: 'auto', display: 'block', overflow: 'visible' }}
    >
      <defs>
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
        {HERO_WORD}
      </Box>
    </Box>
  );
}

// Hero specimen — the word written live with the synthesis engine onto a
// Sütterlin lineature, the project's whole thesis in one stroke. The engine is
// the lead; the font specimen is a graceful fallback (see FontSpecimen).
export function HeroSpecimen() {
  // 'probe' renders the engine off-screen to learn whether the word resolves;
  // it then promotes to 'engine' (real, animated) or falls back to 'fallback'.
  const [phase, setPhase] = useState<'probe' | 'engine' | 'fallback'>('probe');
  // Bumping this remounts the active specimen so its write-in replays.
  const [replayKey, setReplayKey] = useState(0);

  const handleResolved = useCallback(
    ({ missing, rendered }: { missing: string[]; rendered: number }) => {
      // Only the probe decides the phase; later resolves (the visible engine) are no-ops.
      setPhase((p) => (p !== 'probe' ? p : missing.length === 0 && rendered > 0 ? 'engine' : 'fallback'));
    },
    [],
  );
  const handleError = useCallback(() => setPhase((p) => (p === 'probe' ? 'fallback' : p)), []);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', mt: { xs: 1, md: 0 } }}>
      <Box sx={{ position: 'relative', width: '100%', maxWidth: { xs: 360, md: 520 }, minHeight: { xs: 96, md: 132 } }}>
        {/* Probe (off-screen) + the visible engine specimen share the cache, so the
            promotion to 'engine' renders instantly from the already-fetched data. */}
        {phase !== 'fallback' && (
          <Box
            sx={
              phase === 'probe'
                ? { position: 'absolute', width: 1, height: 1, overflow: 'hidden', opacity: 0, pointerEvents: 'none' }
                : undefined
            }
            aria-hidden={phase === 'probe' ? true : undefined}
          >
            <WrittenWord
              key={`engine-${phase}-${replayKey}`}
              text={HERO_WORD}
              height={132}
              durationMs={2400}
              maxWidth={520}
              onResolved={handleResolved}
              onError={handleError}
            />
          </Box>
        )}
        {/* While the engine probes (and on fallback) the font specimen is the
            visible content, so the hero is never blank during a cold-start fetch.
            It's replaced the moment the engine confirms a full render. */}
        {phase !== 'engine' && (
          <Box key={`font-${replayKey}`}>
            <FontSpecimen />
          </Box>
        )}
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
