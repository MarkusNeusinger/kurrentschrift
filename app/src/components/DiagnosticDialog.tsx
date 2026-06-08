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

import { knownGlyph } from '../constants';
import { useAdmin } from '../state';
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
          Diagnose · {known?.label ?? glyphKey}
        </Typography>
        <IconButton size="small" onClick={closeDiagnose} aria-label="Diagnose schließen">
          <CloseIcon />
        </IconButton>
      </Box>
      <Tabs value={tab} onChange={(_e, v) => setTab(v)} sx={{ px: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Tab value="diagnostic" label="Skelett & Canonical" />
        <Tab value="fit" label="Fit (M4)" />
      </Tabs>
      <Box sx={{ flex: 1, minHeight: 0, overflow: 'auto', p: 2 }}>
        {!hasCanonical ? (
          <Alert severity="info">Noch kein Canonical — erst im Einrichten-Wizard einen Weg zeichnen und speichern.</Alert>
        ) : tab === 'diagnostic' ? (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
              Die drei Verarbeitungsschritte nebeneinander: der reine Loth-Crop, das daraus
              gewonnene Skelett mit den abgetasteten Ankern und schließlich die kanonische Vorlage
              in Template-Koordinaten (Grundlinie = 0, Mittellinie = 1).
            </Typography>
            <DiagnosticView glyphKey={glyphKey} cropCacheBust={cropCacheBust} colWidth={COL_W} colHeight={COL_H} />
          </>
        ) : (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
              Die kanonische Vorlage auf ihr eigenes Skelett gefittet (M4): Skelett, Vorlage (grau)
              und Fit (rot) übereinander, dazu die Fehlermaße. Mit dem λ-Regler die
              Regularisierung abwägen — niedrig folgt dem Skelett, hoch hält die Form zusammen.
            </Typography>
            <FitView glyphKey={glyphKey} cropCacheBust={cropCacheBust} colWidth={COL_W} colHeight={COL_H} />
          </>
        )}
      </Box>
    </Dialog>
  );
}
