// LandingView — kurrentschrift.ink public landing.
//
// "Paper & ink" identity (deliberately NOT the anyplot/pyplots palette): aged cream
// paper, aged iron-gall brown as the writing ink, viridian as the single sparing
// accent. A single-column hero (<HeroWritten>) writes the brand word with a pen,
// then the three scripts ("Drei Schriften, drei Federn"), the live tools
// ("Schon zur Hand") and the honest "Noch im Werden" roadmap follow.
//
// Headlines/brand use Playfair Display (`display`); body/eyebrow use EB Garamond
// (`garamond`); the showpiece word uses GL-GermanCursive (`script`). All honour
// prefers-reduced-motion. The paper atmosphere (gradient + grain + vignette) is
// shared via <PaperBackground> so the same look carries across every page; only
// the work surfaces (A4 preview, letter crops, chart scan) stay neutral.

import { Box, Stack, Typography } from '@mui/material';

import { CategoryHeading } from '@/components/CategoryHeading';
import { PageContainer } from '@/components/PageContainer';
import { PaperCardLink } from '@/components/PaperCardLink';
import { PublicLayout } from '@/layouts/public/PublicLayout';
import { de } from '@/locales';
import { paths } from '@/routes/paths';
import { HeroWritten } from '@/sections/landing/HeroWritten';
import { Reveal } from '@/sections/landing/Reveal';
import { display, letterpress, paper } from '@/styles/paper';

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

// The "So geht es" three-step, in the order the top nav names the areas.
// `howRoutes` is keyed by the locale's own step ids, so a step added without
// its route fails to compile instead of rendering a dead card (the same guard
// the hub cards use). Each step points at the ENTRY of its area.
// Each step goes to its AREA, not to one of its tools: the sentences name two
// tools apiece, and the hub is the page that holds both (design-system.md §6 —
// /lesen and /schreiben are the hub entries; Schriftkunde is its own area page
// with no hub above it). Linking straight to the quiz or the worksheet would
// promise the area and deliver one tool, hiding the other (Copilot review).
const howRoutes: Record<keyof typeof de.landing.howSteps, string> = {
  nachschlagen: paths.schriftkunde,
  lesen: paths.lesen,
  schreiben: paths.schreiben,
};
const howSteps = (Object.keys(de.landing.howSteps) as (keyof typeof de.landing.howSteps)[]).map((id) => ({
  ...de.landing.howSteps[id],
  to: howRoutes[id],
}));

// The three starter scripts from the Kurrent family. `written` marks which the
// engine can already render (Sütterlin); `state` is the small badge text.
const scripts = de.landing.scripts;

