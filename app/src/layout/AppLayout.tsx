// Persistent layout shell: sidebar on the left, page content on the right.

import { Box, CircularProgress, Typography } from '@mui/material';
import { Outlet } from 'react-router-dom';

import { GlyphSidebar } from '../components/GlyphSidebar';
import { useAdmin } from '../state';

export function AppLayout() {
  const { source, loadError } = useAdmin();

  if (loadError) {
    return (
      <Box sx={{ p: 4 }}>
        <Typography variant="h5" gutterBottom>
          API nicht erreichbar
        </Typography>
        <Typography color="text.secondary">{loadError}</Typography>
        <Typography sx={{ mt: 2 }}>
          Läuft die API? <code>uv run uvicorn api.main:app --reload --port 8000</code>
        </Typography>
      </Box>
    );
  }

  if (!source) {
    return (
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2 }}>
        <CircularProgress />
        <Typography color="text.secondary">lade Quelle…</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: '280px 1fr', height: '100vh' }}>
      <GlyphSidebar />
      <Box sx={{ overflow: 'hidden', display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <Outlet />
      </Box>
    </Box>
  );
}
