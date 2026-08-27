// HeroWritten — the single-column landing hero. The brand word
// ("Kurrentſchrift") is written live by the synthesis engine (<WrittenWord>,
// GET /write/word — the same Sütterlin ductus that writes /federprobe), then a
// viridian flourish underlines it; a Playfair headline, a short lead and the
// two area CTAs follow. Deliberately minimalist — no eyebrow.
//
// Engine-first, and the engine gets as long as it needs (owner decision
// 2026-08-27, replacing the earlier 2.5 s cold-start timer): a WRITTEN word is
// the whole point of the hero, so a slow backend means waiting — the reserved
// word area holds its space, and after a short moment a quiet patience line
// appears under the spinner. Only a genuine failure falls back to the
// GL-GermanCursive show-font wipe with the travelling nib: a fetch error after
// the cold-start retries, or a composition with missing glyphs. The caption
// switches with the mode, so the page never claims a live synthesis over a
// static font. prefers-reduced-motion shows the finished word at rest in both
// modes. index.html preloads the composition on `/`, so the wait is rare and
// short in production.

import { useCallback, useState } from 'react';
import { Box, Typography } from '@mui/material';
import { keyframes } from '@mui/system';
import { Link as RouterLink } from 'react-router-dom';

import { PageContainer } from '@/components/PageContainer';
import { WrittenWord } from '@/components/WrittenWord';
import { useElementSize } from '@/hooks/useElementSize';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion';
import { de } from '@/locales';
import { paths } from '@/routes/paths';
import { display, garamond, letterpress, paper, script } from '@/styles/paper';

const t = de.landing.hero;
const reduce = '@media (prefers-reduced-motion: reduce)';

// How long the fallback pen takes to wipe the whole word (the engine mode gets
// its timing from the composition itself via onResolved.writeEndMs).
const WRITE_MS = 3200;
// Width/height ratio of the composed brand word (bounds of
// /write/word?text=Kurrentſchrift incl. the renderer's padding, checked
// 2026-08-27) — reserves the word area BEFORE the payload arrives so neither
// the engine nor the fallback shifts the copy below (CLS). Drift after a
// re-authoring is harmless: the svg centres in the reserved box either way.
const HERO_WORD_ASPECT = 5.4;
// Cap the engine word so it matches the fallback's presence (9rem show-font)
// instead of bleeding across the full `wide` container on desktop.
const HERO_MAX_W = 880;
// The flourish starts this long before the word finishes — the underline swash
// begins while the last letter is still completing, like a real signature.
const FLOURISH_LEAD_MS = 350;

type HeroPhase = 'pending' | 'engine' | 'font';

// The fallback word reveals left→right (the right inset shrinks from full to none).
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
        transform: 'rotate(-158deg)',
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

// The viridian underline swash, drawn just as the word finishes. Positioned in
// % of the word box so it serves both modes (the em-based fallback and the
// px-sized engine svg alike).
function Flourish({ delayMs }: { delayMs: number }) {
  return (
    <Box
      component="svg"
      aria-hidden
      viewBox="0 0 1000 60"
      preserveAspectRatio="none"
      sx={{
        position: 'absolute',
        left: '-1%',
        width: '102%',
        // Low enough that the swash only grazes the deepest descenders (ſ, f)
        // instead of striking through them — tuned against screenshots of the
        // composed word at 1440 and 390.
        bottom: '-8%',
        height: '14%',
        overflow: 'visible',
        pointerEvents: 'none',
      }}
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
          animation: `${flourishDraw} 900ms cubic-bezier(.6,.02,.2,1) ${delayMs}ms forwards`,
          [reduce]: { strokeDashoffset: 0, animation: 'none' },
        }}
      />
    </Box>
  );
}

// The show-font fallback: the GLKurrent specimen wiped in left→right by the
// travelling nib (the pre-engine hero, kept verbatim as the cold-start path).
function FontWord() {
  return (
    <Box
      sx={{
        position: 'relative',
        display: 'inline-block',
        // The font-size drives word + nib together. A steep vw term lets the
        // word grow into the column on phones (measured to stay within it down
        // to 320px); the 9rem cap keeps desktop calm, the 3rem floor protects
        // the very narrowest screens.
        fontSize: 'clamp(3rem, 15.5vw, 9rem)',
        lineHeight: 1,
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
          // block, not inline-block: an inline-block child adds the wrapper's
          // baseline strut below it (~0.26em), which silently stretched the
          // reserved hero box past its aspect ratio in fallback mode.
          display: 'block',
          px: '0.06em',
          textShadow: letterpress,
          clipPath: 'inset(-8% 100% -20% -4%)',
          animation: `${reveal} ${WRITE_MS}ms linear forwards`,
          [reduce]: { clipPath: 'none', animation: 'none' },
        }}
      >
        {t.word}
      </Box>

      {/* travelling nib — rides the reveal edge left→right "writing" the word at
          the tuned angle (NibSvg rotate), fading in/out; hidden for reduced-motion. */}
      <Box
        aria-hidden
        sx={{
          position: 'absolute',
          left: '-2%',
          bottom: '0.4em',
          animation: `${nibTravel} ${WRITE_MS}ms linear forwards`,
          [reduce]: { display: 'none' },
        }}
      >
        <NibSvg />
      </Box>
    </Box>
  );
}

