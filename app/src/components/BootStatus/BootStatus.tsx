// BootStatus — boot state (loading spinner / load error) shared by the public
// quiz/tafel and the admin layout. The consumers draw different chrome (the
// public pages a centered block, the admin shell the paper texture with
// top-left error copy); pixel parity beats unification, so the component keeps
// both looks behind an explicit `shell` prop instead of forcing one onto the
// other.
//
// The plain shell is a centered block WITHOUT its own <main>/background: the
// public consumers render it inside <PublicLayout> (which owns the paper
// atmosphere, the <main> landmark, header and footer), so the navigation stays
// usable during a cold-start boot or an error instead of vanishing with the
// page chrome.

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
  // 'plain' = centered block inside an existing layout (quiz/tafel, within
  // PublicLayout); 'paper' = standalone PaperBackground shell with the admin's
  // top-left error block / centered spinner.
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
      sx={{
        // Tall enough to read as the page body between header and footer, but
        // no viewport-filling block — the surrounding PublicLayout owns those.
        minHeight: '55vh',
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
