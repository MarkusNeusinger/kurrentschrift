// Router-level error surface. Its main real-world trigger is a failed lazy
// chunk load (e.g. an old tab requesting hashed chunks that a new deploy
// replaced) — a full reload fetches the current bundle and recovers.
import { Box, Button, Typography } from '@mui/material';
import { useRouteError } from 'react-router-dom';

import { PaperBackground } from '@/components/PaperBackground';

export function RouteError() {
  const error = useRouteError();
  return (
    <PaperBackground minHeight="100dvh">
      <Box
        sx={{
          minHeight: '100dvh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 2,
          px: 3,
          textAlign: 'center',
        }}
      >
        <Typography variant="h5">Da ist etwas schiefgegangen.</Typography>
        <Typography color="text.secondary" sx={{ maxWidth: 480 }}>
          Vermutlich ist die Seite veraltet (neue Version veröffentlicht). Ein Neuladen behebt das
          in der Regel.
        </Typography>
        {error instanceof Error && (
          <Typography variant="body2" color="text.disabled">
            {error.message}
          </Typography>
        )}
        <Button variant="outlined" onClick={() => window.location.reload()}>
          Seite neu laden
        </Button>
      </Box>
    </PaperBackground>
  );
}