// The written brand word + flourish. Remounted (via `runKey`) to replay. The
// box reserves the word's aspect before any payload arrives; the engine svg is
// sized to fill it exactly (height from the measured width), the fallback
// centres its em-sized word in the same space.
function HeroWord({
  runKey,
  phase,
  flourishDelayMs,
  onResolved,
  onError,
}: {
  runKey: number;
  phase: HeroPhase;
  flourishDelayMs: number | null;
  onResolved: (info: { missing: string[]; rendered: number; writeEndMs: number }) => void;
  onError: () => void;
}) {
  const [box, setBox] = useState<HTMLElement | null>(null);
  const { w } = useElementSize(box);
  const height = w > 0 ? Math.round(w / HERO_WORD_ASPECT) : 0;

  return (
    <Box
      ref={setBox}
      sx={{
        position: 'relative',
        width: '100%',
        maxWidth: HERO_MAX_W,
        mx: 'auto',
        aspectRatio: `${HERO_WORD_ASPECT}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {phase === 'font' ? (
        <FontWord key={runKey} />
      ) : (
        // Mounted during `pending` too — the mount is what starts the fetch
        // (answered by the render cache / the index.html preload).
        height > 0 && (
          <WrittenWord
            key={runKey}
            text={t.word}
            height={height}
            maxWidth={w}
            showLineature={false}
            ariaLabel={t.wordAria}
            onResolved={onResolved}
            onError={onError}
          />
        )
      )}

      {/* the engine gets as long as it needs — after a short moment the wait
          says so quietly instead of swapping in a static font (owner decision
          2026-08-27). Pure CSS delay: no timer to clean up, and the line never
          shows on the fast path. */}
      {phase === 'pending' && (
        <Typography
          sx={{
            position: 'absolute',
            bottom: '6%',
            width: '100%',
            textAlign: 'center',
            fontFamily: garamond,
            fontStyle: 'italic',
            fontSize: '0.9rem',
            color: paper.sepia,
            ...riseIn(3),
          }}
        >
          {t.waiting}
        </Typography>
      )}

      {flourishDelayMs != null && <Flourish key={`f-${runKey}`} delayMs={flourishDelayMs} />}
    </Box>
  );
}

export function HeroWritten() {
  const [runKey, setRunKey] = useState(0);
  const [phase, setPhase] = useState<HeroPhase>('pending');
  const [engineEndMs, setEngineEndMs] = useState(0);
  const reduced = usePrefersReducedMotion();

  const onResolved = useCallback(({ missing, rendered, writeEndMs }: { missing: string[]; rendered: number; writeEndMs: number }) => {
    setEngineEndMs(writeEndMs);
    // A brand word with letters missing must not appear half-written — any
    // gap falls back to the complete show-font specimen.
    setPhase((p) => (p === 'font' ? p : missing.length || !rendered ? 'font' : 'engine'));
  }, []);
  const onError = useCallback(() => setPhase((p) => (p === 'pending' ? 'font' : p)), []);

  const flourishDelayMs =
    phase === 'font'
      ? WRITE_MS - FLOURISH_LEAD_MS
      : phase === 'engine' && engineEndMs > 0
        ? Math.max(0, engineEndMs - FLOURISH_LEAD_MS)
        : null;

  return (
    <PageContainer
      width="wide"
      component="section"
      sx={{ textAlign: 'center', pt: { xs: 5, md: 8 }, pb: { xs: 4, md: 6 } }}
    >
      <HeroWord
        runKey={runKey}
        phase={phase}
        flourishDelayMs={flourishDelayMs}
        onResolved={onResolved}
        onError={onError}
      />

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
        {/* the caption is honest about the mode: the engine claim appears only
            once the engine actually writes (pending/fallback show the generic
            specimen line). */}
        {phase === 'engine' ? t.wordCaptionEngine : t.wordCaption}
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
            '&:hover': { color: paper.viridianText },
          }}
        >
          {t.replay}
        </Box>
      )}
    </PageContainer>
  );
}
