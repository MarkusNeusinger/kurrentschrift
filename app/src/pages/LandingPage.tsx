// LandingPage — kurrentschrift.ink public landing.
//
// "Paper & ink" identity (deliberately NOT the anyplot/pyplots palette): aged cream
// paper, aged iron-gall brown as the writing ink, viridian as the single sparing
// accent. Composition follows docs/reference/kurrentschrift-landing.html: a sticky
// blurred nav (PublicHeader) + a two-column hero — editorial copy on the left, a
// giant GL-GermanCursive specimen ("Kurrent") that writes itself on the right —
// then the live tools, the ductus pipeline and the honest "bald" roadmap.
//
// Headlines/brand use Cormorant Garamond (`display`); body/eyebrow use EB Garamond
// (`garamond`); the showpiece uses GL-GermanCursive (`script`). All honour
// prefers-reduced-motion. The paper atmosphere (gradient + grain + vignette) is
// shared via <PaperBackground> so the same look carries across every page; only
// the work surfaces (A4 preview, letter crops, chart scan) stay neutral.

import { useEffect, useRef, useState, type ReactNode } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Box, Container, Link, Stack, Typography } from '@mui/material';
import { keyframes } from '@mui/system';

import { PaperBackground } from '@/components/PaperBackground';
import { PublicHeader } from '@/components/PublicHeader';
import { paths } from '@/routes/paths';
import { display, garamond, paper, script } from '@/styles/paper';

// --- animations -----------------------------------------------------------
const writeIn = keyframes`from { clip-path: inset(0 100% 0 0); } to { clip-path: inset(0 0 0 0); }`;
// Only a `to` rule: the draw-in starts from each line's own strokeDashoffset
// (set to SPECIMEN_VB.w below), so nothing here is coupled to the viewBox width.
const drawStroke = keyframes`to { stroke-dashoffset: 0; }`;
const fadeUp = keyframes`from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: none; }`;
const fadeIn = keyframes`from { opacity: 0; } to { opacity: 1; }`;
const reduce = '@media (prefers-reduced-motion: reduce)';

// on-load entrance for the hero copy (staggered), reduced-motion safe
const fu = (delay: number) => ({
  opacity: 0,
  animation: `${fadeUp} .9s cubic-bezier(.2,.7,.2,1) ${delay}s both`,
  [reduce]: { opacity: 1, transform: 'none', animation: 'none' },
});
// delayed fade-in for the specimen sub-line + caption
const fi = (delay: number) => ({
  opacity: 0,
  animation: `${fadeIn} 1s ease ${delay}s forwards`,
  [reduce]: { opacity: 1, animation: 'none' },
});

// Tools that exist today → real RouterLinks. Staged features → "bald", no link.
const tools = [
  {
    title: 'Lineatur-Vorlage',
    to: paths.worksheet,
    cta: 'Übungsblatt erstellen →',
    desc: 'Hilfslinien für deutsche Schreibschrift auf A4 — Verhältnis frei wählbar, optional Schräglinien, als druckfertiges PDF.',
  },
  {
    title: 'Buchstaben-Quiz',
    to: paths.quiz,
    cta: 'Quiz starten →',
    desc: 'Lies echte Kurrent-Buchstaben aus historischer Vorlage; am Ende zeigt die Auswertung, was dir schwerfiel.',
  },
];

const roadmap = [
  { title: 'Einstieg & Alphabet', desc: 'Geschichte in zwei Sätzen, Alphabet-Tafel, die wichtigsten Regeln.' },
  { title: 'Animierte Tafel', desc: 'Schreibreihenfolge, Ansatzpunkte und Schwellzug-Aufbau live.' },
  { title: 'Lese-Lupe', desc: 'Historische Scans transkribiert, mit Erklärung pro Buchstabe.' },
  { title: 'Schrift-Analyse', desc: 'Statistik über die eigene Hand — Schräglage, Schwellzug, Verteilung.' },
  { title: 'Offene Daten', desc: 'Kanonische Glyph-Daten — Anker, Schwellzug, Ductus — zitierbar.' },
];

