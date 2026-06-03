// LandingPage — kurrentschrift.ink public landing.
//
// Distinct "paper & ink" identity (deliberately NOT the anyplot/pyplots token
// palette): aged cream paper, aged iron-gall brown as the writing ink, viridian
// as the single sparing accent (historic, chromium-oxide green). The hero word
// is set in GL-GermanCursive (German Kurrent/Sütterlin cursive by Gutenberg-Labo,
// free license — attribute in THIRD_PARTY_NOTICES.md) and "writes itself" via a
// CSS clip-path reveal, honoured by prefers-reduced-motion.
//
// The page is a showcase, not an app: it links out to the two tools that exist
// today (/schreiben, /quiz) and stages the rest of the vision as "bald" — no
// dead buttons. Keep the tool pages on the clean light theme so crops and the
// A4 preview stay legible; this expressive look lives on the landing only.
// Dialing this toward "option 3" = just turn the paper tokens / hero size down.
//
// Font asset: drop gl-germancursive.woff2 into src/assets/fonts/. The @font-face
// is declared below via <GlobalStyles>; no separate CSS file needed.

import { useEffect, useRef, useState, type ReactNode } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Box, Container, GlobalStyles, Link, Stack, Typography } from '@mui/material';
import { keyframes } from '@mui/system';

import kurrentWoff2 from '../assets/fonts/gl-germancursive.woff2';

// --- identity tokens (local to the landing, on purpose) -------------------
const paper = {
  bg: '#e7dabf',
  hi: '#f1e8d4',
  lo: '#d8c7a3',
  ink: '#241a10',
  inkSoft: '#473420',
  sepia: '#6f5230',
  sepiaFaint: '#9a8259',
  viridian: '#40826d',
  line: '#b6a079',
};
const garamond = "'EB Garamond', Georgia, 'Times New Roman', serif";
const script = "'GLKurrent', cursive";

// faint paper grain (greyscale fractal noise, multiplied over the warm base)
const GRAIN =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.05'/%3E%3C/svg%3E\")";

// --- animations -----------------------------------------------------------
const writeIn = keyframes`from { clip-path: inset(0 100% 0 0); } to { clip-path: inset(0 0 0 0); }`;
const drawLine = keyframes`from { transform: scaleX(0); } to { transform: scaleX(1); }`;
const reduce = '@media (prefers-reduced-motion: reduce)';

// The ductus pipeline (kept from the previous landing — the project's core
// explanation), condensed to four steps for the timeline.
const steps = [
  { step: 'Scannen', detail: 'Geometrie & Strichbreite aus der Vorlage' },
  { step: 'Fitten', detail: 'Ductus-Prior legt Reihenfolge & Kreuzungen fest' },
  { step: 'Mitteln', detail: 'viele Proben → deine persönliche Buchstabenform' },
  { step: 'Verbinden', detail: 'berechnete Übergänge statt Paar-Katalog' },
];

