// Public worksheet generator (/schreiben): a configurable set of ruled guide
// lines (German: Hilfslinien) for practising German cursive, rendered live as
// A4 and downloadable as a print-ready PDF. Geometry lives in lib/lineatur.ts,
// the PDF in lib/pdf.ts; this file is the UI shell only.
//
// Scope per vision.md §2 / architektur.md §15: ratio ascender:x-height:descender
// freely configurable with the three start-script presets (Kurrent · Sütterlin ·
// Offenbacher), plus optional slant guides — and, since 2026-08-30, the
// content-aware part: an Übungstext set into the rows as a Vorschrift, composed
// server-side like the Federprobe (useWorksheetText.ts) and placed by
// lib/uebungstext.ts, drawn alike in the preview and the PDF.

import { useMemo, useState } from 'react';
import { Box, Paper, Typography } from '@mui/material';

import { PageContainer } from '@/components/PageContainer';
import { PageHeader } from '@/components/PageHeader';
import { PublicLayout } from '@/layouts/public/PublicLayout';
import { A4, PRESETS, RULING_THEMES, buildLineature, type LineatureConfig } from '@/lib/lineatur';
import { lineaturePdf } from '@/lib/pdf';
import { maxCharsPerLine, placeText } from '@/lib/uebungstext';
import { de, fmt } from '@/locales';
import { ConfigPanel } from '@/sections/worksheet/ConfigPanel';
import { PreviewSvg } from '@/sections/worksheet/PreviewSvg';
import { scriptMismatchNote, sheetNoteOf, textStatusOf, WRITTEN_SCRIPT } from '@/sections/worksheet/status';
import { useWorksheetText } from '@/sections/worksheet/useWorksheetText';
import { tokens } from '@/theme';

const ratioLabel = (c: LineatureConfig) =>
  `${c.ratioAscender} : ${c.ratioXHeight} : ${c.ratioDescender}`;

const SITE_URL = 'kurrentschrift.ink';

// The left footer string: the free-text caption (title/name) plus the live
// spec (ratio + slant + pen angle), so a printed sheet carries its settings.
// The site URL is placed in the opposite corner (see render below).
// `mixedScript` adds the one thing the sheet could otherwise not tell about
// itself: that the Vorschrift is written in another script than the ruling is
// labelled with — a sheet on the table has no popover to open.
function buildSpec(cfg: LineatureConfig, caption: string, mixedScript: boolean): string {
  const parts: string[] = [];
  const c = caption.trim();
  if (c) parts.push(c);
  if ([cfg.ratioAscender, cfg.ratioXHeight, cfg.ratioDescender].every(Number.isFinite)) {
    parts.push(ratioLabel(cfg));
  }
  if (cfg.showSlant && Number.isFinite(cfg.slantDeg)) parts.push(fmt(de.worksheet.spec.slant, { deg: cfg.slantDeg }));
  if (cfg.showPenAngle && Number.isFinite(cfg.penAngleDeg)) parts.push(fmt(de.worksheet.spec.pen, { deg: cfg.penAngleDeg }));
  if (mixedScript) parts.push(de.worksheet.spec.vorschrift);
  return parts.join('  ·  ');
}

function stripPreset(p: (typeof PRESETS)[number]): LineatureConfig {
  // Drop the preset-only metadata, keep just the config knobs.
  const { id: _id, label: _label, note: _note, ...cfg } = p;
  void _id;
  void _label;
  void _note;
  return cfg;
}

// Sütterlin is the active authoring script (CONFIG.sourceId), so the worksheet
// opens on its preset; Kurrent/Offenbacher stay one click away.
const DEFAULT_PRESET = PRESETS.find((p) => p.id === WRITTEN_SCRIPT) ?? PRESETS[0];

