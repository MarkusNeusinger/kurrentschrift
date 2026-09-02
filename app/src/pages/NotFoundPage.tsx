// 404 surface for unknown URLs. Replaces the old silent redirect to "/" so a
// mistyped or stale link is visible as such instead of quietly landing on the
// landing page.
//
// It carries the FOOTER like every other page: a 404 is a dead end, and the
// dead end is exactly where a visitor needs the Impressum link (DDG §5) and the
// three areas — the page used to hide it (`footer={false}`).
//
// It also reports itself. A broken link somewhere on the web is otherwise
// invisible to us; `page_not_found` with the path is the only way to notice
// one (the sibling repo has counted it this way since its own 404 landed —
// owner rule "Gute Sachen aufs Schwesterprojekt", 2026-09-01).
import { useEffect } from 'react';

import { Box, Button, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

import { usePageMeta } from '@/hooks/usePageMeta';
import { PublicLayout } from '@/layouts/public/PublicLayout';
import { trackEvent } from '@/lib/analytics';
import { de } from '@/locales';
import { paths } from '@/routes/paths';
import { hitArea } from '@/styles/hitArea';

/** Where the miss came from — a URL that matches no route is a different
 *  problem from a route that rendered and then threw. */
export type NotFoundSource = 'catch_all' | 'route_error';

export function NotFoundPage({ source = 'catch_all' }: { source?: NotFoundSource } = {}) {
  usePageMeta(de.seo.notFound);

  useEffect(() => {
    // `window.location`, not `useLocation`: this component is also the fallback
    // inside the router error boundary, where the router context is the very
    // thing that may have failed.
    trackEvent('page_not_found', { path: window.location.pathname, source });
  }, [source]);

  return (
    <PublicLayout>
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
        <Button component={RouterLink} to={paths.home} variant="outlined" sx={[hitArea(), { mt: 1 }]}>
          {de.common.notFound.toHome}
        </Button>
      </Box>
    </PublicLayout>
  );
}

export default NotFoundPage;
