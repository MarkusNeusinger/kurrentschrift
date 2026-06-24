// LandingView — kurrentschrift.ink public landing.
//
// "Paper & ink" identity (deliberately NOT the anyplot/pyplots palette): aged cream
// paper, aged iron-gall brown as the writing ink, viridian as the single sparing
// accent. Composition follows docs/reference/kurrentschrift-landing.html: a sticky
// blurred nav (PublicHeader) + a two-column hero — editorial copy on the left, a
// giant GL-GermanCursive specimen ("Kurrent") that writes itself on the right —
// then the live tools, the ductus pipeline and the honest "bald" roadmap.
//
// Headlines/brand use Playfair Display (`display`); body/eyebrow use EB Garamond
// (`garamond`); the showpiece uses GL-GermanCursive (`script`). All honour
// prefers-reduced-motion. The paper atmosphere (gradient + grain + vignette) is
// shared via <PaperBackground> so the same look carries across every page; only
// the work surfaces (A4 preview, letter crops, chart scan) stay neutral.

import { Link as RouterLink } from 'react-router-dom';
import { Box, Link, Stack, Typography } from '@mui/material';
import { keyframes } from '@mui/system';

import { PageContainer } from '@/components/PageContainer';
import { PublicLayout } from '@/layouts/public/PublicLayout';
import { de } from '@/locales';
import { paths } from '@/routes/paths';
import { HeroSpecimen } from '@/sections/landing/HeroSpecimen';
import { Reveal } from '@/sections/landing/Reveal';
import { display, garamond, letterpress, paper } from '@/styles/paper';

// --- animations -----------------------------------------------------------
const fadeUp = keyframes`from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: none; }`;
const reduce = '@media (prefers-reduced-motion: reduce)';

// on-load entrance for the hero copy (staggered), reduced-motion safe
const fu = (delay: number) => ({
  opacity: 0,
  animation: `${fadeUp} .9s cubic-bezier(.2,.7,.2,1) ${delay}s both`,
  [reduce]: { opacity: 1, transform: 'none', animation: 'none' },
});

// Tools that exist today → real RouterLinks. Staged features → common.soon, no
// link. German copy lives in @/locales (landing.tools / landing.roadmap /
// landing.pillars); here we only attach the route targets.
const tools = [
  { ...de.landing.tools.worksheet, to: paths.worksheet },
  { ...de.landing.tools.scribe, to: paths.scribe },
  { ...de.landing.tools.quiz, to: paths.quiz },
];

const roadmap = de.landing.roadmap;

// The thesis — the three-way combination that makes this project different. Vision
// prose (not interactive promises); what's usable today lives under
// landing.toolsHeading, planned work under landing.roadmapHeading.
const pillars = de.landing.pillars;

export function LandingView() {
  return (
    <PublicLayout>
      {/* hero — copy left, giant script specimen right */}
      <PageContainer width="wide" component="section">
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
              {de.landing.hero.eyebrow}
            </Box>

            <Typography
              component="h1"
              variant="h1"
              sx={{
                fontFamily: display,
                fontWeight: 600,
                lineHeight: 1.04,
                letterSpacing: '-0.01em',
                color: paper.ink,
                textShadow: letterpress,
                mb: '1.5rem',
                ...fu(0.18),
              }}
            >
              {de.landing.hero.titleLine1}<br />
              {de.landing.hero.titleLine2}<br />
              <Box component="em" sx={{ fontStyle: 'italic', color: paper.viridian }}>
                {de.landing.hero.titleEm}
              </Box>{' '}
              {de.landing.hero.titleLine3}<br />
              {de.landing.hero.titleLine4}
            </Typography>

            <Typography
              sx={{
                maxWidth: '42ch',
                color: paper.inkSoft,
                lineHeight: 1.6,
                mb: '2.3rem',
                ...fu(0.32),
              }}
            >
              {de.landing.hero.leadBeforeBold}{' '}
              <Box component="b" sx={{ fontWeight: 600, color: paper.ink }}>
                {de.landing.hero.leadBold}
              </Box>
              {de.landing.hero.leadAfterBold}
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
                {de.landing.hero.ctaWrite}
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
                {de.landing.hero.ctaRead}{' '}
                <Box component="span" className="arrow">
                  →
                </Box>
              </Box>
            </Box>
          </Box>

          {/* right (below the copy on phones): the word written onto a real Kurrent
              lineature. Rendered as SVG so the baseline is an exact coordinate and
              the ascenders land on the Oberlinie regardless of viewport/font box. */}
          <HeroSpecimen />
        </Box>
      </PageContainer>

      {/* thesis — three pillars, framed as the goal (not as shipped features) */}
      <PageContainer width="wide" sx={{ pt: { xs: 4, md: 6 } }}>
        <Typography variant="overline" sx={{ color: paper.sepia, display: 'block', mb: 2.5 }}>
          {de.landing.pillarsHeading}
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
                <Typography variant="h4" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, textShadow: letterpress, mb: '0.5rem', lineHeight: 1.1 }}>
                  {p.title}
                </Typography>
                <Typography variant="body2" sx={{ color: paper.inkSoft, maxWidth: '30ch', lineHeight: 1.55 }}>{p.desc}</Typography>
              </Box>
            </Reveal>
          ))}
        </Box>
      </PageContainer>

      {/* lower sections — live tools, pipeline, roadmap, footer */}
      <PageContainer width="wide" sx={{ pt: { xs: 6, md: 8 }, pb: { xs: 6, md: 9 } }}>
        {/* live tools */}
        <Box sx={{ pt: { xs: 2, md: 3 } }}>
          <Typography variant="overline" sx={{ color: paper.sepia, display: 'block', mb: 2 }}>
            {de.landing.toolsHeading}
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
                    bgcolor: paper.hi,
                    transition: 'transform .2s ease, box-shadow .3s ease, border-color .2s ease',
                    '&:hover': { transform: 'translateY(-3px)', boxShadow: '0 12px 30px rgba(36,26,16,.16)', borderColor: paper.viridian },
                  }}
                >
                  <Typography variant="h4" sx={{ fontFamily: display, fontWeight: 600, mb: 0.75 }}>{t.title}</Typography>
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
            {de.landing.roadmapHeading}
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
                    <Typography variant="h6" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, minWidth: { sm: 210 } }}>
                      {r.title}
                    </Typography>
                    <Box component="span" sx={{ display: { xs: 'inline', sm: 'none' }, fontStyle: 'italic', fontSize: '.85rem', color: paper.sepia, whiteSpace: 'nowrap' }}>
                      {de.common.soon}
                    </Box>
                  </Box>
                  <Typography variant="body2" sx={{ color: paper.inkSoft, flex: 1 }}>
                    {r.desc}
                  </Typography>
                  <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' }, fontStyle: 'italic', fontSize: '.85rem', color: paper.sepia, whiteSpace: 'nowrap' }}>
                    {de.common.soon}
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
            <Typography sx={{ fontFamily: garamond, fontStyle: 'italic', color: paper.inkSoft }}>
              {de.landing.footer.scripts}
            </Typography>
            <Typography variant="body2" sx={{ color: paper.sepia, fontStyle: 'italic' }}>
              {de.landing.footer.disclaimer}
            </Typography>
          </Box>
          <Link
            component={RouterLink}
            to={paths.impressum}
            variant="body2"
            sx={{ color: paper.sepia, textDecoration: 'none', '&:hover': { color: paper.viridian } }}
          >
            {de.impressum.footerLink}
          </Link>
        </Box>
      </PageContainer>
    </PublicLayout>
  );
}
