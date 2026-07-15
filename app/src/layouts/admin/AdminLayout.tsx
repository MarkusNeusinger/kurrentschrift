// Persistent layout shell: on desktop the sidebar sits on the left next to the
// page content; on mobile it collapses into a temporary Drawer opened from a
// top app bar, so the full width is available for the chart / editor.

import MenuIcon from '@mui/icons-material/Menu';
import {
  AppBar,
  Box,
  Drawer,
  IconButton,
  Toolbar,
  Typography,
  useMediaQuery,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useState } from 'react';
import { Outlet } from 'react-router-dom';

import { BootStatus } from '@/components/BootStatus';
import { PaperBackground } from '@/components/PaperBackground';
import { useAdmin } from '@/context/AdminContext';
import { AdminModals } from '@/layouts/admin/AdminModals';
import { de } from '@/locales/admin';
import { GlyphSidebar } from '@/sections/admin/sidebar/GlyphSidebar';

const DRAWER_WIDTH = 280;

export function AdminLayout() {
  const { source, loadError, waking } = useAdmin();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [navOpen, setNavOpen] = useState(false);

  if (loadError) {
    return (
      <BootStatus
        shell="paper"
        variant="error"
        title={de.common.boot.apiUnreachable}
        message={loadError}
        detail={
          <>
            {de.common.boot.apiUnreachableDetail}{' '}
            {de.common.boot.apiUnreachableDevHint} <code>uv run uvicorn api.main:app --reload --port 8000</code>.
          </>
        }
        onRetry={() => window.location.reload()}
        retryLabel={de.common.boot.retry}
      />
    );
  }

  if (!source) {
    return (
      <BootStatus
        shell="paper"
        variant="loading"
        message={waking ? de.common.boot.apiColdStart : de.common.boot.loadingSource}
      />
    );
  }

  if (isMobile) {
    return (
      <PaperBackground minHeight="100dvh">
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100dvh' }}>
          <AppBar position="static" color="transparent" elevation={0} sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Toolbar variant="dense" sx={{ gap: 1 }}>
              <IconButton edge="start" aria-label={de.admin.layout.openMenu} onClick={() => setNavOpen(true)}>
                <MenuIcon />
              </IconButton>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                {de.common.brand.name}
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
