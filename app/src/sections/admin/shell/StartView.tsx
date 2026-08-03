// The way into the admin: pick the Vorlage first, then work.
//
// The old admin dropped straight into a chart with a source select buried in
// the sidebar, which made "which script am I even editing?" a question you had
// to go looking for. Everything below the entry — every letter, every join,
// every word — belongs to exactly ONE source and its hand, so choosing it is
// the first act, not a setting.
//
// The card for the ACTIVE source is marked as such, so re-entering /admin from
// the header chip reads as "you are here, switch if you want" rather than as a
// blank question.
//
// Typography and layout come from the public design system (PageContainer +
// PageHeader): this is the admin's front door and the one screen that is pure
// choice rather than work surface, so it is set exactly like a public page.

import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { Alert, Box, ButtonBase, Chip, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';

import { PageContainer } from '@/components/PageContainer';
import { PageHeader } from '@/components/PageHeader';
import { useAdmin } from '@/context/AdminContext';
import { de, fmt, styleLabel } from '@/locales/admin';
import { paths } from '@/routes/paths';
import { display, letterpress, paper } from '@/styles/paper';

export function StartView() {
  const { sources, sourceId, switchSource } = useAdmin();
  const navigate = useNavigate();
  const t = de.admin.shell;

  const choose = (id: string) => {
    if (id !== sourceId) switchSource(id);
    navigate(paths.admin.letters);
  };

  return (
    <PageContainer component="section" sx={{ pt: { xs: 4, md: 6 }, pb: { xs: 6, md: 8 } }}>
      <PageHeader eyebrow={t.startEyebrow} title={t.startTitle}>
        <Typography variant="body1" sx={{ color: paper.inkSoft }}>
          {t.startIntro}
        </Typography>
      </PageHeader>

      {sources.length === 0 ? (
        <Alert severity="warning">{t.startNoSources}</Alert>
      ) : (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' },
            gap: 2.5,
          }}
        >
          {sources.map((s) => {
            const active = s.id === sourceId;
            return (
              <ButtonBase
                key={s.id}
                onClick={() => choose(s.id)}
                sx={{
                  textAlign: 'left',
                  display: 'block',
                  border: 1,
                  borderColor: active ? 'primary.main' : 'divider',
                  borderRadius: 2,
                  p: 2.5,
                  bgcolor: 'background.paper',
                  transition: 'border-color .2s',
                  '&:hover': { borderColor: 'primary.main' },
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                  <Typography
                    component="h2"
                    sx={{
                      flex: 1,
                      fontFamily: display,
                      fontWeight: 600,
                      fontSize: '1.45rem',
                      lineHeight: 1.3,
                      color: paper.ink,
                      textShadow: letterpress,
                    }}
                  >
                    {styleLabel(s.style_id)}
                  </Typography>
                  {active && <CheckCircleIcon fontSize="small" color="primary" />}
                </Box>
                {/* The plate itself, then its id: „Sütterlin" alone does not say
                    which chart the workbench will open. */}
                <Typography variant="body2" sx={{ color: paper.inkSoft }}>
                  {s.title}
                </Typography>
                <Typography variant="caption" sx={{ display: 'block', color: paper.sepia, mt: 0.25 }}>
                  {s.id}
                </Typography>
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 1.5 }}>
                  <Chip size="small" variant="outlined" label={fmt(t.startRatio, { ratio: s.style_ratio.join(':') })} />
                  <Chip size="small" variant="outlined" label={fmt(t.startSlant, { deg: s.slant_deg })} />
                </Box>
              </ButtonBase>
            );
          })}
        </Box>
      )}

      <Typography variant="caption" sx={{ display: 'block', mt: 3, color: paper.sepia }}>
        {t.startHint}
      </Typography>
    </PageContainer>
  );
}