export function WorksheetView() {
  const [cfg, setCfg] = useState<LineatureConfig>(() => stripPreset(DEFAULT_PRESET));
  const [presetId, setPresetId] = useState<string>(DEFAULT_PRESET.id);
  const [caption, setCaption] = useState<string>(DEFAULT_PRESET.label);
  // The Übungstext: model lines set into the rows, each followed by a grey
  // copy to trace over and by empty rows to write it freely.
  const [text, setText] = useState<string>('');
  const [trace, setTrace] = useState<boolean>(true);
  const [practiceRows, setPracticeRows] = useState<number>(2);
  // Ruling colour scheme: today's print look vs the ~1900 Schulheft print
  // (blue lines, optional red Randleiste). Preview and PDF read the same map.
  const [rulingThemeId, setRulingThemeIdRaw] = useState<string>(RULING_THEMES[0].id);
  // Leaving the Schulheft theme also clears the Randleiste — its toggle only
  // renders there, so a stuck-on margin line would otherwise be uncontrollable.
  const setRulingThemeId = (id: string) => {
    setRulingThemeIdRaw(id);
    if (id !== 'schulheft') setCfg((c) => ({ ...c, showMarginLine: false }));
  };
  const rulingStyles = (RULING_THEMES.find((t) => t.id === rulingThemeId) ?? RULING_THEMES[0]).styles;

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

  const { segments, marks, rows } = useMemo(() => buildLineature(cfg), [cfg]);
  const written = useWorksheetText(text);
  const placed = useMemo(
    () =>
      placeText(written.lines, rows, {
        xHeightMm: cfg.xHeightMm,
        trace,
        practiceRows,
        left: cfg.marginMm,
        right: A4.widthMm - cfg.marginMm,
      }),
    [written.lines, rows, cfg.xHeightMm, cfg.marginMm, trace, practiceRows],
  );
  const textStatus = useMemo(() => textStatusOf(written, placed, cfg.xHeightMm), [written, placed, cfg.xHeightMm]);
  const scriptMismatch = scriptMismatchNote(presetId, text);
  const sheetNote = sheetNoteOf(cfg, rows.length);
  const spec = buildSpec(cfg, caption, scriptMismatch !== null && placed.placed.length > 0);
  const maxChars = maxCharsPerLine(cfg.xHeightMm, cfg.marginMm, A4.widthMm - cfg.marginMm);

  const download = () => {
    const blob = lineaturePdf(segments, {
      footerLeft: spec,
      footerRight: SITE_URL,
      marks,
      styles: rulingStyles,
      shapes: placed.shapes,
    });
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
    <PublicLayout footer>
      <PageContainer width="wide" sx={{ pt: { xs: 4, md: 6 } }}>
        <PageHeader eyebrow={de.common.nav.write} title={de.worksheet.title}>
          <Typography variant="body1" sx={{ color: 'text.secondary', lineHeight: 1.7 }}>
            {de.worksheet.intro}
          </Typography>
        </PageHeader>

        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', md: '340px 1fr' },
            gap: { xs: 3, md: 4 },
            alignItems: 'start',
          }}
        >
          {/* Controls */}
          <ConfigPanel
            cfg={cfg}
            set={set}
            presetId={presetId}
            applyPreset={applyPreset}
            caption={caption}
            setCaption={setCaption}
            onDownload={download}
            rulingThemeId={rulingThemeId}
            setRulingThemeId={setRulingThemeId}
            text={text}
            setText={setText}
            trace={trace}
            setTrace={setTrace}
            practiceRows={practiceRows}
            setPracticeRows={setPracticeRows}
            textStatus={textStatus}
            busy={written.loading}
            maxChars={maxChars}
            scriptMismatch={scriptMismatch}
            sheetNote={sheetNote}
          />

          {/* Preview */}
          <Box>
            <Typography variant="overline" sx={{ color: 'text.secondary', display: 'block', mb: 1 }}>
              {de.worksheet.preview}
            </Typography>
            {/* A blank sheet says why it is blank — it used to look like a
                finished page and downloaded as one (audit 2026-09-02). */}
            {sheetNote && (
              <Typography
                role="status"
                variant="body2"
                sx={{ color: 'error.main', mb: 1.5, maxWidth: '44rem' }}
              >
                {sheetNote}
              </Typography>
            )}
            <Paper
              variant="outlined"
              sx={{
                p: { xs: 1.5, sm: 3 },
                bgcolor: tokens.ink.rule,
                display: 'flex',
                justifyContent: 'center',
              }}
            >
              <PreviewSvg
                segments={segments}
                marks={marks}
                footerLeft={spec}
                footerRight={SITE_URL}
                styles={rulingStyles}
                shapes={placed.shapes}
                rowMarks={placed.marks}
              />
            </Paper>
          </Box>
        </Box>
      </PageContainer>
    </PublicLayout>
  );
}
