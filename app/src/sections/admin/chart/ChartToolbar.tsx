// Toolbar row of the chart editor: mode toggle (Schwenken/Bbox/Verschieben),
// the lock toggle, the zoom −/slider/+ group, the active-glyph chip and the
// delete/Einrichten/Diagnose actions.
// Pure props — all state is derived in ChartView and passed in.

import AddBoxIcon from '@mui/icons-material/AddBox';
import AddIcon from '@mui/icons-material/Add';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import ControlCameraIcon from '@mui/icons-material/ControlCamera';
import DeleteIcon from '@mui/icons-material/Delete';
import LockIcon from '@mui/icons-material/Lock';
import LockOpenIcon from '@mui/icons-material/LockOpen';
import OpenWithIcon from '@mui/icons-material/OpenWith';
import RemoveIcon from '@mui/icons-material/Remove';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import VisibilityIcon from '@mui/icons-material/Visibility';
import {
  Box,
  Button,
  Chip,
  IconButton,
  Paper,
  Slider,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material';

import { de, fmt } from '@/locales/admin';
import { ZOOM_MAX, ZOOM_MIN, ZOOM_PRESETS } from './chartConstants';
import type { Mode } from './chartConstants';

interface ChartToolbarProps {
  mode: Mode;
  onModeChange: (mode: Mode) => void;
  activeGlyph: string | null;
  activeLocked: boolean;
  // Whether the active glyph has a bbox (lock/delete/Einrichten gate).
  hasActiveBbox: boolean;
  activeHasCanonical: boolean;
  zoom: number;
  onZoomChange: (zoom: number) => void;
  onZoomOut: () => void;
  onZoomIn: () => void;
  onToggleLock: () => void;
  onDelete: () => void;
  onOpenWizard: () => void;
  onOpenDiagnose: () => void;
  onOpenRederiveAll: () => void;
}

export function ChartToolbar({
  mode,
  onModeChange,
  activeGlyph,
  activeLocked,
  hasActiveBbox,
  activeHasCanonical,
  zoom,
  onZoomChange,
  onZoomOut,
  onZoomIn,
  onToggleLock,
  onDelete,
  onOpenWizard,
  onOpenDiagnose,
  onOpenRederiveAll,
}: ChartToolbarProps) {
  return (
    <Paper square sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 1, borderBottom: 1, borderColor: 'divider', flexWrap: 'wrap' }}>
      <ToggleButtonGroup size="small" value={mode} exclusive onChange={(_e, v: Mode | null) => v && onModeChange(v)}>
        <ToggleButton value="pan">
          <OpenWithIcon fontSize="small" />
          &nbsp;{de.admin.toolbar.pan}
        </ToggleButton>
        <ToggleButton value="bbox">
          <AddBoxIcon fontSize="small" />
          &nbsp;{de.admin.toolbar.bbox}
        </ToggleButton>
        <ToggleButton value="edit">
          <ControlCameraIcon fontSize="small" />
          &nbsp;{de.admin.toolbar.edit}
        </ToggleButton>
      </ToggleButtonGroup>

      <Tooltip
        title={
          !hasActiveBbox
            ? de.admin.toolbar.lockNeedsBbox
            : activeLocked
              ? de.admin.toolbar.unlock
              : de.admin.toolbar.lock
        }
      >
        <span>
          <ToggleButton
            size="small"
            value="lock"
            selected={activeLocked}
            color="success"
            disabled={!hasActiveBbox}
            aria-label={activeLocked ? de.admin.toolbar.unlockAria : de.admin.toolbar.lockAria}
            onChange={onToggleLock}
          >
            {activeLocked ? <LockIcon fontSize="small" /> : <LockOpenIcon fontSize="small" />}
          </ToggleButton>
        </span>
      </Tooltip>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: { xs: 0, sm: 300 }, flex: { xs: 1, sm: 'none' } }}>
        <IconButton size="small" onClick={onZoomOut}>
          <RemoveIcon />
        </IconButton>
        <Slider
          size="small"
          sx={{ width: { xs: 'auto', sm: 160 }, flex: { xs: 1, sm: 'none' } }}
          value={zoom}
          min={ZOOM_MIN}
          max={ZOOM_MAX}
          step={0.05}
          marks={ZOOM_PRESETS.map((p) => ({ value: p }))}
          onChange={(_e, v) => typeof v === 'number' && onZoomChange(v)}
        />
        <IconButton size="small" onClick={onZoomIn}>
          <AddIcon />
        </IconButton>
        <Typography variant="caption" sx={{ minWidth: 50 }}>
          {Math.round(zoom * 100)}%
        </Typography>
      </Box>

      <Box sx={{ flex: 1 }} />

      {activeGlyph ? <Chip label={`${de.admin.toolbar.activeGlyph} ${activeGlyph}`} color="primary" size="small" /> : <Chip label={de.admin.toolbar.noActiveGlyph} size="small" variant="outlined" />}
      <Tooltip title={de.admin.toolbar.deleteBbox}>
        <span>
          <IconButton
            size="small"
            color="error"
            aria-label={de.admin.toolbar.deleteBbox}
            disabled={activeLocked || !activeGlyph || !hasActiveBbox}
            onClick={onDelete}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </span>
      </Tooltip>
      <Tooltip title={activeLocked ? fmt(de.admin.toolbar.lockedFirstUnlock, { glyph: activeGlyph ?? '' }) : de.admin.toolbar.openWizard}>
        <span>
          <Button
            size="small"
            variant="contained"
            startIcon={<AutoFixHighIcon />}
            disabled={activeLocked || !activeGlyph || !hasActiveBbox}
            onClick={onOpenWizard}
          >
            {de.admin.toolbar.setup}
          </Button>
        </span>
      </Tooltip>
      <Tooltip title={activeHasCanonical ? de.admin.toolbar.diagnoseTooltip : de.admin.toolbar.diagnoseNeedsCanonical}>
        <span>
          <Button
            size="small"
            variant="outlined"
            startIcon={<VisibilityIcon />}
            disabled={!activeGlyph || !activeHasCanonical}
            onClick={onOpenDiagnose}
          >
            {de.admin.toolbar.diagnose}
          </Button>
        </span>
      </Tooltip>
      <Tooltip title={de.admin.rederive.buttonTooltip}>
        <Button size="small" variant="outlined" startIcon={<RestartAltIcon />} onClick={onOpenRederiveAll}>
          {de.admin.rederive.button}
        </Button>
      </Tooltip>
    </Paper>
  );
}
