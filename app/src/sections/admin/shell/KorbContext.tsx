// The Auftragskorb as a workbench-wide facility instead of a panel on one page.
//
// Every view can complain about what it shows — a letter, a join, a whole word,
// and since the redesign also a freely typed combination that no plate ever
// wrote. So the filing dialog and the basket itself are mounted ONCE in the
// admin shell and reached through this context; a view only has to say WHAT it
// wants to file (`fileMark`). The open count travels back out for the header
// badge.
//
// The basket read is admin-gated and may 401. That must stay a quiet absence:
// `openCount` is then null (no badge, not a claimed zero) and the drawer shows
// the panel's own error line, while the views around it keep working.

import CloseIcon from '@mui/icons-material/Close';
import { Box, Drawer, IconButton, Typography } from '@mui/material';
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

import { useAdmin } from '@/context/AdminContext';
import { listWorkItems } from '@/lib/api';
import { de } from '@/locales/admin';

import { KorbPanel } from './KorbPanel';
import { MarkDialog } from './MarkDialog';
import { markKey, type Mark } from './model';

interface KorbState {
  // Open + returned items of the active source; null while unknown or when the
  // admin-gated read failed.
  openCount: number | null;
  fileMark: (mark: Mark) => void;
  openKorb: () => void;
}

const Ctx = createContext<KorbState | null>(null);

export function KorbProvider({ children }: { children: ReactNode }) {
  const { sourceId, openWizard } = useAdmin();
  const [mark, setMark] = useState<Mark | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [openCount, setOpenCount] = useState<number | null>(null);
  // Bumped after a filing or a basket mutation so both the count and the panel
  // refetch — the panel keeps its own optimistic state, this only re-syncs.
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setOpenCount(null);
    listWorkItems(sourceId, undefined, { retries: 1 })
      .then((rows) => {
        if (!cancelled) setOpenCount(rows.filter((i) => i.status === 'open' || i.status === 'returned').length);
      })
      .catch(() => {
        if (!cancelled) setOpenCount(null);
      });
    return () => {
      cancelled = true;
    };
  }, [sourceId, tick]);

  const value = useMemo<KorbState>(
    () => ({
      openCount,
      fileMark: (next: Mark) => setMark(next),
      openKorb: () => setDrawerOpen(true),
    }),
    [openCount],
  );

  return (
    <Ctx.Provider value={value}>
      {children}
      <Drawer
        anchor="right"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        // Full width on phones, a readable column on desktop — the basket is a
        // list of prose notes, not a data table.
        sx={{ '& .MuiDrawer-paper': { width: { xs: '100%', sm: 460 }, maxWidth: '100%', p: 2 } }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <Typography variant="subtitle1" sx={{ flex: 1 }}>
            {de.admin.werkbank.korbTitle}
          </Typography>
          <IconButton size="small" aria-label={de.admin.shell.closeKorb} onClick={() => setDrawerOpen(false)}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </Box>
        <KorbPanel
          sourceId={sourceId}
          refreshKey={tick}
          onChanged={() => setTick((n) => n + 1)}
          onNavigate={() => setDrawerOpen(false)}
        />
      </Drawer>
      {mark && (
        <MarkDialog
          key={markKey(mark)}
          mark={mark}
          sourceId={sourceId}
          onClose={() => setMark(null)}
          onFiled={() => setTick((n) => n + 1)}
          onOpenWizard={openWizard}
        />
      )}
    </Ctx.Provider>
  );
}

export function useKorb(): KorbState {
  const value = useContext(Ctx);
  if (!value) throw new Error('useKorb must be used inside <KorbProvider>');
  return value;
}

// The ⚑ affordance every view files with, so the wording and the icon stay the
// same wherever a complaint is raised.
export function useFileMark(): (mark: Mark) => void {
  return useKorb().fileMark;
}

export const useOpenCount = (): number | null => useKorb().openCount;
