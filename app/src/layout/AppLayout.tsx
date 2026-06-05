// Persistent layout shell: on desktop the sidebar sits on the left next to the
// page content; on mobile it collapses into a temporary Drawer opened from a
// top app bar, so the full width is available for the chart / editor.

import MenuIcon from '@mui/icons-material/Menu';
import {
  AppBar,
  Box,
  Button,
  CircularProgress,
  Drawer,
  IconButton,
  Toolbar,
  Typography,
  useMediaQuery,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useState } from 'react';
import { Outlet } from 'react-router-dom';

import { GlyphSidebar } from '../components/GlyphSidebar';
import { useAdmin } from '../state';

const DRAWER_WIDTH = 280;

export function AppLayout() {
  const { source, loadError, waking } = useAdmin();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [navOpen, setNavOpen] = useState(false);

  if (loadError) {
    return (
      <Box sx={{ p: 4 }}>
        <Typography variant="h5" gutterBottom>
          API nicht erreichbar
        </Typography>
        <Typography color="text.secondary">{loadError}</Typography>
        <Typography sx={{ mt: 2 }}>
          Die API (Cloud Run) konnte auch nach mehreren Versuchen nicht erreicht werden.
          Im lokalen Dev läuft sie über <code>uv run uvicorn api.main:app --reload --port 8000</code>.
        </Typography>
        <Button variant="outlined" sx={{ mt: 2 }} onClick={() => window.location.reload()}>
          Erneut versuchen
        </Button>
      </Box>
    );
  }

  if (!source) {
    return (
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2 }}>
        <CircularProgress />
        <Typography color="text.secondary">
          {waking ? 'API startet (Cold Start), einen Moment…' : 'lade Quelle…'}
        </Typography>
      </Box>
    );
  }

  if (isMobile) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100dvh' }}>
        <AppBar position="static" color="default" elevation={1}>
          <Toolbar variant="dense" sx={{ gap: 1 }}>
            <IconButton edge="start" aria-label="Menü öffnen" onClick={() => setNavOpen(true)}>
              <MenuIcon />
            </IconButton>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              kurrentschrift
            </Typography>
          </Toolbar>
        </AppBar>
        <Drawer
          open={navOpen}
          onClose={() => setNavOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{ '& .MuiDrawer-paper': { width: DRAWER_WIDTH, maxWidth: '85vw' } }}
        >
          <GlyphSidebar onNavigate={() => setNavOpen(false)} />
        </Drawer>
        <Box sx={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <Outlet />
        </Box>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: `${DRAWER_WIDTH}px 1fr`, height: '100vh' }}>
      <GlyphSidebar />
      <Box sx={{ overflow: 'hidden', display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <Outlet />
      </Box>
    </Box>
  );
}
