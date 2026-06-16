// BootStatus — full-page boot screen (loading spinner / load error) shared by
// the public quiz and the admin layout. The two consumers draw different
// chrome today (the quiz a flat centered page on `background.default`, the
// admin shell the paper texture with top-left error copy); pixel parity beats
// unification, so the component keeps both looks behind an explicit `shell`
// prop instead of forcing one onto the other.
//
// The plain shell roots on `<main>` so the public quiz route still exposes
// exactly one main landmark in its loading/error states (the loaded state gets
// its `<main>` from PublicLayout instead) — the two are mutually exclusive
// returns, so there is never a double landmark.

import { Box, Button, CircularProgress, Typography } from '@mui/material';
import type { ReactNode } from 'react';

import { PaperBackground } from '@/components/PaperBackground';

interface BootStatusProps {
  variant: 'loading' | 'error';
  title?: string;
  message?: ReactNode;
  // Extra explanatory paragraph under the error message (may carry markup,
  // e.g. a <code> dev-server hint).
  detail?: ReactNode;
  onRetry?: () => void;
  retryLabel?: string;
  // 'plain' = flat centered page (quiz); 'paper' = PaperBackground shell with
  // the admin's top-left error block / centered spinner.
  shell?: 'plain' | 'paper';
}

export function BootStatus({ variant, title, message, detail, onRetry, retryLabel, shell = 'plain' }: BootStatusProps) {
  if (shell === 'paper') {
    if (variant === 'error') {
      return (
        <PaperBackground minHeight="100dvh">
          <Box sx={{ p: 4 }}>
            <Typography variant="h5" gutterBottom>
              {title}
            </Typography>
            <Typography color="text.secondary">{message}</Typography>
            {detail != null && <Typography sx={{ mt: 2 }}>{detail}</Typography>}
            {onRetry && (
              <Button variant="outlined" sx={{ mt: 2 }} onClick={onRetry}>
                {retryLabel}
              </Button>
            )}
          </Box>
        </PaperBackground>
      );
    }
    return (
      <PaperBackground minHeight="100dvh">
        <Box sx={{ height: '100dvh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2 }}>
          <CircularProgress />
          <Typography color="text.secondary">{message}</Typography>
        </Box>
      </PaperBackground>
    );
  }

  return (
    <Box
      component="main"
      sx={{
        minHeight: '100vh',
        bgcolor: 'background.default',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        p: 4,
      }}
    >
      {variant === 'error' ? (
        <>
          <Typography variant="h6" gutterBottom>
            {title}
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 2 }}>
            {message}
          </Typography>
          {onRetry && (
            <Button variant="outlined" onClick={onRetry}>
              {retryLabel}
            </Button>
          )}
        </>
      ) : (
        <>
          <CircularProgress />
          <Typography color="text.secondary" sx={{ mt: 2 }}>
            {message}
          </Typography>
        </>
      )}
    </Box>
  );
}
