// Buchstaben — the first of the three views, and the one that carries a
// letter's WHOLE life in one column: the chart cell it was cut from, the ductus
// the author drew, how the engine writes it (chart form and derived Laufform),
// every occurrence the harvest found in the plates, what those occurrences
// condense to, and the two ways onward — to this letter's joins and to the
// words it appears in.
//
// Without a letter in the URL the view is the alphabet overview (every authored
// letter, chart crop vs. written); picking one focuses it. That is the same
// pattern in all three views: overview ⇄ detail, one subject at a time.

import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import {
  Alert,
  Box,
  Button,
  Chip,
  Collapse,
  IconButton,
  Tooltip,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { WrittenGlyph } from '@/components/WrittenGlyph';
import { useAdmin } from '@/context/AdminContext';
import { LETTER_BY_KEY } from '@/domain/glyphs';
import { cropUrl } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { ChartView } from '@/sections/admin/chart/ChartView';
import { GlyphComparison } from '@/sections/admin/compare/GlyphComparison';
import { LaufformApplyDialog } from '@/sections/admin/letters/LaufformApplyDialog';
import { LetterStats } from '@/sections/admin/shell/LensStats';
import { LetterPicker } from '@/sections/admin/shell/LetterPicker';
import { OccurrenceThumb } from '@/sections/admin/shell/OccurrenceThumb';
import { useFileMark } from '@/sections/admin/shell/KorbContext';
import { useWorkbench } from '@/sections/admin/shell/WorkbenchData';
import { joinsUrl, neighbourLetters, readLetterFocus, wordsUrl } from '@/sections/admin/shell/focus';
import { EvidenceState, Panel, ViewHeader } from '@/sections/admin/shell/Panel';
import { garamond } from '@/styles/paper';

// The Laufform is stored as this template variant (core/database LAUFFORM_VARIANT).
const LAUFFORM_VARIANT = 100;
const FACE_H = 190; // px per face in the "wie geschrieben" row

export function LetterView() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const { sourceId, bboxesByKey, glyphsByKey, cropCacheBust, refreshCrop, setActiveGlyph, openWizard, openDiagnose } =
    useAdmin();
  const workbench = useWorkbench();
  const fileMark = useFileMark();
  const t = de.admin.letters;

  const { glyphKey } = readLetterFocus(params);
  const [chartOpen, setChartOpen] = useState(false);
  const [applyOpen, setApplyOpen] = useState(false);
  // The Laufform face reports itself unavailable when the letter has no
  // variant-100 row — most letters do not, and that is information, not a gap.
  const [noLaufform, setNoLaufform] = useState(false);

  // Everything that acts on "the active glyph" — the wizard, the Diagnose
  // modal, the chart's bbox tools — reads it from the admin context. The URL is
  // the source of truth here, so it pushes into that context on every change.
  useEffect(() => {
    if (glyphKey) setActiveGlyph(glyphKey);
  }, [glyphKey, setActiveGlyph]);

  useEffect(() => {
    setNoLaufform(false);
  }, [glyphKey]);

  const focus = (key: string | null) => setParams(key ? { g: key } : {}, { replace: false });

  const occurrences = glyphKey ? (workbench.instancesByKey.get(glyphKey) ?? []) : [];
  const aggregate = glyphKey ? workbench.aggregatesByKey.get(glyphKey) : undefined;

  // The joins this letter takes part in, as the harvest actually saw them —
  // left of it and right of it, so the way into the Übergänge view starts from
  // evidence rather than from all 900 theoretical combinations.
  const relatedJoins = useMemo(() => {
    if (!glyphKey) return [];
    const seen = new Map<string, { leftKey: string; rightKey: string; count: number }>();
    for (const [key, rows] of workbench.pairsByKey) {
      const [leftKey, rightKey] = key.split('→');
      if (leftKey !== glyphKey && rightKey !== glyphKey) continue;
      seen.set(key, { leftKey, rightKey, count: rows.length });
    }
    return [...seen.values()].sort((a, b) => b.count - a.count);
  }, [glyphKey, workbench.pairsByKey]);

  // The words this letter was written in — one chip per specimen, so "how does
  // it look in running text?" is one click away.
  const relatedWords = useMemo(() => {
    const out = new Map<string, { specimenId: string; word: string }>();
    for (const inst of occurrences) {
      const id = inst.measurements.specimen_id;
      const sample = id ? workbench.sampleById.get(id) : undefined;
      if (id && sample) out.set(id, { specimenId: id, word: sample.word });
    }
    return [...out.values()];
  }, [occurrences, workbench.sampleById]);

  if (!glyphKey) {
    return (
      <Box sx={{ p: { xs: 2, md: 3 }, overflowY: 'auto' }}>
        <ViewHeader title={t.overviewTitle} intro={t.overviewIntro}>
          <LetterPicker onPick={focus}>
            {(open) => (
              <Button size="small" variant="outlined" onClick={open}>
                {t.pickLetter}
              </Button>
            )}
          </LetterPicker>
        </ViewHeader>
        {/* The comparison grid only knows AUTHORED letters — the picker above
            is the way to a letter that has no canonical yet. */}
        <GlyphComparison onPick={focus} />
      </Box>
    );
  }

  const letter = LETTER_BY_KEY[glyphKey];
  const hasBbox = glyphKey in bboxesByKey;
  const hasCanonical = glyphsByKey[glyphKey]?.has_data === true;
  const locked = bboxesByKey[glyphKey]?.locked === true;
  const { prev, next } = neighbourLetters(glyphKey);

  return (
    <Box sx={{ p: { xs: 2, md: 3 }, overflowY: 'auto' }}>
      <ViewHeader
        title={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            <IconButton size="small" disabled={!prev} aria-label={t.prevLetter} onClick={() => prev && focus(prev)}>
              <ChevronLeftIcon fontSize="small" />
            </IconButton>
            <LetterPicker activeKey={glyphKey} onPick={focus}>
              {(open) => (
                <Tooltip title={t.pickLetter}>
                  <Chip
                    clickable
                    onClick={open}
                    label={
                      <Typography component="span" sx={{ fontFamily: garamond, fontSize: 22, lineHeight: 1.4 }}>
                        {letter?.glyph ?? glyphKey}
                      </Typography>
                    }
                    sx={{ height: 40, px: 0.5 }}
                  />
                </Tooltip>
              )}
            </LetterPicker>
            <IconButton size="small" disabled={!next} aria-label={t.nextLetter} onClick={() => next && focus(next)}>
              <ChevronRightIcon fontSize="small" />
            </IconButton>
            <Typography variant="caption" color="text.secondary">
              {glyphKey}
              {letter?.note ? ` · ${letter.note}` : ''}
            </Typography>
          </Box>
        }
        chips={
          <>
            <Chip
              size="small"
              variant="outlined"
              color={hasCanonical ? 'success' : hasBbox ? 'warning' : 'default'}
              label={hasCanonical ? t.stateCanonical : hasBbox ? t.stateBbox : t.stateEmpty}
            />
            {locked && <Chip size="small" variant="outlined" label={t.stateLocked} />}
            <Chip size="small" variant="outlined" label={fmt(t.occurrenceCount, { count: occurrences.length })} />
          </>
        }
      >
        <Button size="small" onClick={() => focus(null)}>
          {t.toOverview}
        </Button>
        <Button size="small" variant="text" onClick={() => fileMark({ target: { kind: 'letter', glyphKey } })}>
          {`⚑ ${de.admin.werkbank.markLetter}`}
        </Button>
      </ViewHeader>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 2, alignItems: 'start' }}>
        {/* 1 — the chart cell and the tools that author it. */}
        <Panel title={t.tafelTitle} caption={t.tafelCaption}>
          {hasBbox ? (
            <Box sx={{ bgcolor: '#fff', border: 1, borderColor: 'divider', borderRadius: 1, p: 1, width: 'fit-content', maxWidth: '100%' }}>
              <img
                src={cropUrl(sourceId, glyphKey, cropCacheBust)}
                alt={fmt(de.admin.werkbank.chartFormAlt, { key: glyphKey })}
                height={FACE_H}
                style={{ display: 'block', maxWidth: '100%', objectFit: 'contain' }}
              />
            </Box>
          ) : (
            <Alert severity="info">{t.noBbox}</Alert>
          )}
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1.5 }}>
            <Button size="small" variant="contained" disabled={!hasBbox} onClick={() => openWizard(glyphKey)}>
              {de.admin.toolbar.setup}
            </Button>
            <Button size="small" variant="outlined" disabled={!hasCanonical} onClick={() => openDiagnose(glyphKey)}>
              {de.admin.toolbar.diagnose}
            </Button>
            <Button size="small" onClick={() => setChartOpen((v) => !v)} endIcon={chartOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}>
              {chartOpen ? t.hideChart : t.showChart}
            </Button>
          </Box>
        </Panel>

        {/* 2 — how the engine writes it: the authored chart ductus and the
            derived Laufform, side by side with the original ink above them. */}
        <Panel title={t.writtenTitle} caption={t.writtenCaption}>
          {!hasCanonical ? (
            <Alert severity="info">{t.noCanonical}</Alert>
          ) : (
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Face label={t.faceChart}>
                <WrittenGlyph
                  glyphKey={glyphKey}
                  sourceId={sourceId}
                  height={FACE_H}
                  cacheBust={cropCacheBust}
                  tight
                  animate={false}
                />
              </Face>
              <Face label={t.faceLaufform} hint={noLaufform ? t.noLaufform : undefined}>
                {!noLaufform && (
                  <WrittenGlyph
                    key={`laufform-${glyphKey}`}
                    glyphKey={glyphKey}
                    sourceId={sourceId}
                    variant={LAUFFORM_VARIANT}
                    height={FACE_H}
                    // An apply rewrites exactly this row, so the face has to
                    // refetch when the version stamp moves.
                    cacheBust={cropCacheBust}
                    tight
                    animate={false}
                    onUnavailable={() => setNoLaufform(true)}
                  />
                )}
              </Face>
            </Box>
          )}
        </Panel>

        {/* 3 — the raw evidence: every occurrence the harvest kept. */}
        <Panel title={fmt(t.occurrencesTitle, { count: occurrences.length })} caption={t.occurrencesCaption}>
          <EvidenceState
            loading={workbench.loading}
            error={workbench.error}
            empty={occurrences.length === 0}
            emptyText={de.admin.werkbank.noOccurrences}
          >
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {occurrences.map((inst) => {
                const sample = workbench.sampleById.get(inst.measurements.specimen_id ?? '');
                if (!sample) return null;
                return (
                  <OccurrenceThumb
                    key={`${inst.measurements.specimen_id}:${inst.measurements.slot}`}
                    inst={inst}
                    sample={sample}
                    sourceId={sourceId}
                    onJump={() => navigate(wordsUrl(sample.word, sample.id))}
                  />
                );
              })}
            </Box>
          </EvidenceState>
        </Panel>

        {/* 4 — what those occurrences condense to (Stufenplan H1). */}
        <Panel title={t.statsTitle} caption={t.statsCaption}>
          <LetterStats
            key={glyphKey}
            glyphKey={glyphKey}
            aggregate={aggregate}
            occurrences={occurrences}
            stats={workbench.letterStats}
            onRebuild={workbench.rebuildLetterStats}
          />
        </Panel>

        {/* 5 — the two ways onward. */}
        <Panel title={t.joinsTitle} caption={t.joinsCaption}>
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
            {relatedJoins.length === 0 ? (
              <Typography variant="caption" color="text.disabled">
                {t.noJoins}
              </Typography>
            ) : (
              relatedJoins.map((join) => (
                <Chip
                  key={`${join.leftKey}→${join.rightKey}`}
                  size="small"
                  variant="outlined"
                  clickable
                  label={`${join.leftKey}→${join.rightKey} · ${join.count}`}
                  onClick={() => navigate(joinsUrl(join.leftKey, join.rightKey))}
                />
              ))
            )}
          </Box>
          <Button size="small" variant="outlined" onClick={() => navigate(joinsUrl(glyphKey, null))}>
            {t.allJoins}
          </Button>
        </Panel>

        <Panel title={t.wordsTitle} caption={t.wordsCaption}>
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            {relatedWords.length === 0 ? (
              <Typography variant="caption" color="text.disabled">
                {t.noWords}
              </Typography>
            ) : (
              relatedWords.map((w) => (
                <Chip
                  key={w.specimenId}
                  size="small"
                  variant="outlined"
                  clickable
                  label={w.word}
                  onClick={() => navigate(wordsUrl(w.word, w.specimenId))}
                />
              ))
            )}
          </Box>
        </Panel>
      </Box>

      {/* Below everything, and deliberately outside the panel grid: the ONE
          step that changes what the engine writes (issue #270). The panels
          above inspect; this one promotes the statistics into rendering, so it
          is set apart, carries its warning in the block itself and asks for a
          confirmation that names what will change (optimierungs-werkbank.md
          §3 bars rendering handles from the inspection surfaces — it does not
          bar a surface that says out loud what it is). Hand-wide by nature:
          the endpoint applies a hand's aggregates wholesale. */}
      <Box
        sx={{
          mt: 3,
          p: 2,
          border: 1,
          borderStyle: 'dashed',
          borderColor: 'warning.main',
          borderRadius: 2,
          maxWidth: 760,
        }}
      >
        <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
          {t.applyBlockTitle}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1.5 }}>
          {t.applyBlockBody}
        </Typography>
        {workbench.handId ? (
          <Button size="small" variant="outlined" color="warning" onClick={() => setApplyOpen(true)}>
            {t.applyBlockButton}
          </Button>
        ) : (
          <Typography variant="caption" color="text.disabled">
            {t.applyBlockNoHand}
          </Typography>
        )}
      </Box>

      {applyOpen && workbench.handId && (
        <LaufformApplyDialog
          handId={workbench.handId}
          aggregates={workbench.allAggregates}
          onClose={() => setApplyOpen(false)}
          // The written rows are both statistics and rendering now: refetch the
          // aggregate layer (its freshness numbers just changed) and bust the
          // render cache so the Laufform face shows what was just written.
          onApplied={() => {
            workbench.refreshLetterStats();
            refreshCrop();
          }}
        />
      )}

      {/* The full chart, for drawing or moving THIS letter's cell. Collapsed by
          default: it is the one tool here that needs the whole plate, and it is
          only reached for when a crop has to be cut or corrected. */}
      <Collapse in={chartOpen} unmountOnExit>
        <Box sx={{ mt: 2, border: 1, borderColor: 'divider', borderRadius: 2, overflow: 'hidden' }}>
          <Box sx={{ height: { xs: '60vh', md: '70vh' }, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <ChartInPanel />
          </Box>
        </Box>
      </Collapse>
    </Box>
  );
}

// The chart needs the loaded source; the layout guarantees one, but the type
// does not — this keeps ChartView's `source` prop required.
function ChartInPanel() {
  const { source } = useAdmin();
  return source ? <ChartView source={source} /> : null;
}

function Face({ label, hint, children }: { label: string; hint?: string; children?: React.ReactNode }) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Box
        sx={{
          minHeight: FACE_H,
          minWidth: 96,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: '#fff',
          border: 1,
          borderColor: 'divider',
          borderRadius: 1,
          px: 1,
        }}
      >
        {hint ? (
          <Typography variant="caption" color="text.disabled" sx={{ p: 1, textAlign: 'center' }}>
            {hint}
          </Typography>
        ) : (
          children
        )}
      </Box>
    </Box>
  );
}
