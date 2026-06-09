// 404 surface for unknown URLs. Replaces the old silent redirect to "/" so a
// mistyped or stale link is visible as such instead of quietly landing on the
// landing page.
import { Box, Button, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

import { PaperBackground } from '@/components/PaperBackground';
import { PublicHeader } from '@/components/PublicHeader';
import { paths } from '@/routes/paths';

export function NotFoundPage() {
  return (
    <PaperBackground minHeight="100dvh">
      <PublicHeader />
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 2,
          px: 3,
          py: { xs: 10, md: 16 },
          textAlign: 'center',
        }}
      >
        <Typography variant="h4" component="h1">
          Seite nicht gefunden
        </Typography>
        <Typography color="text.secondary" sx={{ maxWidth: 480 }}>
          Unter dieser Adresse liegt nichts — der Link ist veraltet oder vertippt.
        </Typography>
        <Button component={RouterLink} to={paths.home} variant="outlined" sx={{ mt: 1 }}>
          Zur Startseite
        </Button>
      </Box>
    </PaperBackground>
  );
}

export default NotFoundPage;
