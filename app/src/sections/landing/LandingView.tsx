// LandingView — kurrentschrift.ink public landing.
//
// "Paper & ink" identity (deliberately NOT the anyplot/pyplots palette): aged cream
// paper, aged iron-gall brown as the writing ink, viridian as the single sparing
// accent. A single-column hero (<HeroWritten>) writes the brand word with a pen,
// then the thesis pillars, the live tools and the honest "bald" roadmap follow.
//
// Headlines/brand use Playfair Display (`display`); body/eyebrow use EB Garamond
// (`garamond`); the showpiece word uses GL-GermanCursive (`script`). All honour
// prefers-reduced-motion. The paper atmosphere (gradient + grain + vignette) is
// shared via <PaperBackground> so the same look carries across every page; only
// the work surfaces (A4 preview, letter crops, chart scan) stay neutral.

import { Link as RouterLink } from 'react-router-dom';
import { Box, Link, Stack, Typography } from '@mui/material';

import { CategoryHeading } from '@/components/CategoryHeading';
import { PageContainer } from '@/components/PageContainer';
import { PublicLayout } from '@/layouts/public/PublicLayout';
import { de } from '@/locales';
import { paths } from '@/routes/paths';
import { HeroWritten } from '@/sections/landing/HeroWritten';
import { Reveal } from '@/sections/landing/Reveal';
import { display, garamond, letterpress, paper } from '@/styles/paper';

// Everything usable today → real RouterLinks, ordered reading → writing
// (Schriftkunde · Quiz · Tafel · Übungsblatt · Federprobe). German copy lives in
// @/locales (landing.tools); here we only attach the route targets.
const tools = [
  { ...de.landing.tools.schriftkunde, to: paths.schriftkunde },
  { ...de.landing.tools.quiz, to: paths.quiz },
  { ...de.landing.tools.tafel, to: paths.tafel },
  { ...de.landing.tools.worksheet, to: paths.worksheet },
  { ...de.landing.tools.scribe, to: paths.scribe },
];

const roadmap = de.landing.roadmap;

// The three starter scripts from the Kurrent family. `written` marks which the
// engine can already render (Sütterlin); `state` is the small badge text.
const scripts = de.landing.scripts;

export function LandingView() {
  return (
    <PublicLayout>
      {/* hero — single column, the brand word written live by a pen */}
      <HeroWritten />

      {/* the three scripts — starters from the Kurrent family, each its own pen */}
      <PageContainer width="wide" sx={{ pt: { xs: 4, md: 6 } }}>
        <CategoryHeading>{de.landing.scriptsHeading}</CategoryHeading>
        <Typography variant="body1" sx={{ color: paper.inkSoft, maxWidth: '64ch', mb: { xs: 3, md: 4 } }}>
          {de.landing.scriptsIntro}
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2.5 }}>
          {scripts.map((s, i) => (
            <Reveal key={s.name} delay={i * 0.06}>
              <Box
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  p: 2.5,
                  borderRadius: 2,
                  border: `1px solid ${paper.line}`,
                  bgcolor: paper.hi,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 1, mb: 0.75 }}>
                  <Typography variant="h5" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, textShadow: letterpress, lineHeight: 1.1 }}>
                    {s.name}
                  </Typography>
                  <Box component="span" sx={{ fontFamily: display, fontStyle: 'italic', color: paper.viridian, fontSize: '1rem', whiteSpace: 'nowrap' }}>
                    {s.feder}
                  </Box>
                </Box>
                <Typography variant="body2" sx={{ color: paper.inkSoft, lineHeight: 1.55, mb: 2, flexGrow: 1 }}>
                  {s.desc}
                </Typography>
                <Box
                  component="span"
                  sx={{
                    alignSelf: 'flex-start',
                    fontSize: '.8rem',
                    fontStyle: 'italic',
                    px: '0.7rem',
                    py: '0.18rem',
                    borderRadius: '999px',
                    border: `1px solid ${s.written ? paper.viridian : paper.line}`,
                    color: s.written ? paper.viridian : paper.sepia,
                  }}
                >
                  {s.state}
                </Box>
              </Box>
            </Reveal>
          ))}
        </Box>
      </PageContainer>

      {/* lower sections — live tools, pipeline, roadmap, footer */}
      <PageContainer width="wide" sx={{ pt: { xs: 6, md: 8 }, pb: { xs: 6, md: 9 } }}>
        {/* what already works — everything usable today, lighter cards */}
        <Box sx={{ pt: { xs: 1, md: 2 } }}>
          <CategoryHeading>{de.landing.toolsHeading}</CategoryHeading>
          <Typography variant="body1" sx={{ color: paper.inkSoft, maxWidth: '64ch', mb: { xs: 3, md: 4 } }}>
            {de.landing.toolsIntro}
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' }, gap: 2 }}>
            {tools.map((t, i) => (
              <Reveal key={t.to} delay={i * 0.06}>
                <Box
                  component={RouterLink}
                  to={t.to}
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    height: '100%',
                    textDecoration: 'none',
                    color: paper.ink,
                    p: 2.5,
                    borderRadius: 2,
                    border: `1px solid ${paper.line}`,
                    bgcolor: paper.hi,
                    transition: 'transform .2s ease, box-shadow .3s ease, border-color .2s ease',
                    '&:hover': { transform: 'translateY(-2px)', boxShadow: '0 10px 24px rgba(36,26,16,.14)', borderColor: paper.viridian },
                  }}
                >
                  <Typography variant="h5" sx={{ fontFamily: display, fontWeight: 600, mb: 0.5 }}>{t.title}</Typography>
                  <Typography variant="body2" sx={{ color: paper.inkSoft, lineHeight: 1.55, mb: 1.25, flexGrow: 1 }}>{t.desc}</Typography>
                  <Typography variant="body2" sx={{ color: paper.viridian, fontWeight: 500 }}>{t.cta}</Typography>
                </Box>
              </Reveal>
            ))}
          </Box>
        </Box>

        {/* roadmap — an honest word on the state, then genuinely-future items */}
        <Box sx={{ mt: { xs: 6, md: 9 } }}>
          <CategoryHeading>{de.landing.roadmapHeading}</CategoryHeading>
          <Typography variant="body2" sx={{ color: paper.inkSoft, maxWidth: '64ch', mb: 2.5 }}>
            {de.landing.roadmapNote}
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
