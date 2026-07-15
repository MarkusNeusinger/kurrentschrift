// 404 surface for unknown URLs. Replaces the old silent redirect to "/" so a
// mistyped or stale link is visible as such instead of quietly landing on the
// landing page.
import { Box, Button, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

import { usePageMeta } from '@/hooks/usePageMeta';
import { PublicLayout } from '@/layouts/public/PublicLayout';
import { de } from '@/locales';
import { paths } from '@/routes/paths';

export function NotFoundPage() {
  usePageMeta(de.seo.notFound);
  return (
    <PublicLayout footer={false}>
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
          {de.common.notFound.title}
        </Typography>
        <Typography color="text.secondary" sx={{ maxWidth: 480 }}>
          {de.common.notFound.body}
        </Typography>
        <Button component={RouterLink} to={paths.home} variant="outlined" sx={{ mt: 1 }}>
          {de.common.notFound.toHome}
        </Button>
      </Box>
    </PublicLayout>
  );
}

export default NotFoundPage;
