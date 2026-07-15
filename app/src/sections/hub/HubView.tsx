// HubView — the shared layout for the two area hubs (/lesen, /schreiben). Each
// hub is a small overview page: a page title, a one-line lead, and a grid of
// cards that lead into the actual tools (Quiz/Tafel, Übungsblatt/Federprobe).
// Same "paper & ink" identity as every public page; sizes come from the theme
// type ladder, surfaces from styles/paper. Card content is passed in by the
// thin page wrappers (strings from locales/de/hub, URLs from routes/paths).

import { Box, Typography } from '@mui/material';

import { PageContainer } from '@/components/PageContainer';
import { PageHeader } from '@/components/PageHeader';
import { PaperCardCta, PaperCardLink } from '@/components/PaperCardLink';
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
            <PaperCardLink key={card.to} to={card.to} sx={{ p: { xs: 3, md: 3.5 } }}>
              {/* h2: the cards sit directly under the PageHeader <h1> */}
              <Typography
                variant="h3"
                component="h2"
                sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, mb: 1 }}
              >
                {card.title}
              </Typography>
              <Typography variant="body2" sx={{ color: paper.inkSoft, flexGrow: 1 }}>
                {card.body}
              </Typography>
              <PaperCardCta>{card.cta}&nbsp;→</PaperCardCta>
            </PaperCardLink>
          ))}
        </Box>
      </PageContainer>
    </PublicLayout>
  );
}
