// HubView — the shared layout for the two area hubs (/lesen, /schreiben). Each
// hub is a small overview page: a page title, a one-line lead, and a grid of
// cards that lead into the actual tools (Quiz/Tafel, Übungsblatt/Federprobe).
// Same "paper & ink" identity as every public page; sizes come from the theme
// type ladder, surfaces from styles/paper. Card content is passed in by the
// thin page wrappers (strings from locales/de/hub, URLs from routes/paths).

import { Box, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

import { PageContainer } from '@/components/PageContainer';
import { PageHeader } from '@/components/PageHeader';
import { PublicLayout } from '@/layouts/public/PublicLayout';
import { display, paper } from '@/styles/paper';

export interface HubCard {
  title: string;
  body: string;
  cta: string;
  to: string;
}

export interface HubViewProps {
  title: string;
  lead: string;
  cards: HubCard[];
}

export function HubView({ title, lead, cards }: HubViewProps) {
  return (
    <PublicLayout>
      <PageContainer sx={{ pt: { xs: 4, md: 7 } }}>
        <PageHeader title={title}>
          <Typography variant="body1" sx={{ color: paper.inkSoft }}>
            {lead}
          </Typography>
        </PageHeader>

        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' },
            gap: { xs: 2.5, md: 3 },
          }}
        >
          {cards.map((card) => (
            <Box
              key={card.to}
              component={RouterLink}
              to={card.to}
              sx={{
                display: 'flex',
                flexDirection: 'column',
                textDecoration: 'none',
                p: { xs: 3, md: 3.5 },
                bgcolor: paper.hi,
                border: `1px solid ${paper.line}`,
                borderRadius: 2,
                color: paper.ink,
                transition: 'border-color .25s, transform .25s, box-shadow .25s',
                // Hover and keyboard focus get the same affordance so tabbing
                // through the cards reads as clearly as pointing at them.
                '&:hover, &:focus-visible': {
                  borderColor: paper.viridian,
                  transform: 'translateY(-2px)',
                  boxShadow: '0 8px 24px rgba(36,26,16,0.10)',
                },
                '&:focus-visible': {
                  outline: `2px solid ${paper.viridian}`,
                  outlineOffset: 3,
                },
                '&:hover .hub-cta::after, &:focus-visible .hub-cta::after': { width: '100%' },
              }}
            >
              <Typography
                variant="h3"
                sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, mb: 1 }}
              >
                {card.title}
              </Typography>
              <Typography variant="body2" sx={{ color: paper.inkSoft, flexGrow: 1 }}>
                {card.body}
              </Typography>
              <Typography
                className="hub-cta"
                component="span"
                variant="body2"
                sx={{
                  mt: 2.5,
                  alignSelf: 'flex-start',
                  position: 'relative',
                  color: paper.viridian,
                  fontFamily: display,
                  '&::after': {
                    content: '""',
                    position: 'absolute',
                    left: 0,
                    bottom: -3,
                    height: '1px',
                    width: 0,
                    bgcolor: paper.viridian,
                    transition: 'width .3s ease',
                  },
                }}
              >
                {card.cta}&nbsp;→
              </Typography>
            </Box>
          ))}
        </Box>
      </PageContainer>
    </PublicLayout>
  );
}