// Tools that exist today → real RouterLinks. Staged features → "bald", no link.
const tools = [
  {
    title: 'Lineatur-Vorlage',
    to: '/schreiben',
    cta: 'Übungsblatt erstellen →',
    desc: 'Hilfslinien für deutsche Schreibschrift auf A4 — Verhältnis frei wählbar, optional Schräglinien, als druckfertiges PDF.',
  },
  {
    title: 'Buchstaben-Quiz',
    to: '/quiz',
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
  return (
    <Box
      sx={{
        position: 'relative',
        minHeight: '100vh',
        color: paper.ink,
        bgcolor: paper.bg,
        fontFamily: garamond,
        backgroundImage: `radial-gradient(130% 90% at 50% -15%, ${paper.hi} 0%, ${paper.bg} 52%, ${paper.lo} 100%)`,
        // grain + vignette as fixed, non-interactive overlays
        '&::before': {
          content: '""',
          position: 'fixed',
          inset: 0,
          pointerEvents: 'none',
          zIndex: 0,
          backgroundImage: GRAIN,
          mixBlendMode: 'multiply',
          opacity: 0.5,
        },
        '&::after': {
          content: '""',
          position: 'fixed',
          inset: 0,
          pointerEvents: 'none',
          zIndex: 0,
          boxShadow: 'inset 0 0 200px rgba(60,40,20,.26)',
        },
      }}
    >
      <GlobalStyles
        styles={{
          '@font-face': {
            fontFamily: 'GLKurrent',
            src: `url(${kurrentWoff2}) format('woff2')`,
            fontDisplay: 'swap',
          },
        }}
      />

      <Container maxWidth="md" sx={{ position: 'relative', zIndex: 1, py: { xs: 5, md: 8 } }}>
        {/* slim header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: { xs: 5, md: 8 } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
            <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: paper.viridian }} />
            <Typography variant="overline" sx={{ color: paper.sepia, lineHeight: 1 }}>
              kurrentschrift.ink
            </Typography>
          </Box>
          <Stack direction="row" spacing={3} sx={{ fontSize: '1rem' }}>
            <Link component={RouterLink} to="/schreiben" sx={{ color: paper.inkSoft, textDecoration: 'none', '&:hover': { color: paper.viridian } }}>
              Schreiben
            </Link>
            <Link component={RouterLink} to="/quiz" sx={{ color: paper.inkSoft, textDecoration: 'none', '&:hover': { color: paper.viridian } }}>
              Lesen
            </Link>
          </Stack>
        </Box>

        {/* hero */}
        <Stack spacing={3.5}>
          <Typography
            component="h1"
            sx={{
              fontFamily: garamond,
              fontStyle: 'italic',
              fontWeight: 400,
              fontSize: { xs: '2.4rem', sm: '3.2rem' },
              lineHeight: 1.1,
              color: paper.ink,
              maxWidth: '18ch',
            }}
          >
            Wie aus Tinte Schrift wird.
          </Typography>

          {/* script showpiece on a ruled baseline, writes itself in */}
          <Box sx={{ position: 'relative', py: 2, my: 1 }}>
            {[18, 58, 78].map((top, i) => (
              <Box
                key={top}
                sx={{
                  position: 'absolute',
                  left: 0,
                  right: 0,
                  top: `${top}%`,
                  height: '1px',
                  bgcolor: i === 1 ? paper.sepiaFaint : paper.line,
                  transformOrigin: 'left',
                  transform: 'scaleX(0)',
                  animation: `${drawLine} .7s ease ${0.15 + i * 0.1}s forwards`,
                  [reduce]: { transform: 'scaleX(1)', animation: 'none' },
                }}
              />
            ))}
            <Box
              component="span"
              sx={{
                display: 'block',
                fontFamily: script,
                color: paper.ink,
                fontSize: { xs: '4.5rem', sm: '7rem' },
                lineHeight: 0.85,
                transform: 'rotate(-2deg)',
                transformOrigin: 'left',
                clipPath: 'inset(0 100% 0 0)',
                animation: `${writeIn} 1.9s cubic-bezier(.6,.02,.2,1) .5s forwards`,
                [reduce]: { clipPath: 'none', animation: 'none' },
              }}
            >
              Kurrent
            </Box>
          </Box>

          <Typography variant="body1" sx={{ color: paper.inkSoft, lineHeight: 1.7, maxWidth: '60ch', fontSize: '1.15rem' }}>
            Eine offene Bibliothek der deutschen Kurrentschrift — kein Font, sondern der Schreibvorgang selbst. Geometrie aus
            historischen Vorlagen, Strichreihenfolge aus einem handkuratierten Ductus. Lesen, animieren, neu schreiben.
          </Typography>
        </Stack>

        {/* live tools */}
        <Box sx={{ mt: { xs: 6, md: 9 } }}>
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
                  <Typography sx={{ fontFamily: garamond, fontWeight: 600, fontSize: '1.5rem', mb: 0.75 }}>{t.title}</Typography>
                  <Typography sx={{ color: paper.inkSoft, lineHeight: 1.6, mb: 1.5 }}>{t.desc}</Typography>
                  <Typography sx={{ color: paper.viridian, fontWeight: 500 }}>{t.cta}</Typography>
                </Box>
              </Reveal>
            ))}
          </Box>
        </Box>

        {/* how it works — ductus pipeline timeline */}
        <Box sx={{ mt: { xs: 6, md: 9 } }}>
          <Typography variant="overline" sx={{ color: paper.sepia, display: 'block', mb: 2 }}>
            In vier Schritten
          </Typography>
          <Box sx={{ position: 'relative', pl: 3 }}>
            <Box sx={{ position: 'absolute', left: 5, top: 6, bottom: 6, width: '1px', bgcolor: paper.line }} />
            <Stack spacing={2.5}>
              {steps.map(({ step, detail }, i) => (
                <Reveal key={step} delay={i * 0.06}>
                  <Box sx={{ position: 'relative' }}>
                    <Box
                      sx={{
                        position: 'absolute',
                        left: -23,
                        top: 5,
                        width: 9,
                        height: 9,
                        borderRadius: '50%',
                        bgcolor: paper.viridian,
                        boxShadow: `0 0 0 4px ${paper.bg}`,
                      }}
                    />
                    <Typography sx={{ color: paper.ink, fontWeight: 600, lineHeight: 1.3 }}>{step}</Typography>
                    <Typography variant="body2" sx={{ color: paper.inkSoft, lineHeight: 1.6 }}>{detail}</Typography>
                  </Box>
                </Reveal>
              ))}
            </Stack>
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
                <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1.5, py: 1.25, borderBottom: `1px solid ${paper.line}` }}>
                  <Typography sx={{ fontFamily: garamond, fontWeight: 600, fontSize: '1.1rem', color: paper.ink, minWidth: { sm: 210 } }}>
                    {r.title}
                  </Typography>
                  <Typography variant="body2" sx={{ color: paper.inkSoft, flex: 1 }}>
                    {r.desc}
                  </Typography>
                  <Box component="span" sx={{ fontStyle: 'italic', fontSize: '.85rem', color: paper.sepiaFaint, whiteSpace: 'nowrap' }}>
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
            justifyContent: 'space-between',
            alignItems: 'flex-end',
            flexWrap: 'wrap',
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
          <Stack direction="row" spacing={3} sx={{ alignItems: 'baseline' }}>
            <Link
              href="https://github.com/MarkusNeusinger/kurrentschrift"
              target="_blank"
              rel="noopener"
              variant="body2"
              sx={{ color: paper.sepia, textDecoration: 'none', '&:hover': { color: paper.viridian } }}
            >
              GitHub
            </Link>
            <Link
              component={RouterLink}
              to="/admin/chart"
              variant="caption"
              sx={{ color: paper.sepiaFaint, textDecoration: 'none', letterSpacing: '0.06em', '&:hover': { color: paper.viridian } }}
            >
              admin
            </Link>
          </Stack>
        </Box>
      </Container>
    </Box>
  );
}
