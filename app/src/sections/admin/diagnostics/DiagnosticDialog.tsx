// DiagnosticDialog — the analysis surface as its own large modal.
//
// The advanced EditorPage was retired; its 3-column diagnostic and the M4 fit
// overlay now live here, opened by the chart toolbar's "Diagnose" button (and
// from the wizard's review step). It is mounted once in AppLayout and driven by
// `diagnoseGlyph` in the admin context, so the columns get the full modal width
// instead of being squeezed into a 320px side panel.

import CloseIcon from '@mui/icons-material/Close';
import { Alert, Box, Dialog, IconButton, Tab, Tabs, Typography } from '@mui/material';
import { useEffect, useState } from 'react';

import { knownGlyph } from '@/domain/glyphs';
import { useAdmin } from '@/context/AdminContext';
import { de } from '@/locales';
import { DiagnosticView } from './DiagnosticView';
import { FitView } from './FitView';

// Big columns so the processing stages are legible; clamped to the viewport
// inside the views, so this is only a ceiling on wide screens.
const COL_W = 420;
const COL_H = 460;

export function DiagnosticDialog() {
  const { diagnoseGlyph, closeDiagnose, glyphsByKey, cropCacheBust } = useAdmin();
  const open = diagnoseGlyph != null;
  const glyphKey = diagnoseGlyph ?? '';
  const known = glyphKey ? knownGlyph(glyphKey) : null;
  const hasCanonical = glyphKey ? glyphsByKey[glyphKey]?.has_data === true : false;
  const [tab, setTab] = useState<'diagnostic' | 'fit'>('diagnostic');

  // Reset to the first tab whenever a different glyph is opened.
  useEffect(() => {
    if (open) setTab('diagnostic');
  }, [open, glyphKey]);

  return (
    <Dialog open={open} onClose={closeDiagnose} fullWidth maxWidth="xl" slotProps={{ paper: { sx: { height: '92vh' } } }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2, pt: 1.5 }}>
        <Typography variant="h6" sx={{ flex: 1 }}>
          {de.admin.diagnostics.title} {known?.label ?? glyphKey}
        </Typography>
        <IconButton size="small" onClick={closeDiagnose} aria-label={de.admin.diagnostics.close}>
          <CloseIcon />
        </IconButton>
      </Box>
      <Tabs value={tab} onChange={(_e, v) => setTab(v)} sx={{ px: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Tab value="diagnostic" label={de.admin.diagnostics.tabDiagnostic} />
        <Tab value="fit" label={de.admin.diagnostics.tabFit} />
      </Tabs>
      <Box sx={{ flex: 1, minHeight: 0, overflow: 'auto', p: 2 }}>
        {!hasCanonical ? (
          <Alert severity="info">{de.admin.diagnostics.noCanonical}</Alert>
        ) : tab === 'diagnostic' ? (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
              {de.admin.diagnostics.diagnosticIntro}
            </Typography>
            <DiagnosticView glyphKey={glyphKey} cropCacheBust={cropCacheBust} colWidth={COL_W} colHeight={COL_H} />
          </>
        ) : (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
              {de.admin.diagnostics.fitIntro}
            </Typography>
            <FitView glyphKey={glyphKey} cropCacheBust={cropCacheBust} colWidth={COL_W} colHeight={COL_H} />
          </>
        )}
      </Box>
    </Dialog>
  );
}
