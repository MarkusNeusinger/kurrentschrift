// HeroWritten — the single-column landing hero. A large brand word
// ("Kurrentſchrift") is written left-to-right by a travelling pen nib (a
// clip-path reveal synced to the nib), then a viridian flourish underlines it;
// a Playfair headline, a short lead and the two area CTAs follow. Deliberately
// minimalist — no eyebrow. prefers-reduced-motion shows the finished word at rest.
//
// The word is rendered in the GL-GermanCursive show-script (`script`) as a
// MARKED specimen (legibility rule: historic forms only as specimen, never as
// reading text). It is kept behind <HeroWord> so a later switch to the live
// WrittenWord engine is a one-component change — decision: font first, engine
// once the Sütterlin synthesis is good enough for a 14-glyph word.

import { useState } from 'react';
import { Box, Typography } from '@mui/material';
import { keyframes } from '@mui/system';
import { Link as RouterLink } from 'react-router-dom';

import { PageContainer } from '@/components/PageContainer';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion';
import { de } from '@/locales';
import { paths } from '@/routes/paths';
import { display, garamond, letterpress, paper, script } from '@/styles/paper';

const t = de.landing.hero;
const reduce = '@media (prefers-reduced-motion: reduce)';

// How long the pen takes to write the whole word.
const WRITE_MS = 3200;

// The word reveals left→right (the right inset shrinks from full to none).
const reveal = keyframes`from { clip-path: inset(-8% 100% -20% -4%); } to { clip-path: inset(-8% -4% -20% -4%); }`;
// The nib rides the reveal edge, fading in at the first stroke and out at the last.
const nibTravel = keyframes`
  0% { left: -2%; opacity: 0; }
  7% { opacity: 1; }
  90% { opacity: 1; }
  100% { left: 99%; opacity: 0; }
`;
const flourishDraw = keyframes`to { stroke-dashoffset: 0; }`;
// `visibility` flips hidden→visible at the animation start (delay end), so the
// element is out of the tab order while it's invisible — a keyboard user can't
// focus a CTA/replay that hasn't appeared yet (with `both`, the `from` state
// holds during the delay). Discrete property: it just snaps on as the fade begins.
const rise = keyframes`from { opacity: 0; visibility: hidden; transform: translateY(14px); } to { opacity: 1; visibility: visible; transform: none; }`;

// Staggered entrance for the supporting copy. Deliberately starts early (the
// word keeps writing behind it) so the hero is usable at once, not after 3s.
const riseIn = (delay: number) => ({
  opacity: 0,
  animation: `${rise} .8s cubic-bezier(.2,.7,.2,1) ${delay}s both`,
  [reduce]: { opacity: 1, transform: 'none', animation: 'none' },
});

// The pen nib (lifted from the design mockup): ink body, cream eye + slit, a
// small metal tip. Sized in `em` so it scales with the word's font-size.
function NibSvg() {
  return (
    <Box
      component="svg"
      viewBox="-54 -8 108 352"
      aria-hidden
      sx={{
        height: '0.7em',
        width: 'auto',
        display: 'block',
        transform: 'rotate(-20deg)',
        transformOrigin: 'bottom center',
        filter: 'drop-shadow(0 2px 2px rgba(36,26,16,.28))',
      }}
    >
      <path
        d="M0 0 C-26 0 -44 60 -44 150 L-44 230 C-44 274 -18 312 0 330 C18 312 44 274 44 230 L44 150 C44 60 26 0 0 0 Z"
        fill={paper.ink}
      />
      <circle cx="0" cy="128" r="13" fill={paper.bg} />
      <line x1="0" y1="146" x2="0" y2="300" stroke={paper.bg} strokeWidth="6" strokeLinecap="round" />
      <path d="M-9 304 L0 340 L9 304 Z" fill="#b9892f" />
    </Box>
  );
}

