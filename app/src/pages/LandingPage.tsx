// Public landing page. Until the public reader/animation/HTR features land
// (post-MVP §11+), this is a low-key placeholder pointing visitors at the
// project goal. The admin tooling lives under /admin/* and is gated by
// Cloudflare Access.

import { Box, Container, Link, Stack, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

export function LandingPage() {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
      }}
    >
      <Container maxWidth="sm" sx={{ py: 8 }}>
        <Stack spacing={3}>
          <Typography variant="overline" color="text.secondary">
            kurrentschrift.ink
          </Typography>
          <Typography variant="h3" component="h1" sx={{ fontWeight: 300, lineHeight: 1.2 }}>
            Eine offene Bibliothek der Kurrent-Ductus-Templates.
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Hier entsteht ein Werkzeug zum Lesen und Re-Inken historischer deutscher Kurrentschrift.
            Analysis-by-synthesis: Geometrie aus der Vorlage, Strich-Reihenfolge aus einem manuell
            kuratierten Ductus-Prior. MVP-Phase — bald mehr.
          </Typography>
          <Box sx={{ pt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <Link
              href="https://github.com/MarkusNeusinger/kurrentschrift"
              target="_blank"
              rel="noopener"
              underline="hover"
              variant="body2"
              color="text.secondary"
            >
              GitHub
            </Link>
            <Link
              component={RouterLink}
              to="/admin/chart"
              underline="hover"
              variant="caption"
              color="text.disabled"
            >
              Admin
            </Link>
          </Box>
        </Stack>
      </Container>
    </Box>
  );
}
