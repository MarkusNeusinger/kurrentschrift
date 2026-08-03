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

import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { Alert, Box, ButtonBase, Chip, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';

import { useAdmin } from '@/context/AdminContext';
import { de, fmt, styleLabel } from '@/locales/admin';
import { paths } from '@/routes/paths';
import { display, garamond } from '@/styles/paper';

export function StartView() {
  const { sources, sourceId, switchSource } = useAdmin();
  const navigate = useNavigate();
  const t = de.admin.shell;

  const choose = (id: string) => {
    if (id !== sourceId) switchSource(id);
    navigate(paths.admin.letters);
  };

  return (
    <Box sx={{ p: { xs: 2, md: 4 }, maxWidth: 900, mx: 'auto', width: '100%' }}>
      <Typography sx={{ fontFamily: display, fontSize: 28, fontWeight: 600, mb: 0.5 }}>{t.startTitle}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3, maxWidth: 640 }}>
        {t.startIntro}
      </Typography>

      {sources.length === 0 ? (
        <Alert severity="warning">{t.startNoSources}</Alert>
      ) : (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2 }}>
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
                  p: 2,
                  bgcolor: 'background.paper',
                  '&:hover': { borderColor: 'primary.light' },
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                  <Typography sx={{ fontFamily: garamond, fontSize: 20, flex: 1 }}>{styleLabel(s.style_id)}</Typography>
                  {active && <CheckCircleIcon fontSize="small" color="primary" />}
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                  {s.id}
                </Typography>
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 1 }}>
                  <Chip size="small" variant="outlined" label={fmt(t.startRatio, { ratio: s.style_ratio.join(':') })} />
                  <Chip size="small" variant="outlined" label={fmt(t.startSlant, { deg: s.slant_deg })} />
                </Box>
              </ButtonBase>
            );
          })}
        </Box>
      )}

      <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mt: 3 }}>
        {t.startHint}
      </Typography>
    </Box>
  );
}