// The written brand word + nib + flourish. Remounted (via `runKey`) to replay.
// This is the engine-swap seam: today it renders the GLKurrent font; later it
// can render the live WrittenWord engine without touching the rest of the hero.
function HeroWord({ runKey }: { runKey: number }) {
  return (
    <Box
      key={runKey}
      sx={{
        position: 'relative',
        display: 'inline-block',
        // The font-size drives the whole composition (word + nib + flourish).
        fontSize: 'clamp(2.8rem, 10vw, 9rem)',
        lineHeight: 1,
        mx: 'auto',
      }}
    >
      <Box
        component="span"
        role="img"
        aria-label={t.wordAria}
        title={t.wordAria}
        sx={{
          fontFamily: script,
          color: paper.ink,
          display: 'inline-block',
          px: '0.06em',
          textShadow: letterpress,
          clipPath: 'inset(-8% 100% -20% -4%)',
          animation: `${reveal} ${WRITE_MS}ms linear forwards`,
          [reduce]: { clipPath: 'none', animation: 'none' },
        }}
      >
        {t.word}
      </Box>

      {/* travelling nib — its tip rides the reveal edge along the baseline */}
      <Box
        aria-hidden
        sx={{
          position: 'absolute',
          left: '-2%',
          bottom: '0.04em',
          animation: `${nibTravel} ${WRITE_MS}ms linear forwards`,
          [reduce]: { display: 'none' },
        }}
      >
        <NibSvg />
      </Box>

      {/* viridian flourish swash, drawn just as the word finishes */}
      <Box
        component="svg"
        aria-hidden
        viewBox="0 0 1000 60"
        preserveAspectRatio="none"
        sx={{ position: 'absolute', left: '-3%', width: '106%', bottom: '-0.18em', height: '0.36em', overflow: 'visible' }}
      >
        <Box
          component="path"
          d="M8 42 C220 8 520 10 742 30 C840 38 922 36 992 20"
          sx={{
            fill: 'none',
            stroke: paper.viridian,
            strokeWidth: 7,
            strokeLinecap: 'round',
            strokeDasharray: 1200,
            strokeDashoffset: 1200,
            animation: `${flourishDraw} 900ms cubic-bezier(.6,.02,.2,1) ${WRITE_MS - 350}ms forwards`,
            [reduce]: { strokeDashoffset: 0, animation: 'none' },
          }}
        />
      </Box>
    </Box>
  );
}

export function HeroWritten() {
  const [runKey, setRunKey] = useState(0);
  const reduced = usePrefersReducedMotion();

  return (
    <PageContainer
      width="wide"
      component="section"
      sx={{ textAlign: 'center', pt: { xs: 5, md: 8 }, pb: { xs: 4, md: 6 } }}
    >
      <HeroWord runKey={runKey} />

      <Typography
        sx={{
          fontFamily: garamond,
          fontStyle: 'italic',
          color: paper.sepia,
          fontSize: '1.05rem',
          mt: { xs: 2.5, md: 3.5 },
          ...riseIn(0.2),
        }}
      >
        {t.wordCaption}
      </Typography>

      <Typography
        component="h1"
        variant="h2"
        sx={{
          fontFamily: display,
          fontWeight: 600,
          color: paper.ink,
          textShadow: letterpress,
          maxWidth: '22ch',
          mx: 'auto',
          mt: { xs: 2.5, md: 3 },
          textWrap: 'balance',
          ...riseIn(0.35),
        }}
      >
        {t.title}
      </Typography>

      <Typography
        variant="body1"
        sx={{ color: paper.inkSoft, maxWidth: '44rem', mx: 'auto', mt: 2, ...riseIn(0.5) }}
      >
        {t.leadBeforeBold}{' '}
        <Box component="b" sx={{ fontWeight: 600, color: paper.ink }}>
          {t.leadBold}
        </Box>
        {t.leadAfterBold}
      </Typography>

      <Box
        sx={{
          display: 'flex',
          gap: 2,
          justifyContent: 'center',
          alignItems: 'center',
          flexWrap: 'wrap',
          mt: { xs: 3.5, md: 4 },
          ...riseIn(0.65),
        }}
      >
        <Box
          component={RouterLink}
          to={paths.lesen}
          sx={{
            fontFamily: garamond,
            fontSize: '1.2rem',
            px: '2.4rem',
            py: '0.6rem',
            borderRadius: '8px',
            bgcolor: paper.viridian,
            color: paper.hi,
            textDecoration: 'none',
            boxShadow: '0 2px 0 rgba(0,0,0,.18)',
            transition: 'transform .2s, box-shadow .3s, filter .3s',
            '&:hover': { filter: 'brightness(1.06)', transform: 'translateY(-2px)', boxShadow: '0 10px 24px rgba(64,130,109,.34)' },
          }}
        >
          {t.ctaRead}
        </Box>
        <Box
          component={RouterLink}
          to={paths.schreiben}
          sx={{
            fontFamily: garamond,
            fontSize: '1.2rem',
            color: paper.inkSoft,
            textDecoration: 'none',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            transition: 'color .25s',
            '& .arrow': { color: paper.viridian, transition: 'transform .25s' },
            '&:hover': { color: paper.ink },
            '&:hover .arrow': { transform: 'translateX(5px)' },
          }}
        >
          {t.ctaWrite}{' '}
          <Box component="span" className="arrow">
            →
          </Box>
        </Box>
      </Box>

      {!reduced && (
        <Box
          component="button"
          type="button"
          onClick={() => setRunKey((k) => k + 1)}
          sx={{
            display: 'block',
            mx: 'auto',
            mt: { xs: 3, md: 3.5 },
            cursor: 'pointer',
            border: 'none',
            bgcolor: 'transparent',
            color: paper.sepia,
            fontFamily: garamond,
            fontStyle: 'italic',
            fontSize: '0.9rem',
            opacity: 0,
            animation: `${rise} .8s ease 0.85s both`,
            transition: 'color .25s',
            '&:hover': { color: paper.viridian },
          }}
        >
          {t.replay}
        </Box>
      )}
    </PageContainer>
  );
}
