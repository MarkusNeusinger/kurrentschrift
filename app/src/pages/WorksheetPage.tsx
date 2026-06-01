// Public worksheet generator (/schreiben): a configurable set of ruled guide
// lines (German: Hilfslinien) for practising German cursive, rendered live as
// A4 and downloadable as a print-ready PDF. Geometry lives in lib/lineatur.ts,
// the PDF in lib/pdf.ts; this file is the UI shell only.
//
// Scope per vision.md §2 / architektur.md §15: ratio ascender:x-height:descender
// freely configurable with the three start-script presets (Kurrent · Sütterlin ·
// Offenbacher), plus optional slant guides. The content-aware variant that
// typesets Kurrent glyphs into the lines is the later WeasyPrint piece.

import { useEffect, useMemo, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import DownloadIcon from '@mui/icons-material/Download';
import {
  Box,
  Button,
  Container,
  Divider,
  FormControlLabel,
  InputAdornment,
  Link,
  Paper,
  Stack,
  Switch,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';

import {
  A4,
  DRAW_ORDER,
  PRESETS,
  ROLE_STYLES,
  buildLineature,
  type LineatureConfig,
  type Segment,
  type TextMark,
} from '../lib/lineatur';
import { lineaturePdf } from '../lib/pdf';
import { tokens } from '../theme';

const garamond = "'EB Garamond', Georgia, 'Times New Roman', serif";

const ratioLabel = (c: LineatureConfig) =>
  `${c.ratioAscender} : ${c.ratioXHeight} : ${c.ratioDescender}`;

// The printed footer line: the free-text caption (a title or name), then the
// live spec (ratio + slant angle) and the site domain, always appended so a
// printed sheet carries its settings and where it came from.
function buildFooter(cfg: LineatureConfig, caption: string): string {
  const parts: string[] = [];
  const c = caption.trim();
  if (c) parts.push(c);
  if ([cfg.ratioAscender, cfg.ratioXHeight, cfg.ratioDescender].every(Number.isFinite)) {
    parts.push(ratioLabel(cfg));
  }
  if (cfg.showSlant && Number.isFinite(cfg.slantDeg)) parts.push(`Neigung ${cfg.slantDeg}°`);
  if (cfg.showPenAngle && Number.isFinite(cfg.penAngleDeg)) parts.push(`Feder ${cfg.penAngleDeg}°`);
  parts.push('kurrentschrift.ink');
  return parts.join('  ·  ');
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

export function WorksheetPage() {
  const [cfg, setCfg] = useState<LineatureConfig>(() => stripPreset(PRESETS[0]));
  const [presetId, setPresetId] = useState<string>(PRESETS[0].id);
  const [caption, setCaption] = useState<string>(PRESETS[0].label);

  useEffect(() => {
    document.title = 'Lineatur-Vorlage · kurrentschrift';
  }, []);

  // Manual edits drop the preset highlight (the config no longer "is" a preset).
  const set = (patch: Partial<LineatureConfig>) => {
    setCfg((c) => ({ ...c, ...patch }));
    setPresetId('');
  };

  const applyPreset = (id: string) => {
    const p = PRESETS.find((x) => x.id === id);
    if (!p) return;
    setCfg(stripPreset(p));
    setPresetId(p.id);
    setCaption(p.label);
  };

  const { segments, marks } = useMemo(() => buildLineature(cfg), [cfg]);
  const footer = buildFooter(cfg, caption);

  const download = () => {
    const blob = lineaturePdf(segments, { caption: footer, marks });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `lineatur-${presetId || 'eigen'}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    // Defer revocation so it can't race the download start on slower devices.
    setTimeout(() => URL.revokeObjectURL(url), 0);
  };

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', py: { xs: 4, md: 6 } }}>
      <Container maxWidth="lg">
        {/* Header */}
        <Stack spacing={1.5} sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
            <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: tokens.green }} />
            <Link
              component={RouterLink}
              to="/"
              variant="overline"
              sx={{ color: 'text.secondary', textDecoration: 'none', lineHeight: 1 }}
            >
              kurrentschrift.ink
            </Link>
          </Box>
          <Typography
            component="h1"
            sx={{
              fontFamily: garamond,
              fontStyle: 'italic',
              fontWeight: 400,
              fontSize: { xs: '1.9rem', sm: '2.3rem' },
              lineHeight: 1.15,
              color: 'text.primary',
            }}
          >
            Lineatur-Vorlage zum Schreiben üben
          </Typography>
          <Typography variant="body1" sx={{ color: 'text.secondary', lineHeight: 1.7, maxWidth: 560 }}>
            Hilfslinien für deutsche Schreibschrift auf DIN&nbsp;A4. Wähle eine der drei
            Start-Schriften als Ausgangspunkt, passe das Verhältnis von Ober-, Mittel- und
            Unterband frei an, schalte bei Bedarf Schräglinien dazu — und lade das Blatt als
            PDF zum Ausdrucken.
          </Typography>
        </Stack>

        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', md: '340px 1fr' },
            gap: { xs: 3, md: 4 },
            alignItems: 'start',
          }}
        >
          {/* Controls */}
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
                helperText="Verhältnis, Neigung, Federwinkel und kurrentschrift.ink werden automatisch ergänzt."
              />

              <Button variant="contained" size="large" startIcon={<DownloadIcon />} onClick={download}>
                Als PDF herunterladen
              </Button>
            </Stack>
          </Paper>

          {/* Preview */}
          <Box>
            <Typography variant="overline" sx={{ color: 'text.secondary', display: 'block', mb: 1 }}>
              Vorschau · DIN A4
            </Typography>
            <Paper
              variant="outlined"
              sx={{
                p: { xs: 1.5, sm: 3 },
                bgcolor: tokens.ink.rule,
                display: 'flex',
                justifyContent: 'center',
              }}
            >
              <PreviewSvg segments={segments} marks={marks} footer={footer} />
            </Paper>
          </Box>
        </Box>
      </Container>
    </Box>
  );
}

function stripPreset(p: (typeof PRESETS)[number]): LineatureConfig {
  // Drop the preset-only metadata, keep just the config knobs.
  const { id: _id, label: _label, note: _note, ...cfg } = p;
  void _id;
  void _label;
  void _note;
  return cfg;
}

function PreviewSvg({
  segments,
  marks,
  footer,
}: {
  segments: Segment[];
  marks: TextMark[];
  footer: string;
}) {
  // Paint in the same role order the PDF uses, so crossings look identical in
  // preview and print (stable sort keeps per-row order within a role).
  const ordered = useMemo(
    () => [...segments].sort((a, b) => DRAW_ORDER.indexOf(a.role) - DRAW_ORDER.indexOf(b.role)),
    [segments],
  );
  const trimmed = footer.trim();
  return (
    <Box
      component="svg"
      viewBox={`0 0 ${A4.widthMm} ${A4.heightMm}`}
      sx={{
        width: '100%',
        maxWidth: 480,
        height: 'auto',
        display: 'block',
        bgcolor: '#FFFFFF',
        boxShadow: '0 1px 6px rgba(0,0,0,0.12)',
      }}
    >
      <rect x={0} y={0} width={A4.widthMm} height={A4.heightMm} fill="#FFFFFF" stroke="none" />
      {ordered.map((s, i) => {
        const st = ROLE_STYLES[s.role];
        return (
          <line
            key={i}
            x1={s.x1}
            y1={s.y1}
            x2={s.x2}
            y2={s.y2}
            stroke={st.color}
            strokeWidth={st.widthMm}
            strokeLinecap="round"
            strokeDasharray={st.dash ? `${st.dash[0]} ${st.dash[1]}` : undefined}
          />
        );
      })}
      {marks.map((m, i) => (
        <text
          key={`m${i}`}
          x={m.x}
          y={m.y}
          fontSize={m.sizeMm}
          fill={m.color ?? '#6B6A63'}
          fontFamily="sans-serif"
        >
          {m.text}
        </text>
      ))}
      {trimmed && (
        <text x={12} y={A4.heightMm - 9} fontSize={3.2} fill="#6B6A63" fontFamily="sans-serif">
          {trimmed}
        </text>
      )}
    </Box>
  );
}
