// Shared footer for every public page: a hairline, a warm one-line sign-off
// (the "private Liebhaberei" voice from the impressum) on the left, the
// Impressum/Datenschutz link on the right. Rendered by <PublicLayout> after the
// page content (inside <PaperBackground>), so it's identical everywhere.
//
// The footer OWNS the bottom gap (its `mt`) — the single source of the distance
// from page content to the footer. Pages therefore set only top padding (`pt`)
// on their outer PageContainer and never add their own `pb`, so the gap is the
// same everywhere (design-system §4).

import { Box, Link, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

import { PageContainer } from '@/components/PageContainer';
import { de } from '@/locales';
import { paths } from '@/routes/paths';
import { garamond, paper } from '@/styles/paper';

export function PublicFooter() {
  return (
    <PageContainer width="wide">
      <Box
        component="footer"
        sx={{
          borderTop: `1px solid ${paper.line}`,
          mt: { xs: 8, md: 11 },
          py: 3,
          display: 'flex',
          flexDirection: 'row',
          flexWrap: 'nowrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 2,
        }}
      >
        <Typography sx={{ fontFamily: garamond, fontStyle: 'italic', color: paper.inkSoft }}>
          {de.common.footer.tagline}
          <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>
            {de.common.footer.taglineRest}
          </Box>
        </Typography>
        <Link
          component={RouterLink}
          to={paths.impressum}
          variant="body2"
          sx={{
            flexShrink: 0,
            color: paper.sepia,
            textDecoration: 'none',
            '&:hover': { color: paper.viridian },
          }}
        >
          {de.impressum.footerLink}
          <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>
            {de.impressum.footerLinkRest}
          </Box>
        </Link>
      </Box>
    </PageContainer>
  );
}