// The thesis — the three-way combination that makes this project different. Vision
// prose (not interactive promises); what's usable today lives under "Jetzt schon
// nutzbar", planned work under "In Arbeit".
const pillars = [
  { num: 'i.', title: 'Tinte statt Font', desc: 'Schwellzug, Schreibreihenfolge und Allographen — Hand-Synthese, keine Glyphe pro Codepoint.' },
  { num: 'ii.', title: 'Statistik statt Bauchgefühl', desc: 'Schräglage, Schwellzug-Profile und Glyph-Verteilung der eigenen Schrift, gemessen statt geschätzt.' },
  { num: 'iii.', title: 'Lineatur zum Text', desc: 'Beliebiger Text mit passender Lineatur in einem Schritt — druckbare Vorlagen, inhaltsbewusst.' },
];

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

// Small scroll-reveal wrapper (IntersectionObserver, fires once).
function Reveal({ children, delay = 0 }: { children: ReactNode; delay?: number }) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [shown, setShown] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) {
          setShown(true);
          io.disconnect();
        }
      },
      { threshold: 0.18 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    <Box
      ref={ref}
      sx={{
        opacity: shown ? 1 : 0,
        transform: shown ? 'none' : 'translateY(22px)',
        transition: `opacity .8s ease ${delay}s, transform .8s cubic-bezier(.2,.7,.2,1) ${delay}s`,
        [reduce]: { opacity: 1, transform: 'none' },
      }}
    >
      {children}
    </Box>
  );
}

