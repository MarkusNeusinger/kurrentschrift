// Step 1 "Ausschluss & Tinte" — assemble the crop the skeleton will see. Three
// pointer modes sharing the canvas: the eraser (Radierer) blanks neighbour ink,
// the ink brush (Tinte) fills white specks, and "Zelle einsetzen" copies ink
// from another cell of the same chart into this crop (e.g. the ä umlaut over a
// u/o for ü/ö). Plus the per-glyph "Lücken füllen" auto-fill threshold. Brushes
// commit to bbox.mask_strokes / bbox.ink_strokes; inserted cells to bbox.patches.

import DeleteOutlineIcon from '@mui/icons-material/DeleteOutlined';
import PhotoSizeSelectLargeIcon from '@mui/icons-material/PhotoSizeSelectLarge';
import UndoIcon from '@mui/icons-material/Undo';
import {
  Box,
  Button,
  Divider,
  FormControlLabel,
  IconButton,
  Slider,
  Stack,
  Switch,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { useEffect, useState } from 'react';

import { InfoHint } from '@/components/InfoHint';
import { de } from '@/locales';
import type { BboxOut } from '@/lib/api';
import { DonorPicker } from '../DonorPicker';
import { HintHeading } from './HintHeading';

const AUTO_FILL_COLOR = '#1fa85a'; // matches crop_mask_to_png_bytes' green

const FILL_MAX = 160; // px²: above this the slider risks eating real counters

type Tool = 'eraser' | 'ink' | 'patch';

export function MaskStep({
  bbox,
  sourceId,
  chartW,
  chartH,
  maskRadius,
  setMaskRadius,
  tool,
  setTool,
  showMask,
  setShowMask,
  undoMask,
  undoInk,
  setFillHoles,
  addPatch,
  removePatch,
}: {
  bbox: BboxOut;
  sourceId: string;
  chartW: number;
  chartH: number;
  maskRadius: number;
  setMaskRadius: (r: number) => void;
  tool: Tool;
  setTool: (t: Tool) => void;
  showMask: boolean;
  setShowMask: (v: boolean) => void;
  undoMask: () => Promise<void>;
  undoInk: () => Promise<void>;
  setFillHoles: (v: number) => void | Promise<void>;
  addPatch: (src: [number, number, number, number]) => void | Promise<void>;
  removePatch: (index: number) => void | Promise<void>;
}) {
  // Live slider value, synced from the stored bbox; committed (PUT) only on
  // release so dragging doesn't spam the server.
  const [fill, setFill] = useState(bbox.fill_holes_max_area);
  useEffect(() => setFill(bbox.fill_holes_max_area), [bbox.fill_holes_max_area]);
  const [pickerOpen, setPickerOpen] = useState(false);

  const isInk = tool === 'ink';
  const isPatch = tool === 'patch';
  const undoCount = isInk ? bbox.ink_strokes.length : bbox.mask_strokes.length;
  const lead = isPatch ? de.wizard.mask.leadPatch : isInk ? de.wizard.mask.leadInk : de.wizard.mask.leadEraser;

  return (
    <Stack spacing={1.5}>
      <HintHeading title={de.wizard.mask.title}>
        <Typography variant="body2" gutterBottom>
          {de.wizard.mask.body1}
        </Typography>
        <Typography variant="body2" gutterBottom>
          {de.wizard.mask.body2}
        </Typography>
        <Typography variant="body2" gutterBottom>
          {de.wizard.mask.inkBody}
        </Typography>
        <Typography variant="body2">{de.wizard.mask.patchBody}</Typography>
      </HintHeading>

      <ToggleButtonGroup size="small" exclusive value={tool} onChange={(_e, v: Tool | null) => v && setTool(v)} fullWidth>
        <ToggleButton value="eraser">{de.wizard.mask.toolEraser}</ToggleButton>
        <ToggleButton value="ink">{de.wizard.mask.toolInk}</ToggleButton>
        <ToggleButton value="patch">{de.wizard.mask.toolPatch}</ToggleButton>
      </ToggleButtonGroup>

      <Typography variant="body2" color="text.secondary">
        {lead}
      </Typography>

      {isPatch ? (
        <>
          <Button size="small" variant="outlined" startIcon={<PhotoSizeSelectLargeIcon />} onClick={() => setPickerOpen(true)}>
            {de.wizard.mask.patchPick}
          </Button>
          <Box>
            <Typography variant="caption" color="text.secondary">
              {de.wizard.mask.patchListTitle}
            </Typography>
            {bbox.patches.length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                {de.wizard.mask.patchEmpty}
              </Typography>
            ) : (
              <Stack spacing={0.5} sx={{ mt: 0.5 }}>
                {bbox.patches.map((_p, i) => (
                  <Box key={i} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="body2">
                      {de.wizard.mask.patchItem} {i + 1}
                    </Typography>
                    <IconButton size="small" aria-label={de.wizard.mask.patchRemove} onClick={() => void removePatch(i)}>
                      <DeleteOutlineIcon fontSize="small" />
                    </IconButton>
                  </Box>
                ))}
              </Stack>
            )}
          </Box>
          {bbox.patches.length > 0 && (
            <Typography variant="caption" color="text.secondary">
              {de.wizard.mask.patchDragHint}
            </Typography>
          )}
        </>
      ) : (
        <>
          <Box>
            <Typography variant="caption">
              {de.wizard.mask.brushSize} {maskRadius}px
            </Typography>
            <Slider size="small" min={1} max={30} value={maskRadius} onChange={(_e, v) => typeof v === 'number' && setMaskRadius(v)} />
          </Box>
          <Button size="small" startIcon={<UndoIcon />} disabled={undoCount === 0} onClick={isInk ? undoInk : undoMask}>
            {de.wizard.mask.undo} ({undoCount})
          </Button>
        </>
      )}

      <Divider />

      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Typography variant="caption">
            {de.wizard.mask.fillHoles} {fill === 0 ? de.wizard.mask.fillHolesOff : `${fill} px²`}
          </Typography>
          <InfoHint title={de.wizard.mask.fillHoles}>{de.wizard.mask.fillHolesHint}</InfoHint>
        </Box>
        <Slider
          size="small"
          min={0}
          max={FILL_MAX}
          step={2}
          value={fill}
          onChange={(_e, v) => typeof v === 'number' && setFill(v)}
          onChangeCommitted={(_e, v) => typeof v === 'number' && setFillHoles(v)}
        />
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        <FormControlLabel
          control={<Switch size="small" checked={showMask} onChange={(e) => setShowMask(e.target.checked)} />}
          label={<Typography variant="body2">{de.wizard.mask.showMask}</Typography>}
        />
        <InfoHint title={de.wizard.mask.showMask}>{de.wizard.mask.showMaskHint}</InfoHint>
      </Box>
      {showMask && (
        <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', pl: 0.5 }}>
          <LegendDot color="#000" label={de.wizard.mask.legendInk} />
          <LegendDot color={AUTO_FILL_COLOR} label={de.wizard.mask.legendAuto} />
          <LegendDot color="#fff" border label={de.wizard.mask.legendGap} />
        </Box>
      )}

      <DonorPicker
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        onConfirm={(src) => void addPatch(src)}
        sourceId={sourceId}
        chartW={chartW}
        chartH={chartH}
      />
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
