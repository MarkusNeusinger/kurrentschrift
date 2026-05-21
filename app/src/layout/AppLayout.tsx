// Persistent layout shell: sidebar on the left, page content on the right.
// Sidebar is always-visible so the user can jump between glyphs without
// going back to the chart. Page-specific actions render inside the page.

import { Box, CircularProgress, Typography } from '@mui/material';
import { Outlet } from 'react-router-dom';
import { GlyphSidebar } from '../components/GlyphSidebar';
import { useAdmin } from '../state';

export function AppLayout() {
  const { bboxes, loadError } = useAdmin();

  if (loadError) {
    return (
      <Box sx={{ p: 4 }}>
        <Typography variant="h5" gutterBottom>
          /api/bboxes konnte nicht geladen werden
        </Typography>
        <Typography color="text.secondary">{loadError}</Typography>
        <Typography sx={{ mt: 2 }}>
          Läuft die API? <code>uv run uvicorn api.main:app --reload --port 8000</code>
        </Typography>
      </Box>
    );
  }

  if (!bboxes) {
    return (
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2 }}>
        <CircularProgress />
        <Typography color="text.secondary">lade…</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: '260px 1fr', height: '100vh' }}>
      <GlyphSidebar />
      <Box sx={{ overflow: 'hidden', display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <Outlet />
      </Box>
    </Box>
  );
}
