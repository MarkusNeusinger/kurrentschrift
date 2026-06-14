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

import { InfoHint } from '@/components/InfoHint';
import { PRESETS, type LineatureConfig } from '@/lib/lineatur';
import { de } from '@/locales';
import { tokens } from '@/theme';

// Overline section label with an optional (i) affordance to its right — the
// detail that used to sit as a sentence under the control now lives behind the
// icon, keeping the panel minimal (style-guide §7).
function SectionLabel({ children, info }: { children: React.ReactNode; info?: React.ReactNode }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25, mb: 1 }}>
      <Typography variant="overline" sx={{ color: 'text.secondary' }}>
        {children}
      </Typography>
      {info}
    </Box>
  );
}

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
  rulingThemeId: string;
  setRulingThemeId: (id: string) => void;
}

export function ConfigPanel({ cfg, set, presetId, applyPreset, caption, setCaption, onDownload, rulingThemeId, setRulingThemeId }: ConfigPanelProps) {
  const isSchulheft = rulingThemeId === 'schulheft';
  return (
    <Paper variant="outlined" sx={{ p: 2.5, bgcolor: tokens.surface.elevated }}>
      <Stack spacing={3}>
        <Box>
          <Typography variant="overline" sx={{ color: 'text.secondary', display: 'block', mb: 1 }}>
            {de.worksheet.config.presetHeading}
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
          <Typography variant="body2" sx={{ color: 'text.disabled', display: 'block', mt: 1, minHeight: '1.2em' }}>
            {PRESETS.find((p) => p.id === presetId)?.note ?? de.worksheet.config.customSetting}
          </Typography>
        </Box>

        <Divider />

        <Box>
          <Typography variant="overline" sx={{ color: 'text.secondary', display: 'block', mb: 1.5 }}>
            {de.worksheet.config.ratioHeading}
          </Typography>
          <Stack direction="row" spacing={1}>
            <NumField label={de.worksheet.config.ratioAscender} value={cfg.ratioAscender} onChange={(v) => set({ ratioAscender: v })} min={0} step={0.5} />
            <NumField label={de.worksheet.config.ratioXHeight} value={cfg.ratioXHeight} onChange={(v) => set({ ratioXHeight: v })} min={0.1} step={0.5} />
            <NumField label={de.worksheet.config.ratioDescender} value={cfg.ratioDescender} onChange={(v) => set({ ratioDescender: v })} min={0} step={0.5} />
          </Stack>
        </Box>

        <Box>
          <SectionLabel
            info={
              <InfoHint title={de.worksheet.config.lineSystemHeading}>
                {de.worksheet.config.lineSystemHint}
              </InfoHint>
            }
          >
            {de.worksheet.config.lineSystemHeading}
          </SectionLabel>
          <ToggleButtonGroup
            exclusive
            fullWidth
            size="small"
            value={cfg.lineSystem}
            onChange={(_, v) => v && set({ lineSystem: v })}
          >
            <ToggleButton value="four" sx={{ textTransform: 'none' }}>{de.worksheet.config.lineSystemFour}</ToggleButton>
            <ToggleButton value="two" sx={{ textTransform: 'none' }}>{de.worksheet.config.lineSystemTwo}</ToggleButton>
            <ToggleButton value="one" sx={{ textTransform: 'none' }}>{de.worksheet.config.lineSystemOne}</ToggleButton>
          </ToggleButtonGroup>
        </Box>

        <Stack spacing={2}>
          <NumField label={de.worksheet.config.xHeight} value={cfg.xHeightMm} onChange={(v) => set({ xHeightMm: v })} min={1} max={40} step={0.5} unit="mm" />
          <NumField label={de.worksheet.config.rowGap} value={cfg.rowGapMm} onChange={(v) => set({ rowGapMm: v })} min={0} max={60} step={0.5} unit="mm" />
          <NumField label={de.worksheet.config.margin} value={cfg.marginMm} onChange={(v) => set({ marginMm: v })} min={5} max={40} step={1} unit="mm" />
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
            label={de.worksheet.config.slantToggle}
          />
          <Stack spacing={2} sx={{ mt: 1 }}>
            <NumField label={de.worksheet.config.slantAngle} value={cfg.slantDeg} onChange={(v) => set({ slantDeg: v })} min={30} max={90} step={1} unit="°" disabled={!cfg.showSlant} />
            <NumField label={de.worksheet.config.slantSpacing} value={cfg.slantSpacingMm} onChange={(v) => set({ slantSpacingMm: v })} min={2} max={60} step={1} unit="mm" disabled={!cfg.showSlant} />
          </Stack>
        </Box>

        <Divider />

        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={cfg.showPenAngle}
                  onChange={(e) => set({ showPenAngle: e.target.checked })}
                />
              }
              label={de.worksheet.config.penAngleToggle}
            />
            <InfoHint title={de.worksheet.config.penAngle}>{de.worksheet.config.penAngleHint}</InfoHint>
          </Box>
          <Box sx={{ mt: 1 }}>
            <NumField label={de.worksheet.config.penAngle} value={cfg.penAngleDeg} onChange={(v) => set({ penAngleDeg: v })} min={0} max={90} step={1} unit="°" disabled={!cfg.showPenAngle} />
          </Box>
        </Box>

        <Divider />

        <Box>
          <SectionLabel
            info={
              <InfoHint title={de.worksheet.config.rulingHeading}>
                {de.worksheet.config.rulingNote}
              </InfoHint>
            }
          >
            {de.worksheet.config.rulingHeading}
          </SectionLabel>
          <ToggleButtonGroup
            exclusive
            fullWidth
            size="small"
            value={rulingThemeId}
            onChange={(_, v) => v && setRulingThemeId(v)}
          >
            <ToggleButton value="druck" sx={{ textTransform: 'none' }}>
              {de.worksheet.config.rulingDruck}
            </ToggleButton>
            <ToggleButton value="schulheft" sx={{ textTransform: 'none' }}>
              {de.worksheet.config.rulingSchulheft}
            </ToggleButton>
          </ToggleButtonGroup>
          {isSchulheft && (
            <FormControlLabel
              sx={{ mt: 1 }}
              control={
                <Switch
                  checked={cfg.showMarginLine}
                  onChange={(e) => set({ showMarginLine: e.target.checked })}
                />
              }
              label={de.worksheet.config.marginToggle}
            />
          )}
        </Box>

        <Divider />

        <TextField
          label={de.worksheet.config.captionLabel}
          size="small"
          fullWidth
          value={caption}
          onChange={(e) => setCaption(e.target.value)}
          placeholder={de.worksheet.config.captionPlaceholder}
          helperText={de.worksheet.config.captionHelp}
        />

        <Button variant="contained" size="large" startIcon={<DownloadIcon />} onClick={onDownload}>
          {de.worksheet.config.download}
        </Button>
      </Stack>
    </Paper>
  );
}
