// Minimal legal footer for the public tool pages (/schreiben, /quiz): a
// hairline + one centered Impressum link, so the legal page is reachable from
// every public page. The landing keeps its own richer footer and links the
// Impressum itself; the Impressum page needs no footer. Render INSIDE
// <PaperBackground>, after the page's content Container.

import { Box, Link } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

import { PageContainer } from '@/components/PageContainer';
import { de } from '@/locales';
import { paths } from '@/routes/paths';
import { paper } from '@/styles/paper';

export function PublicFooter() {
  return (
    <PageContainer width="wide">
      <Box sx={{ borderTop: `1px solid ${paper.line}`, py: 2.5, textAlign: 'center' }}>
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
  );
}
