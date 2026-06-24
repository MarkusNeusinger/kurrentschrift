// Shared footer for every public page: a hairline, a warm one-line sign-off
// (the "private Liebhaberei" voice from the impressum) on the left, the
// Impressum/Datenschutz link on the right. Rendered by <PublicLayout> after the
// page content (inside <PaperBackground>), so it's identical everywhere.

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
          mt: { xs: 6, md: 8 },
          py: 3,
          display: 'flex',
          flexDirection: { xs: 'column', sm: 'row' },
          justifyContent: 'space-between',
          alignItems: { xs: 'flex-start', sm: 'center' },
          gap: 1.5,
        }}
      >
        <Typography sx={{ fontFamily: garamond, fontStyle: 'italic', color: paper.inkSoft }}>
          {de.common.footer.tagline}
        </Typography>
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
