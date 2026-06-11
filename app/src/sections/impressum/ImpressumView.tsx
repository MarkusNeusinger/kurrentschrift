// ImpressumView — legal page (/impressum): Impressum, Datenschutz, Quellen &
// Lizenzen, Transparenz. Same "paper & ink" identity as every public page
// (PaperBackground + PublicHeader, tokens from styles/paper). All German prose
// lives in app/src/locales/de/impressum.ts; this component is layout only.
//
// Layout follows the anyplot legal page loosely (portrait next to the operator
// block, hairline rows for the hosting table) but stays deliberately compact —
// the audience here is far less technical.

import type { ReactNode } from 'react';
import { Box, Container, Link, Typography } from '@mui/material';

import portraitUrl from '@/assets/markus-neusinger.webp';
import { PaperBackground } from '@/components/PaperBackground';
import { PublicHeader } from '@/components/PublicHeader';
import { de } from '@/locales';
import { display, garamond, letterpress, paper } from '@/styles/paper';

const t = de.impressum;

// --- shared text styles -----------------------------------------------------
const prose = {
  fontFamily: garamond,
  color: paper.inkSoft,
  fontSize: '1.02rem',
  lineHeight: 1.7,
  mb: 1.5,
} as const;

const subTitle = {
  fontFamily: display,
  fontWeight: 600,
  fontSize: '1.05rem',
  color: paper.ink,
  mt: 2.5,
  mb: 0.5,
} as const;

// In-prose links: sepia with a hairline underline, viridian on hover.
const proseLink = {
  color: paper.sepia,
  textDecorationColor: `${paper.sepia}80`,
  transition: 'color .2s',
  '&:hover': { color: paper.viridian, textDecorationColor: paper.viridian },
} as const;

function Section({ heading, children }: { heading: string; children: ReactNode }) {
  return (
    <Box component="section" sx={{ mt: { xs: 5, md: 6 } }}>
      <Typography variant="overline" sx={{ color: paper.sepia, display: 'block', mb: 1 }}>
        {heading}
      </Typography>
      {children}
    </Box>
  );
}

export function ImpressumView() {
  return (
    <PaperBackground>
      <PublicHeader tone="paper" />

      <Container maxWidth="md" sx={{ position: 'relative', zIndex: 1, px: { xs: 2.5, sm: 4, md: 6 }, pt: { xs: 4, md: 6 }, pb: { xs: 6, md: 9 } }}>
        <Typography
          component="h1"
          sx={{ fontFamily: display, fontWeight: 600, fontSize: { xs: '2rem', md: '2.6rem' }, color: paper.ink, textShadow: letterpress }}
        >
          {t.title}
        </Typography>

        {/* Impressum — portrait beside the operator/contact block */}
        <Section heading={t.imprint.heading}>
          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              alignItems: { xs: 'flex-start', sm: 'center' },
              gap: { xs: 3, sm: 5 },
              mb: 2,
            }}
          >
            <Box
              component="img"
              src={portraitUrl}
              alt={t.imprint.operatorName}
              width={240}
              height={518}
              loading="lazy"
              sx={{ width: { xs: 104, sm: 124 }, height: 'auto', flexShrink: 0, display: 'block' }}
            />
            <Box>
              <Typography sx={subTitle}>{t.imprint.operatorLabel}</Typography>
              <Typography sx={{ ...prose, mb: 0 }}>
                {t.imprint.operatorName}
                <br />
                {t.imprint.operatorPlace}
              </Typography>

              <Typography sx={subTitle}>{t.imprint.contactLabel}</Typography>
              <Typography sx={{ ...prose, mb: 0 }}>
                <Link href={`mailto:${t.imprint.email}`} sx={proseLink}>
                  {t.imprint.email}
                </Link>
                <br />
                {t.imprint.linkedinLabel}:{' '}
                <Link href={t.imprint.linkedinUrl} target="_blank" rel="noopener noreferrer" sx={proseLink}>
                  {t.imprint.linkedinHandle}
                </Link>
              </Typography>
            </Box>
          </Box>
          <Typography sx={{ ...prose, fontStyle: 'italic', mb: 0 }}>{t.imprint.disclaimer}</Typography>
        </Section>

        {/* Datenschutz */}
        <Section heading={t.privacy.heading}>
          <Typography sx={prose}>{t.privacy.intro}</Typography>

          <Typography sx={subTitle}>{t.privacy.analyticsTitle}</Typography>
          <Typography sx={prose}>
            {t.privacy.analyticsBeforeLink}
            <Link href={t.privacy.analyticsUrl} target="_blank" rel="noopener noreferrer" sx={proseLink}>
              {t.privacy.analyticsLinkText}
            </Link>
            {t.privacy.analyticsAfterLink}
          </Typography>

          <Typography sx={subTitle}>{t.privacy.logsTitle}</Typography>
          <Typography sx={prose}>{t.privacy.logs}</Typography>

          <Typography sx={subTitle}>{t.privacy.hostingTitle}</Typography>
          <Typography sx={{ ...prose, mb: 1 }}>{t.privacy.hostingIntro}</Typography>
          <Box sx={{ mb: 1.5 }}>
            {t.privacy.hosting.map((row) => (
              <Box
                key={row.label}
                sx={{
                  display: 'flex',
                  flexDirection: { xs: 'column', sm: 'row' },
                  gap: { xs: 0, sm: 2 },
                  py: 0.9,
                  borderBottom: `1px solid ${paper.line}`,
                }}
              >
                <Typography sx={{ ...prose, mb: 0, color: paper.sepia, minWidth: { sm: 170 } }}>{row.label}</Typography>
                <Typography sx={{ ...prose, mb: 0 }}>{row.value}</Typography>
              </Box>
            ))}
          </Box>

          <Typography sx={subTitle}>{t.privacy.notCollectedTitle}</Typography>
          <Box component="ul" sx={{ m: 0, mb: 1.5, pl: 3 }}>
            {t.privacy.notCollected.map((item) => (
              <Typography key={item} component="li" sx={{ ...prose, mb: 0.25 }}>
                {item}
              </Typography>
            ))}
          </Box>

          <Typography sx={subTitle}>{t.privacy.rightsTitle}</Typography>
          <Typography sx={{ ...prose, mb: 0 }}>{t.privacy.rights}</Typography>
        </Section>

        {/* Quellen & Lizenzen */}
        <Section heading={t.sources.heading}>
          <Typography sx={prose}>{t.sources.geometry}</Typography>
          <Typography sx={prose}>{t.sources.fonts}</Typography>
          <Typography sx={{ ...prose, mb: 0 }}>{t.sources.code}</Typography>
        </Section>

        {/* Transparenz */}
        <Section heading={t.transparency.heading}>
          <Typography sx={{ ...prose, mb: 0 }}>{t.transparency.text}</Typography>
        </Section>

        <Typography sx={{ ...prose, mb: 0, mt: { xs: 5, md: 6 }, textAlign: 'center', fontSize: '.9rem', color: paper.sepiaFaint, fontStyle: 'italic' }}>
          {t.lastUpdated}
        </Typography>
      </Container>
    </PaperBackground>
  );
}
