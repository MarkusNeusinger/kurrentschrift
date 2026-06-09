// Schritt 1 · Ausschluss (Radierer) — brush radius + undo. The eraser strokes
// themselves are painted on WizardCanvas and committed to bbox.mask_strokes.

import UndoIcon from '@mui/icons-material/Undo';
import { Box, Button, Slider, Stack, Typography } from '@mui/material';

import { de } from '@/locales';
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
      <Typography variant="subtitle2">{de.wizard.mask.title}</Typography>
      <Typography variant="body2" color="text.secondary">
        {de.wizard.mask.body1}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {de.wizard.mask.body2}
      </Typography>
      <Box>
        <Typography variant="caption">{de.wizard.mask.brushSize} {maskRadius}px</Typography>
        <Slider size="small" min={2} max={30} value={maskRadius} onChange={(_e, v) => typeof v === 'number' && setMaskRadius(v)} />
      </Box>
      <Button size="small" startIcon={<UndoIcon />} disabled={bbox.mask_strokes.length === 0} onClick={undoMask}>
        {de.wizard.mask.undo} ({bbox.mask_strokes.length})
      </Button>
    </Stack>
  );
}
