// Schritt 5 · Übersicht & Freigabe — Diagnose link, the unified-vs-split
// (applyAll) choice and the lock summary. The lock button itself sits in the
// wizard footer ("Abschließen & sperren").

import VisibilityIcon from '@mui/icons-material/Visibility';
import { Alert, Box, Button, FormControlLabel, Radio, RadioGroup, Stack, Typography } from '@mui/material';

import { isLetterSplit, POSITION_LABEL } from '@/domain/glyphs';
import type { KnownGlyph } from '@/domain/glyphs';
import type { BboxOut } from '@/lib/api';

export function OverviewStep({
  glyphKey,
  known,
  hasCanonical,
  applyAll,
  setApplyAll,
  bboxesByKey,
  openDiagnose,
}: {
  glyphKey: string;
  known: KnownGlyph;
  hasCanonical: boolean;
  applyAll: boolean;
  setApplyAll: (v: boolean) => void;
  bboxesByKey: Record<string, BboxOut>;
  openDiagnose: (key: string) => void;
}) {
  return (
    <Stack spacing={2} sx={{ maxWidth: 640 }}>
      <Typography variant="subtitle2">Schritt 5 · Übersicht & Freigabe</Typography>
      <Typography variant="body2" color="text.secondary">
        Alles geprüft? Mit der <b>Diagnose</b> kannst du das Ergebnis groß ansehen: der reine
        Crop, das Skelett mit Ankern und die kanonische Vorlage nebeneinander (plus den M4-Fit).
      </Typography>
      {hasCanonical ? (
        <Button variant="outlined" startIcon={<VisibilityIcon />} onClick={() => openDiagnose(glyphKey)} sx={{ alignSelf: 'flex-start' }}>
          Diagnose öffnen
        </Button>
      ) : (
        <Alert severity="warning">Noch kein Weg gezeichnet — Schritt „Weg" zuerst.</Alert>
      )}
      <Box>
        <Typography variant="subtitle2" gutterBottom>
          Positionen (Anfang · Mitte · Ende)
        </Typography>
        <RadioGroup value={applyAll ? 'unified' : 'split'} onChange={(e) => setApplyAll(e.target.value === 'unified')}>
          <FormControlLabel value="unified" control={<Radio />} label="Eine Form für alle Positionen" />
          <FormControlLabel value="split" control={<Radio />} label={`Nur „${POSITION_LABEL[known.position]}“ getrennt einrichten (abweichende Form)`} />
        </RadioGroup>
        <Typography variant="caption" color="text.secondary" component="div">
          {applyAll
            ? 'Diese Form gilt für alle drei Positionen; die Anschlussstriche werden je Position aus Anfang/Ende erzeugt. Im Quiz und in der Sidebar erscheint der Buchstabe einmal.'
            : `Nur „${POSITION_LABEL[known.position]}“ bekommt diese Form, die anderen Positionen behalten ihre eigene. Der Buchstabe erscheint dann pro Position getrennt.`}
        </Typography>
        {isLetterSplit(glyphKey, bboxesByKey) && applyAll && (
          <Alert severity="warning" sx={{ mt: 1 }}>
            Der Buchstabe ist aktuell aufgetrennt — „Eine Form für alle“ überträgt <b>diese</b> Form auf
            alle drei Positionen und überschreibt die abweichenden.
          </Alert>
        )}
      </Box>
      <Typography variant="caption" color="text.secondary">
        Mit „Abschließen & sperren“ wird der Glyph gesperrt (🔒) und ist erst nach Entsperren wieder
        änderbar.
      </Typography>
    </Stack>
  );
}
