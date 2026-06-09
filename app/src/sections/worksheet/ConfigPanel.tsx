import DownloadIcon from '@mui/icons-material/Download';
import {
  Box,
  Button,
  Divider,
  FormControlLabel,
  InputAdornment,
  Paper,
  Stack,
  Switch,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';

import { PRESETS, type LineatureConfig } from '@/lib/lineatur';
import { tokens } from '@/theme';

function NumField(props: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
  disabled?: boolean;
}) {
  const { label, value, onChange, min, max, step, unit, disabled } = props;
  return (
    <TextField
      label={label}
      type="number"
      size="small"
      fullWidth
      disabled={disabled}
      // Store NaN for an empty/partial entry so the field can actually be
      // cleared while editing (rendered as '' above); buildLineature treats a
      // non-finite config as "blank preview" rather than snapping the value back.
      value={Number.isFinite(value) ? value : ''}
      onChange={(e) => onChange(parseFloat(e.target.value))}
      slotProps={{
        htmlInput: { min, max, step },
        input: unit
          ? { endAdornment: <InputAdornment position="end">{unit}</InputAdornment> }
          : undefined,
      }}
    />
  );
}

interface ConfigPanelProps {
  cfg: LineatureConfig;
  set: (patch: Partial<LineatureConfig>) => void;
  presetId: string;
  applyPreset: (id: string) => void;
  caption: string;
  setCaption: (s: string) => void;
  onDownload: () => void;
}

export function ConfigPanel({ cfg, set, presetId, applyPreset, caption, setCaption, onDownload }: ConfigPanelProps) {
  return (
    <Paper variant="outlined" sx={{ p: 2.5, bgcolor: tokens.surface.elevated }}>
      <Stack spacing={3}>
        <Box>
          <Typography variant="overline" sx={{ color: 'text.secondary', display: 'block', mb: 1 }}>
            Start-Schrift
          </Typography>
          <ToggleButtonGroup
            exclusive
            fullWidth
            size="small"
            value={presetId || null}
            onChange={(_, v) => v && applyPreset(v)}
          >
            {PRESETS.map((p) => (
              <ToggleButton key={p.id} value={p.id} sx={{ textTransform: 'none' }}>
                {p.label}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
          <Typography variant="caption" sx={{ color: 'text.disabled', display: 'block', mt: 1, minHeight: '1.2em' }}>
            {PRESETS.find((p) => p.id === presetId)?.note ?? 'Eigene Einstellung'}
          </Typography>
        </Box>

        <Divider />

        <Box>
          <Typography variant="overline" sx={{ color: 'text.secondary', display: 'block', mb: 1.5 }}>
            Verhältnis · Ober : Mittel : Unter
          </Typography>
          <Stack direction="row" spacing={1}>
            <NumField label="Ober" value={cfg.ratioAscender} onChange={(v) => set({ ratioAscender: v })} min={0} step={0.5} />
            <NumField label="Mittel" value={cfg.ratioXHeight} onChange={(v) => set({ ratioXHeight: v })} min={0.1} step={0.5} />
            <NumField label="Unter" value={cfg.ratioDescender} onChange={(v) => set({ ratioDescender: v })} min={0} step={0.5} />
          </Stack>
        </Box>

        <Stack spacing={2}>
          <NumField label="Mittelband (x-Höhe)" value={cfg.xHeightMm} onChange={(v) => set({ xHeightMm: v })} min={1} max={40} step={0.5} unit="mm" />
          <NumField label="Zeilenabstand" value={cfg.rowGapMm} onChange={(v) => set({ rowGapMm: v })} min={0} max={60} step={0.5} unit="mm" />
          <NumField label="Seitenrand" value={cfg.marginMm} onChange={(v) => set({ marginMm: v })} min={5} max={40} step={1} unit="mm" />
        </Stack>

        <Divider />

        <Box>
          <FormControlLabel
            control={
              <Switch
                checked={cfg.showSlant}
                onChange={(e) => set({ showSlant: e.target.checked })}
              />
            }
            label="Schräglinien (Neigung)"
          />
          <Stack spacing={2} sx={{ mt: 1 }}>
            <NumField label="Neigungswinkel" value={cfg.slantDeg} onChange={(v) => set({ slantDeg: v })} min={0} max={60} step={1} unit="°" disabled={!cfg.showSlant} />
            <NumField label="Abstand der Schräglinien" value={cfg.slantSpacingMm} onChange={(v) => set({ slantSpacingMm: v })} min={2} max={60} step={1} unit="mm" disabled={!cfg.showSlant} />
          </Stack>
        </Box>

        <Divider />

        <Box>
          <FormControlLabel
            control={
              <Switch
                checked={cfg.showPenAngle}
                onChange={(e) => set({ showPenAngle: e.target.checked })}
              />
            }
            label="Federwinkel (Stifthaltung)"
          />
          <Box sx={{ mt: 1 }}>
            <NumField label="Federwinkel" value={cfg.penAngleDeg} onChange={(v) => set({ penAngleDeg: v })} min={0} max={90} step={1} unit="°" disabled={!cfg.showPenAngle} />
          </Box>
          <Typography variant="caption" sx={{ color: 'text.disabled', display: 'block', mt: 1 }}>
            Anstellwinkel der Feder zur Schreiblinie — als Winkelmarke oben links. Bei der Spitzfeder (Kurrent) kommt die Strichstärke aus dem Druck, nicht aus dem Winkel.
          </Typography>
        </Box>

        <Divider />

        <TextField
          label="Titel / Name (optional)"
          size="small"
          fullWidth
          value={caption}
          onChange={(e) => setCaption(e.target.value)}
          placeholder="z. B. Kurrent"
          helperText="Erscheint mit Verhältnis/Neigung/Feder unten links; kurrentschrift.ink steht unten rechts."
        />

        <Button variant="contained" size="large" startIcon={<DownloadIcon />} onClick={onDownload}>
          Als PDF herunterladen
        </Button>
      </Stack>
    </Paper>
  );
}
