// Schritt 1 · Ausschluss (Radierer) — brush radius + undo. The eraser strokes
// themselves are painted on WizardCanvas and committed to bbox.mask_strokes.

import UndoIcon from '@mui/icons-material/Undo';
import { Box, Button, Slider, Stack, Typography } from '@mui/material';

import type { BboxOut } from '@/lib/api';

export function MaskStep({
  bbox,
  maskRadius,
  setMaskRadius,
  undoMask,
}: {
  bbox: BboxOut;
  maskRadius: number;
  setMaskRadius: (r: number) => void;
  undoMask: () => Promise<void>;
}) {
  return (
    <Stack spacing={1.5}>
      <Typography variant="subtitle2">Schritt 1 · Ausschluss (Radierer)</Typography>
      <Typography variant="body2" color="text.secondary">
        Auf den Lehrtafeln stehen die Buchstaben dicht beieinander — ragt Tinte vom Nachbarn
        in diesen Ausschnitt, verfälscht sie später Skelett und Anker. Mit dem Pinsel direkt
        über die störenden Stellen malen; das Übermalte wird vor der Skelettberechnung entfernt.
      </Typography>
      <Typography variant="body2" color="text.secondary">
        Nur fremde Tinte ausschließen — vom eigentlichen Buchstaben nichts wegradieren.
      </Typography>
      <Box>
        <Typography variant="caption">Pinselgröße: {maskRadius}px</Typography>
        <Slider size="small" min={2} max={30} value={maskRadius} onChange={(_e, v) => typeof v === 'number' && setMaskRadius(v)} />
      </Box>
      <Button size="small" startIcon={<UndoIcon />} disabled={bbox.mask_strokes.length === 0} onClick={undoMask}>
        Letzten Strich zurück ({bbox.mask_strokes.length})
      </Button>
    </Stack>
  );
}
