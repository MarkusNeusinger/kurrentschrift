// DiagnosticDialog — the analysis surface as its own large modal.
//
// One scrollable page instead of tabs: every processing stage is visible at
// once and captioned (what is shown, why the step matters) — Original →
// Skelett & Stützstellen → Kanonische Form → Einpassung → Fertig geschrieben.
// Opened by the chart toolbar's "Diagnose" button (and from the wizard's
// review step); mounted once in AppLayout and driven by `diagnoseGlyph` in
// the admin context.

import CloseIcon from '@mui/icons-material/Close';
import { Alert, Box, CircularProgress, Dialog, Divider, IconButton, Typography } from '@mui/material';
import { useEffect, useState } from 'react';

import { WrittenGlyph } from '@/components/WrittenGlyph';
import { knownGlyph } from '@/domain/glyphs';
import { useAdmin } from '@/context/AdminContext';
import type { DiagnosticData } from '@/lib/api';
import { de } from '@/locales/admin';
import { DiagnosticView } from './DiagnosticView';
import { FitView } from './FitView';
import { QualityView } from './QualityView';

// Big columns so the processing stages are legible; clamped to the viewport
// inside the views, so this is only a ceiling on wide screens.
const COL_W = 420;
const COL_H = 460;

function Section({ title, intro, children }: { title: string; intro: string; children: React.ReactNode }) {
  return (
    <Box>
      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5, maxWidth: 900 }}>
        {intro}
      </Typography>
      {children}
    </Box>
  );
}

export function DiagnosticDialog() {
  const { diagnoseGlyph, closeDiagnose, glyphsByKey, cropCacheBust } = useAdmin();
  const open = diagnoseGlyph != null;
  const glyphKey = diagnoseGlyph ?? '';
  const known = glyphKey ? knownGlyph(glyphKey) : null;
  const hasCanonical = glyphKey ? glyphsByKey[glyphKey]?.has_data === true : false;
  // The diagnostic payload fetched by DiagnosticView, shared with the
  // "Fertig geschrieben" stage so the same data isn't fetched twice per open.
  const [diag, setDiag] = useState<DiagnosticData | null>(null);
  useEffect(() => {
    setDiag(null);
  }, [glyphKey, cropCacheBust]);

  return (
    <Dialog open={open} onClose={closeDiagnose} fullWidth maxWidth="xl" slotProps={{ paper: { sx: { height: '92vh' } } }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2, pt: 1.5, pb: 1 }}>
        <Typography variant="h6" sx={{ flex: 1 }}>
          {de.admin.diagnostics.title} {known?.label ?? glyphKey}
        </Typography>
        <IconButton size="small" onClick={closeDiagnose} aria-label={de.admin.diagnostics.close}>
          <CloseIcon />
        </IconButton>
      </Box>
      <Box sx={{ flex: 1, minHeight: 0, overflow: 'auto', px: 2, pb: 3 }}>
        {!hasCanonical ? (
          <Alert severity="info">{de.admin.diagnostics.noCanonical}</Alert>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
            <Section title={de.admin.diagnostics.sectionPipeline} intro={de.admin.diagnostics.diagnosticIntro}>
              <DiagnosticView
                glyphKey={glyphKey}
                cropCacheBust={cropCacheBust}
                colWidth={COL_W}
                colHeight={COL_H}
                onData={setDiag}
              />
            </Section>
            <Divider />
            <Section title={de.admin.diagnostics.sectionFit} intro={de.admin.diagnostics.fitIntro}>
              <FitView glyphKey={glyphKey} cropCacheBust={cropCacheBust} colWidth={COL_W} colHeight={COL_H} />
            </Section>
            <Divider />
            <Section title={de.admin.quality.sectionTitle} intro={de.admin.quality.intro}>
              <QualityView glyphKey={glyphKey} cropCacheBust={cropCacheBust} />
            </Section>
            <Divider />
            <Section title={de.admin.diagnostics.sectionWritten} intro={de.admin.diagnostics.writtenCaption}>
              {/* Reuses DiagnosticView's payload (no second fetch); the key
                  remounts the writing performance when the canonical changes.
                  WrittenGlyph brings its own replay button. */}
              {diag ? (
                <WrittenGlyph
                  key={`${glyphKey}-${cropCacheBust ?? 0}`}
                  glyphKey={glyphKey}
                  cacheBust={cropCacheBust}
                  data={diag}
                  height={300}
                />
              ) : (
                <CircularProgress size={28} />
              )}
            </Section>
          </Box>
        )}
      </Box>
    </Dialog>
  );
}
