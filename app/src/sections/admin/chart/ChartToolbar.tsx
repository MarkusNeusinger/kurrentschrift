// Toolbar row of the chart editor: mode toggle (Schwenken/Bbox/Verschieben),
// the lock toggle with its scope-aware tooltips, the zoom −/slider/+ group,
// the active-glyph chip and the delete/Einrichten/Diagnose actions.
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

import { ZOOM_MAX, ZOOM_MIN, ZOOM_PRESETS } from './chartConstants';
import type { Mode } from './chartConstants';

interface ChartToolbarProps {
  mode: Mode;
  onModeChange: (mode: Mode) => void;
  activeGlyph: string | null;
  // Lock scope (whole letter vs. single position) and its aggregate state, as
  // derived in ChartView from isLetterSplit/siblingKeys.
  activeSplit: boolean;
  activeLocked: boolean;
  // Whether any key in the lock scope has a bbox (the lock button's gate).
  hasLockableBbox: boolean;
  // Whether the active glyph itself has a bbox (delete/Einrichten gate).
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
}

export function ChartToolbar({
  mode,
  onModeChange,
  activeGlyph,
  activeSplit,
  activeLocked,
  hasLockableBbox,
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
}: ChartToolbarProps) {
  return (
    <Paper square sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 1, borderBottom: 1, borderColor: 'divider', flexWrap: 'wrap' }}>
      <ToggleButtonGroup size="small" value={mode} exclusive onChange={(_e, v: Mode | null) => v && onModeChange(v)}>
        <ToggleButton value="pan">
          <OpenWithIcon fontSize="small" />
          &nbsp;Schwenken
        </ToggleButton>
        <ToggleButton value="bbox">
          <AddBoxIcon fontSize="small" />
          &nbsp;Bbox
        </ToggleButton>
        <ToggleButton value="edit">
          <ControlCameraIcon fontSize="small" />
          &nbsp;Verschieben
        </ToggleButton>
      </ToggleButtonGroup>

      <Tooltip
        title={
          !hasLockableBbox
            ? 'Glyph mit Bbox wählen, um ihn als fertig zu sperren'
            : activeSplit
              ? activeLocked
                ? 'Entsperren (nur diese Position — aufgetrennt)'
                : 'Als fertig sperren (nur diese Position — aufgetrennt)'
              : activeLocked
                ? 'Entsperren (alle Positionen, wieder bearbeitbar)'
                : 'Als fertig sperren (alle Positionen, vor Änderungen schützen)'
        }
      >
        <span>
          <ToggleButton
            size="small"
            value="lock"
            selected={activeLocked}
            color="success"
            disabled={!hasLockableBbox}
            aria-label={activeLocked ? 'Glyph entsperren' : 'Glyph als fertig sperren'}
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

      {activeGlyph ? <Chip label={`aktiv: ${activeGlyph}`} color="primary" size="small" /> : <Chip label="kein aktiver Glyph" size="small" variant="outlined" />}
      <Tooltip title="Bbox des aktiven Glyphs löschen">
        <span>
          <IconButton
            size="small"
            color="error"
            aria-label="Bbox des aktiven Glyphs löschen"
            disabled={activeLocked || !activeGlyph || !hasActiveBbox}
            onClick={onDelete}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </span>
      </Tooltip>
      <Tooltip title={activeLocked ? `${activeGlyph} ist gesperrt — erst entsperren` : 'Einrichtungs-Wizard für den aktiven Glyph öffnen'}>
        <span>
          <Button
            size="small"
            variant="contained"
            startIcon={<AutoFixHighIcon />}
            disabled={activeLocked || !activeGlyph || !hasActiveBbox}
            onClick={onOpenWizard}
          >
            Einrichten
          </Button>
        </span>
      </Tooltip>
      <Tooltip title={activeHasCanonical ? 'Diagnose (Skelett · Canonical · Fit) groß ansehen' : 'Noch kein Canonical — erst im Wizard einen Weg zeichnen'}>
        <span>
          <Button
            size="small"
            variant="outlined"
            startIcon={<VisibilityIcon />}
            disabled={!activeGlyph || !activeHasCanonical}
            onClick={onOpenDiagnose}
          >
            Diagnose
          </Button>
        </span>
      </Tooltip>
    </Paper>
  );
}
