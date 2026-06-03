// Public landing page. Editorial paper aesthetic with anyplot's imprint
// palette — warm off-white, warm grayscale type, brand green used sparingly
// (eyebrow dot, timeline nodes, admin-link hover). The hero headline is set in
// EB Garamond italic (SIL OFL 1.1, self-hosted via @fontsource — imported in
// main.tsx, attributed in THIRD_PARTY_NOTICES.md). Body and functional labels
// stay in the sans stack so they don't compete with the hero.

import { Box, Container, Link, Stack, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

import { tokens } from '../theme';

const garamond = "'EB Garamond', Georgia, 'Times New Roman', serif";

// The ductus pipeline, condensed to four steps for the landing timeline.
const steps = [
  { step: 'Scannen', detail: 'Geometrie & Strichbreite aus der Vorlage' },
  { step: 'Fitten', detail: 'Ductus-Prior legt Reihenfolge & Kreuzungen fest' },
  { step: 'Mitteln', detail: 'viele Proben → deine persönliche Buchstabenform' },
  { step: 'Verbinden', detail: 'berechnete Übergänge statt Paar-Katalog' },
];

export function LandingPage() {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
        // single hairline at the top — subtle editorial framing
        '&::before': {
          content: '""',
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          height: '1px',
          bgcolor: 'divider',
        },
      }}
    >
      <Container maxWidth="sm" sx={{ py: 8 }}>
        <Stack spacing={3.5}>
          {/* Eyebrow: brand-green dot + lowercase domain */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
            <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: tokens.green }} />
            <Typography variant="overline" sx={{ color: 'text.secondary', lineHeight: 1 }}>
              kurrentschrift.ink
            </Typography>
          </Box>

          {/* Hero — EB Garamond italic, near-black ink */}
          <Typography
            component="h1"
            sx={{
              fontFamily: garamond,
              fontStyle: 'italic',
              fontWeight: 400,
              fontSize: { xs: '2.25rem', sm: '2.75rem' },
              lineHeight: 1.14,
              color: 'text.primary',
            }}
          >
            Wie aus Tinte Schrift wird.
          </Typography>

          {/* Body — secondary ink, sans, comfortable line-height */}
          <Typography variant="body1" sx={{ color: 'text.secondary', lineHeight: 1.7 }}>
            Eine offene Bibliothek der deutschen Kurrentschrift — kein Font, sondern
            der Schreibvorgang selbst. Geometrie aus historischen Vorlagen,
            Strichreihenfolge aus einem handkuratierten Ductus. Lesen, animieren,
            neu schreiben.
          </Typography>

          {/* Primary CTAs — the tools a visitor can already use today */}
          <Stack direction="row" spacing={3} sx={{ flexWrap: 'wrap', rowGap: 1 }}>
            <Link
              component={RouterLink}
              to="/quiz"
              sx={{
                color: tokens.green,
                fontWeight: 500,
                textDecoration: 'none',
                '&:hover': { color: tokens.greenDark },
              }}
            >
              Buchstaben-Quiz starten →
            </Link>
            <Link
              component={RouterLink}
              to="/schreiben"
              sx={{
                color: tokens.green,
                fontWeight: 500,
                textDecoration: 'none',
                '&:hover': { color: tokens.greenDark },
              }}
            >
              Übungsblatt erstellen →
            </Link>
          </Stack>

          {/* How it works — the ductus pipeline as a quiet timeline */}
          <Box sx={{ pt: 1 }}>
            <Typography
              variant="overline"
              sx={{ color: 'text.secondary', display: 'block', mb: 2 }}
            >
              In vier Schritten
            </Typography>
            <Box sx={{ position: 'relative', pl: 3 }}>
              {/* connecting hairline */}
              <Box
                sx={{
                  position: 'absolute',
                  left: 5,
                  top: 6,
                  bottom: 6,
                  width: '1px',
                  bgcolor: 'divider',
                }}
              />
              <Stack spacing={2.25}>
                {steps.map(({ step, detail }) => (
                  <Box key={step} sx={{ position: 'relative' }}>
                    {/* node dot, masked over the hairline */}
                    <Box
                      sx={{
                        position: 'absolute',
                        left: -23,
                        top: 5,
                        width: 9,
                        height: 9,
                        borderRadius: '50%',
                        bgcolor: tokens.green,
                        boxShadow: (t) => `0 0 0 4px ${t.palette.background.default}`,
                      }}
                    />
                    <Typography sx={{ color: 'text.primary', fontWeight: 500, lineHeight: 1.3 }}>
                      {step}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary', lineHeight: 1.6 }}>
                      {detail}
                    </Typography>
                  </Box>
                ))}
              </Stack>
            </Box>
          </Box>

          {/* Footer row: muted links left + right, divider above */}
          <Box
            sx={{
              pt: 4,
              mt: 2,
              borderTop: '1px solid',
              borderColor: 'divider',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'baseline',
            }}
          >
            <Link
              href="https://github.com/MarkusNeusinger/kurrentschrift"
              target="_blank"
              rel="noopener"
              variant="body2"
              sx={{
                color: 'text.secondary',
                textDecoration: 'none',
                '&:hover': { color: tokens.green },
              }}
            >
              GitHub
            </Link>
            <Link
              component={RouterLink}
              to="/admin/chart"
              variant="caption"
              sx={{
                color: 'text.disabled',
                textDecoration: 'none',
                letterSpacing: '0.06em',
                textTransform: 'lowercase',
                '&:hover': { color: tokens.green },
              }}
            >
              admin
            </Link>
          </Box>
        </Stack>
      </Container>
    </Box>
  );
}
