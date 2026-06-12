// Step 1 "Ausschluss & Tinte" — two brushes sharing one radius: the eraser
// (Radierer) blanks neighbour ink, the ink brush (Tinte) fills white specks.
// Plus the per-glyph "Lücken füllen" auto-fill threshold. The strokes are
// painted on WizardCanvas and committed to bbox.mask_strokes / bbox.ink_strokes;
// the fill threshold persists to bbox.fill_holes_max_area.

import UndoIcon from '@mui/icons-material/Undo';
import {
  Box,
  Button,
  Divider,
  FormControlLabel,
  Slider,
  Stack,
  Switch,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { useEffect, useState } from 'react';

import { de } from '@/locales';
import type { BboxOut } from '@/lib/api';

const AUTO_FILL_COLOR = '#1fa85a'; // matches crop_mask_to_png_bytes' green

const FILL_MAX = 160; // px²: above this the slider risks eating real counters

export function MaskStep({
  bbox,
  maskRadius,
  setMaskRadius,
  tool,
  setTool,
  showMask,
  setShowMask,
  undoMask,
  undoInk,
  setFillHoles,
}: {
  bbox: BboxOut;
  maskRadius: number;
  setMaskRadius: (r: number) => void;
  tool: 'eraser' | 'ink';
  setTool: (t: 'eraser' | 'ink') => void;
  showMask: boolean;
  setShowMask: (v: boolean) => void;
  undoMask: () => Promise<void>;
  undoInk: () => Promise<void>;
  setFillHoles: (v: number) => void | Promise<void>;
}) {
  // Live slider value, synced from the stored bbox; committed (PUT) only on
  // release so dragging doesn't spam the server.
  const [fill, setFill] = useState(bbox.fill_holes_max_area);
  useEffect(() => setFill(bbox.fill_holes_max_area), [bbox.fill_holes_max_area]);

  const isInk = tool === 'ink';
  const undoCount = isInk ? bbox.ink_strokes.length : bbox.mask_strokes.length;

  return (
    <Stack spacing={1.5}>
      <Typography variant="subtitle2">{de.wizard.mask.title}</Typography>

      <ToggleButtonGroup
        size="small"
        exclusive
        value={tool}
        onChange={(_e, v: 'eraser' | 'ink' | null) => v && setTool(v)}
        fullWidth
      >
        <ToggleButton value="eraser">{de.wizard.mask.toolEraser}</ToggleButton>
        <ToggleButton value="ink">{de.wizard.mask.toolInk}</ToggleButton>
      </ToggleButtonGroup>

      {isInk ? (
        <Typography variant="body2" color="text.secondary">
          {de.wizard.mask.inkBody}
        </Typography>
      ) : (
        <>
          <Typography variant="body2" color="text.secondary">
            {de.wizard.mask.body1}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {de.wizard.mask.body2}
          </Typography>
        </>
      )}

      <Box>
        <Typography variant="caption">
          {de.wizard.mask.brushSize} {maskRadius}px
        </Typography>
        <Slider size="small" min={1} max={30} value={maskRadius} onChange={(_e, v) => typeof v === 'number' && setMaskRadius(v)} />
      </Box>
      <Button
        size="small"
        startIcon={<UndoIcon />}
        disabled={undoCount === 0}
        onClick={isInk ? undoInk : undoMask}
      >
        {de.wizard.mask.undo} ({undoCount})
      </Button>

      <Divider />

      <Box>
        <Typography variant="caption">
          {de.wizard.mask.fillHoles} {fill === 0 ? de.wizard.mask.fillHolesOff : `${fill} px²`}
        </Typography>
        <Slider
          size="small"
          min={0}
          max={FILL_MAX}
          step={2}
          value={fill}
          onChange={(_e, v) => typeof v === 'number' && setFill(v)}
          onChangeCommitted={(_e, v) => typeof v === 'number' && setFillHoles(v)}
        />
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
          {de.wizard.mask.fillHolesHint}
        </Typography>
      </Box>

      <FormControlLabel
        sx={{ mt: 0.5 }}
        control={<Switch size="small" checked={showMask} onChange={(e) => setShowMask(e.target.checked)} />}
        label={<Typography variant="body2">{de.wizard.mask.showMask}</Typography>}
      />
      {showMask ? (
        <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', pl: 0.5 }}>
          <LegendDot color="#000" label={de.wizard.mask.legendInk} />
          <LegendDot color={AUTO_FILL_COLOR} label={de.wizard.mask.legendAuto} />
          <LegendDot color="#fff" border label={de.wizard.mask.legendGap} />
        </Box>
      ) : (
        <Typography variant="caption" color="text.secondary" sx={{ pl: 0.5 }}>
          {de.wizard.mask.showMaskHint}
        </Typography>
      )}
    </Stack>
  );
}

function LegendDot({ color, label, border }: { color: string; label: string; border?: boolean }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
      <Box sx={{ width: 12, height: 12, bgcolor: color, borderRadius: 0.5, border: border ? '1px solid #999' : 'none' }} />
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
    </Box>
  );
}