export function LandingPage() {
  // Bumping this remounts the script word so its write-in animation replays.
  const [replayKey, setReplayKey] = useState(0);

  return (
    <PaperBackground>
      <PublicHeader tone="paper" />

      {/* hero — copy left, giant script specimen right */}
      <Container maxWidth="lg" component="section" sx={{ position: 'relative', zIndex: 1, px: { xs: 2.5, sm: 4, md: 6 } }}>
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', md: '1.05fr 0.95fr' },
            gap: { xs: 4, md: 6 },
            alignItems: 'center',
            minHeight: { md: 'calc(100vh - 160px)' },
            py: { xs: 4, md: 5 },
          }}
        >
          {/* left: editorial copy */}
          <Box>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.7rem',
                mb: '1.4rem',
                color: paper.sepia,
                fontStyle: 'italic',
                fontSize: '1.02rem',
                letterSpacing: '0.06em',
                ...fu(0.05),
              }}
            >
              <Box component="span" sx={{ width: 42, height: '1px', bgcolor: paper.sepia }} />
              Gotische Kursive · seit jeher von Hand
            </Box>

            <Typography
              component="h1"
              sx={{
                fontFamily: display,
                fontWeight: 500,
                fontSize: 'clamp(2.5rem, 5.4vw, 4.4rem)',
                lineHeight: 1.04,
                letterSpacing: '-0.01em',
                color: paper.ink,
                mb: '1.5rem',
                ...fu(0.18),
              }}
            >
              In echter Tinte<br />
              geschrieben.<br />
              <Box component="em" sx={{ fontStyle: 'italic', color: paper.viridian }}>
                Nicht
              </Box>{' '}
              als Font gesetzt.
            </Typography>

            <Typography
              sx={{
                fontSize: 'clamp(1.08rem, 1.5vw, 1.3rem)',
                maxWidth: '42ch',
                color: paper.inkSoft,
                lineHeight: 1.6,
                mb: '2.3rem',
                ...fu(0.32),
              }}
            >
              Eine offene Bibliothek der deutschen Kurrentschrift —{' '}
              <Box component="b" sx={{ fontWeight: 600, color: paper.ink }}>
                kein Font, sondern der Schreibvorgang selbst
              </Box>
              : Geometrie aus historischen Vorlagen, Strichreihenfolge aus handkuratiertem Ductus.
            </Typography>

            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center', ...fu(0.46) }}>
              <Box
                component={RouterLink}
                to={paths.worksheet}
                sx={{
                  fontFamily: garamond,
                  fontSize: '1.06rem',
                  px: '1.6rem',
                  py: '0.85rem',
                  borderRadius: '2px',
                  bgcolor: paper.ink,
                  color: paper.hi,
                  textDecoration: 'none',
                  boxShadow: '0 2px 0 rgba(0,0,0,.2)',
                  transition: 'transform .2s ease, box-shadow .3s ease, background .3s ease',
                  '&:hover': { bgcolor: '#000', transform: 'translateY(-2px)', boxShadow: '0 8px 22px rgba(36,26,16,.4)' },
                }}
              >
                Schreiben üben
              </Box>
              <Box
                component={RouterLink}
                to={paths.quiz}
                sx={{
                  fontFamily: garamond,
                  fontSize: '1.06rem',
                  color: paper.inkSoft,
                  textDecoration: 'none',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  transition: 'color .25s ease',
                  '& .arrow': { color: paper.viridian, transition: 'transform .25s ease' },
                  '&:hover': { color: paper.ink },
                  '&:hover .arrow': { transform: 'translateX(5px)' },
                }}
              >
                Buchstaben lesen{' '}
                <Box component="span" className="arrow">
                  →
                </Box>
              </Box>
            </Box>
          </Box>

          {/* right (below the copy on phones): the word written onto a real Kurrent
              lineature. Rendered as SVG so the baseline is an exact coordinate and
              the ascenders land on the Oberlinie regardless of viewport/font box. */}
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', mt: { xs: 1, md: 0 } }}>
            <Box
              key={`word-${replayKey}`}
              component="svg"
              viewBox={`0 0 ${SPECIMEN_VB.w} ${SPECIMEN_VB.h}`}
              role="img"
              aria-label="Kurrent"
              sx={{
                width: '100%',
                maxWidth: { xs: 360, md: 520 },
                height: 'auto',
                display: 'block',
                overflow: 'visible',
              }}
            >
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
                sx={{
                  fontFamily: script,
                  fontSize: 100,
                  fill: paper.ink,
                  clipPath: 'inset(0 100% 0 0)',
                  animation: `${writeIn} 1.9s cubic-bezier(.6,.02,.2,1) .5s forwards`,
                  [reduce]: { clipPath: 'none', animation: 'none' },
                }}
              >
                Kurrent
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
              leſen · ſchreiben · verſtehen
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
              <Box component="span">Synthese in echter Hand — hier: Loth, 1866.</Box>
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
                ↻ nochmal schreiben
              </Box>
            </Box>
          </Box>
        </Box>
      </Container>

      {/* thesis — three pillars, framed as the goal (not as shipped features) */}
      <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1, px: { xs: 2.5, sm: 4, md: 6 }, pt: { xs: 4, md: 6 } }}>
        <Typography variant="overline" sx={{ color: paper.sepia, display: 'block', mb: 2.5 }}>
          Wohin das Projekt zielt
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, borderTop: `1px solid ${paper.line}` }}>
          {pillars.map((p, i) => (
            <Reveal key={p.title} delay={i * 0.06}>
              <Box
                sx={{
                  height: '100%',
                  px: { xs: 0, md: 3 },
                  py: { xs: 2.5, md: 3 },
                  borderTop: { xs: i > 0 ? `1px solid ${paper.line}` : 'none', md: 'none' },
                  borderLeft: { md: i > 0 ? `1px solid ${paper.line}` : 'none' },
                }}
              >
                <Box sx={{ fontFamily: display, fontStyle: 'italic', fontWeight: 500, color: paper.viridian, fontSize: '1.1rem', mb: '0.8rem' }}>{p.num}</Box>
                <Typography sx={{ fontFamily: display, fontWeight: 600, fontSize: '1.5rem', color: paper.ink, mb: '0.5rem', lineHeight: 1.1 }}>
                  {p.title}
                </Typography>
                <Typography sx={{ color: paper.inkSoft, fontSize: '1.02rem', maxWidth: '30ch', lineHeight: 1.55 }}>{p.desc}</Typography>
              </Box>
            </Reveal>
          ))}
        </Box>
      </Container>

      {/* lower sections — live tools, pipeline, roadmap, footer */}
      <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1, px: { xs: 2.5, sm: 4, md: 6 }, pt: { xs: 6, md: 8 }, pb: { xs: 6, md: 9 } }}>
        {/* live tools */}
        <Box sx={{ pt: { xs: 2, md: 3 } }}>
          <Typography variant="overline" sx={{ color: paper.sepia, display: 'block', mb: 2 }}>
            Jetzt schon nutzbar
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2.5 }}>
            {tools.map((t, i) => (
              <Reveal key={t.to} delay={i * 0.08}>
                <Box
                  component={RouterLink}
                  to={t.to}
                  sx={{
                    display: 'block',
                    height: '100%',
                    textDecoration: 'none',
                    color: paper.ink,
                    p: 3,
                    borderRadius: '3px',
                    border: `1px solid ${paper.line}`,
                    bgcolor: 'rgba(255,255,255,0.18)',
                    transition: 'transform .2s ease, box-shadow .3s ease, border-color .2s ease',
                    '&:hover': { transform: 'translateY(-3px)', boxShadow: '0 12px 30px rgba(36,26,16,.16)', borderColor: paper.viridian },
                  }}
                >
                  <Typography sx={{ fontFamily: display, fontWeight: 600, fontSize: '1.6rem', mb: 0.75 }}>{t.title}</Typography>
                  <Typography sx={{ color: paper.inkSoft, lineHeight: 1.6, mb: 1.5 }}>{t.desc}</Typography>
                  <Typography sx={{ color: paper.viridian, fontWeight: 500 }}>{t.cta}</Typography>
                </Box>
              </Reveal>
            ))}
          </Box>
        </Box>

        {/* roadmap — staged honestly, no dead links */}
        <Box sx={{ mt: { xs: 6, md: 9 } }}>
          <Typography variant="overline" sx={{ color: paper.sepia, display: 'block', mb: 2 }}>
            In Arbeit
          </Typography>
          <Stack spacing={0}>
            {roadmap.map((r, i) => (
              <Reveal key={r.title} delay={i * 0.05}>
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: { xs: 'column', sm: 'row' },
                    alignItems: { sm: 'baseline' },
                    gap: { xs: 0.5, sm: 1.5 },
                    py: 1.25,
                    borderBottom: `1px solid ${paper.line}`,
                  }}
                >
                  {/* title + badge share one line on mobile, badge moves to the far right on sm+ */}
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'baseline',
                      justifyContent: 'space-between',
                      gap: 1.5,
                      width: { xs: '100%', sm: 'auto' },
                    }}
                  >
                    <Typography sx={{ fontFamily: display, fontWeight: 600, fontSize: '1.2rem', color: paper.ink, minWidth: { sm: 210 } }}>
                      {r.title}
                    </Typography>
                    <Box component="span" sx={{ display: { xs: 'inline', sm: 'none' }, fontStyle: 'italic', fontSize: '.85rem', color: paper.sepiaFaint, whiteSpace: 'nowrap' }}>
                      bald
                    </Box>
                  </Box>
                  <Typography variant="body2" sx={{ color: paper.inkSoft, flex: 1 }}>
                    {r.desc}
                  </Typography>
                  <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' }, fontStyle: 'italic', fontSize: '.85rem', color: paper.sepiaFaint, whiteSpace: 'nowrap' }}>
                    bald
                  </Box>
                </Box>
              </Reveal>
            ))}
          </Stack>
        </Box>

        {/* footer */}
        <Box
          sx={{
            mt: { xs: 7, md: 10 },
            pt: 4,
            borderTop: `1px solid ${paper.line}`,
            display: 'flex',
            flexDirection: { xs: 'column', sm: 'row' },
            justifyContent: 'space-between',
            alignItems: { xs: 'flex-start', sm: 'flex-end' },
            gap: 2,
          }}
        >
          <Box>
            <Typography sx={{ fontFamily: garamond, fontStyle: 'italic', color: paper.inkSoft, fontSize: '1.1rem' }}>
              Kurrent · Sütterlin · Offenbacher Schrift
            </Typography>
            <Typography variant="caption" sx={{ color: paper.sepia, fontStyle: 'italic' }}>
              Synthese, klar gekennzeichnet — wir simulieren Schrift, nicht Provenienz.
            </Typography>
          </Box>
          <Link
            href="https://github.com/MarkusNeusinger/kurrentschrift"
            target="_blank"
            rel="noopener"
            variant="body2"
            sx={{ color: paper.sepia, textDecoration: 'none', '&:hover': { color: paper.viridian } }}
          >
            GitHub
          </Link>
        </Box>
      </Container>
    </PaperBackground>
  );
}

// Default export for React.lazy route splitting (routes/sections).
export default LandingPage;
