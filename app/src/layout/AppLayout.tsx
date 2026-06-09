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

import { DiagnosticDialog } from '../components/DiagnosticDialog';
import { GlyphSidebar } from '../components/GlyphSidebar';
import { PaperBackground } from '../components/PaperBackground';
import { SetupWizard } from '../components/wizard/SetupWizard';
import { useAdmin } from '../state';

const DRAWER_WIDTH = 280;

// The Einrichtungs-Wizard and the Diagnose modal are mounted once here — driven
// by `wizardGlyph` / `diagnoseGlyph` in the admin context — so the chart
// toolbar AND the sidebar can open them for any glyph from a single instance.
function AdminModals() {
  const { wizardGlyph, closeWizard, diagnoseGlyph } = useAdmin();
  return (
    <>
      <SetupWizard glyphKey={wizardGlyph ?? ''} open={wizardGlyph != null} onClose={closeWizard} />
      <DiagnosticDialog key={diagnoseGlyph ?? 'none'} />
    </>
  );
}

export function AppLayout() {
  const { source, loadError, waking } = useAdmin();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [navOpen, setNavOpen] = useState(false);

  if (loadError) {
    return (
      <PaperBackground minHeight="100dvh">
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
      </PaperBackground>
    );
  }

  if (!source) {
    return (
      <PaperBackground minHeight="100dvh">
        <Box sx={{ height: '100dvh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2 }}>
          <CircularProgress />
          <Typography color="text.secondary">
            {waking ? 'API startet (Cold Start), einen Moment…' : 'lade Quelle…'}
          </Typography>
        </Box>
      </PaperBackground>
    );
  }

  if (isMobile) {
    return (
      <PaperBackground minHeight="100dvh">
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100dvh' }}>
          <AppBar position="static" color="transparent" elevation={0} sx={{ borderBottom: 1, borderColor: 'divider' }}>
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
          <AdminModals />
        </Box>
      </PaperBackground>
    );
  }

  return (
    <PaperBackground minHeight="100vh">
      <Box sx={{ display: 'grid', gridTemplateColumns: `${DRAWER_WIDTH}px 1fr`, height: '100vh' }}>
        <GlyphSidebar />
        <Box sx={{ overflow: 'hidden', display: 'flex', flexDirection: 'column', minWidth: 0 }}>
          <Outlet />
        </Box>
        <AdminModals />
      </Box>
    </PaperBackground>
  );
}