export function LandingView() {
  return (
    <PublicLayout>
      {/* hero — single column, the brand word written live by a pen */}
      <HeroWritten />

      {/* "So geht es" — the path through the three areas, right after the hero:
          the page answered „was" but not „wie fange ich an" (owner decision
          2026-09-03). Same PaperCardLink as every other card here, so the
          focus ring, the link colour and the touch target come from the theme
          (#485) rather than from a new component. */}
      <PageContainer width="wide" sx={{ pt: { xs: 4, md: 6 } }}>
        <CategoryHeading>{de.landing.howHeading}</CategoryHeading>
        {/* An ORDERED list, not three cards in a grid: the order is the whole
            point of the section, and it must reach a screen reader too — the
            printed ordinal alone would not (Copilot review, #503). `role="list"`
            is kept because `list-style: none` drops list semantics in Safari;
            Reveal is the <li> itself, so the grid still stretches the items to
            equal height. */}
        <Box
          component="ol"
          role="list"
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' },
            gap: 2.5,
            listStyle: 'none',
            p: 0,
            m: 0,
          }}
        >
          {howSteps.map((step, i) => (
            <Reveal key={step.to} delay={i * 0.06} component="li">
              <PaperCardLink to={step.to}>
                {/* The ordinal in ink, for the eye. The list itself carries the
                    sequence for assistive tech, so a bare „1" read out before
                    the heading would only be noise — hence aria-hidden. */}
                <Typography
                  component="span"
                  variant="caption"
                  aria-hidden
                  sx={{ fontFamily: display, fontStyle: 'italic', color: paper.viridianText, display: 'block', mb: 0.25 }}
                >
                  {i + 1}
                </Typography>
                {/* h3: the cards sit directly under the CategoryHeading <h2> */}
                <Typography
                  variant="h5"
                  component="h3"
                  sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, textShadow: letterpress, mb: 0.5 }}
                >
                  {step.title}
                </Typography>
                <Typography variant="body2" sx={{ color: paper.inkSoft, lineHeight: 1.55, mb: 1.25, flexGrow: 1 }}>
                  {step.desc}
                </Typography>
                <Typography variant="body2" sx={{ color: paper.viridianText, fontWeight: 500 }}>
                  {step.cta}
                </Typography>
              </PaperCardLink>
            </Reveal>
          ))}
        </Box>
      </PageContainer>

      {/* the three scripts — starters from the Kurrent family, each its own pen */}
      <PageContainer width="wide" sx={{ pt: { xs: 4, md: 6 } }}>
        <CategoryHeading>{de.landing.scriptsHeading}</CategoryHeading>
        <Typography variant="body1" sx={{ color: paper.inkSoft, maxWidth: '64ch', mb: { xs: 3, md: 4 } }}>
          {de.landing.scriptsIntro}
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2.5 }}>
          {scripts.map((s, i) => (
            <Reveal key={s.name} delay={i * 0.06}>
              <PaperCardLink to={`${paths.tafel}#${s.styleId}`}>
                <Box sx={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 1, mb: 0.75 }}>
                  {/* h3: the cards sit directly under the CategoryHeading <h2> */}
                  <Typography variant="h5" component="h3" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, textShadow: letterpress, lineHeight: 1.1 }}>
                    {s.name}
                  </Typography>
                  <Box component="span" sx={{ fontFamily: display, fontStyle: 'italic', color: paper.viridianText, fontSize: '1rem', whiteSpace: 'nowrap' }}>
                    {s.feder}
                  </Box>
                </Box>
                <Typography variant="body2" sx={{ color: paper.inkSoft, lineHeight: 1.55, flexGrow: 1 }}>
                  {s.desc}
                </Typography>
                {/* the honest state rides the link text AND an explicit status
                    tag: viridian + „in aktiver Optimierung" for the script the
                    engine already writes (Sütterlin), muted „noch nicht
                    begonnen" for the two that are only a scan today. A hairline
                    sets the row off from the description; on narrow cards the
                    tag wraps under the CTA. */}
                <Box
                  sx={{
                    mt: 2,
                    pt: 1.5,
                    borderTop: `1px solid ${paper.line}`,
                    display: 'flex',
                    flexWrap: 'wrap',
                    alignItems: 'baseline',
                    justifyContent: 'space-between',
                    columnGap: 1.5,
                    rowGap: 0.25,
                  }}
                >
                  <Typography
                    variant="body2"
                    sx={{ fontWeight: 500, color: s.written ? paper.viridianText : paper.sepia }}
                  >
                    {s.cta}
                  </Typography>
                  {/* `caption` (14px) rather than an ad-hoc .85rem: the status
                      marks used to render at 13.6px, under the §9 floor. */}
                  <Typography
                    component="span"
                    variant="caption"
                    sx={{ fontStyle: 'italic', color: s.written ? paper.viridianText : paper.sepia, whiteSpace: 'nowrap' }}
                  >
                    {s.status}
                  </Typography>
                </Box>
              </PaperCardLink>
            </Reveal>
          ))}
        </Box>
      </PageContainer>

      {/* lower sections — live tools ("Schon zur Hand") + roadmap ("Noch im Werden");
          the footer is rendered globally by PublicLayout, not here */}
      <PageContainer width="wide" sx={{ pt: { xs: 6, md: 8 } }}>
        {/* what already works — everything usable today, lighter cards */}
        <Box sx={{ pt: { xs: 1, md: 2 } }}>
          <CategoryHeading>{de.landing.toolsHeading}</CategoryHeading>
          <Typography variant="body1" sx={{ color: paper.inkSoft, maxWidth: '64ch', mb: { xs: 3, md: 4 } }}>
            {de.landing.toolsIntro}
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' }, gap: 2 }}>
            {tools.map((t, i) => (
              <Reveal key={t.to} delay={i * 0.06}>
                <PaperCardLink to={t.to}>
                  {/* h3: the cards sit directly under the CategoryHeading <h2> */}
                  <Typography variant="h5" component="h3" sx={{ fontFamily: display, fontWeight: 600, mb: 0.5 }}>{t.title}</Typography>
                  <Typography variant="body2" sx={{ color: paper.inkSoft, lineHeight: 1.55, mb: 1.25, flexGrow: 1 }}>{t.desc}</Typography>
                  <Typography variant="body2" sx={{ color: paper.viridianText, fontWeight: 500 }}>{t.cta}</Typography>
                </PaperCardLink>
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
                    <Typography variant="h6" component="h3" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, minWidth: { sm: 210 } }}>
                      {r.title}
                    </Typography>
                    <Typography component="span" variant="caption" sx={{ display: { xs: 'inline', sm: 'none' }, fontStyle: 'italic', color: paper.sepia, whiteSpace: 'nowrap' }}>
                      {de.common.soon}
                    </Typography>
                  </Box>
                  <Typography variant="body2" sx={{ color: paper.inkSoft, flex: 1 }}>
                    {r.desc}
                  </Typography>
                  <Typography component="span" variant="caption" sx={{ display: { xs: 'none', sm: 'inline' }, fontStyle: 'italic', color: paper.sepia, whiteSpace: 'nowrap' }}>
                    {de.common.soon}
                  </Typography>
                </Box>
              </Reveal>
            ))}
          </Stack>
        </Box>
      </PageContainer>
      {/* the legal footer is the shared <PublicFooter>, rendered by PublicLayout */}
    </PublicLayout>
  );
}
