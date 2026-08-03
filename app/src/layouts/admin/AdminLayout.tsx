// The admin shell: one header over one scrolling work area, on every screen
// size. The old split — a permanent 280px letter sidebar on desktop, the same
// sidebar in a Drawer on phones — is gone with the redesign: the letters belong
// to the Buchstaben view (LetterPicker), the Vorlage to the header, and the
// Auftragskorb to its own drawer. What is left is genuinely global, so one
// layout serves both breakpoints and the mobile case stops being a special one.

import { Box } from '@mui/material';
import { Outlet } from 'react-router-dom';

import { BootStatus } from '@/components/BootStatus';
import { PaperBackground } from '@/components/PaperBackground';
import { useAdmin } from '@/context/AdminContext';
import { AdminModals } from '@/layouts/admin/AdminModals';
import { de } from '@/locales/admin';
import { AdminHeader } from '@/sections/admin/shell/AdminHeader';
import { KorbProvider, useKorb } from '@/sections/admin/shell/KorbContext';
import { WorkbenchDataProvider } from '@/sections/admin/shell/WorkbenchData';

// Split out so it can call useKorb() — the provider has to sit above it.
function AdminShell() {
  const { openCount, openKorb } = useKorb();
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100dvh' }}>
      <AdminHeader openCount={openCount} onOpenKorb={openKorb} />
      <Box component="main" sx={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <Outlet />
      </Box>
      <AdminModals />
    </Box>
  );
}

export function AdminLayout() {
  const { source, loadError, waking } = useAdmin();

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

  return (
    <PaperBackground minHeight="100dvh">
      {/* Both providers sit ABOVE the outlet, so walking between the three
          views keeps the loaded occurrences and the basket state — the whole
          point of one workbench instead of five pages. */}
      <WorkbenchDataProvider>
        <KorbProvider>
          <AdminShell />
        </KorbProvider>
      </WorkbenchDataProvider>
    </PaperBackground>
  );
}
