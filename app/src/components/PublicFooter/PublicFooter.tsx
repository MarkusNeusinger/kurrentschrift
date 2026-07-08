// Shared footer for every public page: a hairline, a warm one-line sign-off
// (the "private Liebhaberei" voice from the impressum) on the left, and a
// small link row on the right — the public GitHub repository, the operator's
// sibling project anyplot.ai, and Impressum/Datenschutz. Rendered by
// <PublicLayout> after the page content (inside <PaperBackground>), so it's
// identical everywhere.
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

const footerLink = {
  color: paper.sepia,
  textDecoration: 'none',
  '&:hover': { color: paper.viridian },
} as const;

// Decorative middot between the footer links.
function Dot() {
  return (
    <Typography component="span" variant="body2" aria-hidden="true" sx={{ color: paper.sepia, opacity: 0.5 }}>
      ·
    </Typography>
  );
}

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
          // Three links no longer fit beside the tagline on a phone — there the
          // link row wraps onto its own line instead of truncating.
          flexWrap: { xs: 'wrap', sm: 'nowrap' },
          justifyContent: 'space-between',
          alignItems: 'center',
          columnGap: 2,
          rowGap: 0.75,
        }}
      >
        <Typography sx={{ fontFamily: garamond, fontStyle: 'italic', color: paper.inkSoft }}>
          {de.common.footer.tagline}
          <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>
            {de.common.footer.taglineRest}
          </Box>
        </Typography>
        {/* `ml: 'auto'` keeps the row on the right edge when it wraps below the tagline. */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, ml: 'auto', flexShrink: 0 }}>
          <Link
            href={de.common.footer.githubUrl}
            target="_blank"
            rel="noopener noreferrer"
            variant="body2"
            sx={footerLink}
          >
            {de.common.footer.github}
          </Link>
          <Dot />
          <Link component={RouterLink} to={paths.impressum} variant="body2" sx={footerLink}>
            {de.impressum.footerLink}
            <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>
              {de.impressum.footerLinkRest}
            </Box>
          </Link>
        </Box>
      </Box>
    </PageContainer>
  );
}
