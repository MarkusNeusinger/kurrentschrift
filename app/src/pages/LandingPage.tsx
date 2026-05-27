// Public landing page. Editorial paper aesthetic with anyplot's imprint
// palette — warm off-white, warm grayscale type, brand green used sparingly
// (a single accent dot + the admin-link hover state). No MonoLisa here; the
// page is a quiet placeholder, not the catalogue itself.

import { Box, Container, Link, Stack, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

import { tokens } from '../theme';

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
        <Stack spacing={3}>
          {/* Eyebrow: brand-green dot + lowercase domain, tracked */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
            <Box
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                bgcolor: tokens.green,
              }}
            />
            <Typography variant="overline" sx={{ color: 'text.secondary', lineHeight: 1 }}>
              kurrentschrift.ink
            </Typography>
          </Box>

          {/* Headline — large, light weight, near-black ink */}
          <Typography
            variant="h3"
            component="h1"
            sx={{
              fontWeight: 300,
              lineHeight: 1.2,
              color: 'text.primary',
              letterSpacing: '-0.02em',
            }}
          >
            Eine offene Bibliothek der Kurrent-Ductus-Templates.
          </Typography>

          {/* Body — secondary ink, comfortable line-height */}
          <Typography
            variant="body1"
            sx={{
              color: 'text.secondary',
              lineHeight: 1.7,
              fontWeight: 400,
            }}
          >
            Hier entsteht ein Werkzeug zum Lesen und Re-Inken historischer deutscher
            Kurrentschrift. Analysis-by-synthesis: Geometrie aus der Vorlage,
            Strich-Reihenfolge aus einem manuell kuratierten Ductus-Prior. MVP-Phase —
            bald mehr.
          </Typography>

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
