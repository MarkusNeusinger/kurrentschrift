// Wörter — the third view, and the one where errors actually become visible
// (optimierungs-werkbank.md §2). Any text can be typed: the engine writes it,
// the view breaks it into the letters and joins it is made of, and if a plate
// of this hand happens to contain the word, the traced specimen sits underneath
// with its occurrence boxes.
//
// The free-text field is deliberately the FIRST thing, not a filter over the
// harvested list: a word that no plate ever wrote still has to look right, and
// until now there was nowhere in the admin to look at one and complain about
// it. A specimen turns the same word into measurable evidence — but its absence
// costs only the evidence, never the judgement.

import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  FormControlLabel,
  Switch,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { WrittenWord } from '@/components/WrittenWord';
import { useAdmin } from '@/context/AdminContext';
import { fetchRenderWord, getWordSampleScore } from '@/lib/api';
import type { ComposedWordOut, WordSampleScoreOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { WordComparison, type WordCompareMode } from '@/sections/admin/compare/WordComparison';
import { WordTraceEditorDialog } from '@/sections/admin/belege/WordTraceEditorDialog';
import { useFileMark } from '@/sections/admin/shell/KorbContext';
import { LayerDot } from '@/sections/admin/shell/LayerDot';
import { WERKBANK_COLORS } from '@/sections/admin/shell/model';
import { Panel, ViewHeader } from '@/sections/admin/shell/Panel';
import { useWorkbench } from '@/sections/admin/shell/WorkbenchData';
import { joinsOfText, joinsUrl, keysOfText, lettersUrl, readWordFocus, wordsUrl } from '@/sections/admin/shell/focus';
import { badness } from '@/sections/admin/shell/model';
import { garamond } from '@/styles/paper';

import { WordSpineCard } from './WordSpineCard';

const WORD_H = 130; // px — the composed word, large enough to judge the rhythm

export function WordView() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const { source, sourceId } = useAdmin();
  const workbench = useWorkbench();
  const fileMark = useFileMark();
  const t = de.admin.words;

  const { text, specimenId } = readWordFocus(params);
  // The input is free until submitted — typing must not re-compose on every
  // keystroke (each distinct text is a server composition).
  const [draft, setDraft] = useState(text ?? '');
  const [mode, setMode] = useState<WordCompareMode>('words');
  const [filter, setFilter] = useState('');
  // What is drawn OVER the specimen crop. The overview defaults to the plain
  // side-by-side (crop | wie geschrieben) — the same first look the letters
  // grid gives — and the overlay is one switch away for when the exact
  // deviation is the question. In the detail the two layers are separately
  // switchable: three inks over one crop is a lot, and which pair matters
  // (ink↔trace, ink↔engine, trace↔engine) changes with the question.
  const [overlay, setOverlay] = useState(false);
  const [showTrace, setShowTrace] = useState(true);
  const [composed, setComposed] = useState<ComposedWordOut | null>(null);
  const [missing, setMissing] = useState<string[]>([]);
  const [editing, setEditing] = useState<string | null>(null);
  const [scores, setScores] = useState<Record<string, WordSampleScoreOut | 'busy' | 'error'>>({});

  useEffect(() => {
    setDraft(text ?? '');
    setMissing([]);
  }, [text]);

  // The composed payload for the evidence overlay. WrittenWord keeps its own
  // internally, so this goes through the SAME shared render cache — one
  // request per text for the panel above and the overlay below.
  useEffect(() => {
    if (!text) {
      setComposed(null);
      return;
    }
    let cancelled = false;
    setComposed(null);
    fetchRenderWord(sourceId, text)
      .then((c) => {
        if (!cancelled) setComposed(c);
      })
      .catch(() => {
        // The panel above reports a compose failure already — the overlay just
        // stays absent rather than claiming a second error.
        if (!cancelled) setComposed(null);
      });
    return () => {
      cancelled = true;
    };
  }, [sourceId, text]);

  const focus = (next: string | null, sample?: string | null) =>
    setParams(next ? { w: next, ...(sample ? { s: sample } : {}) } : {}, { replace: false });

  // Every stored trace of this word — usually one, but a word can appear on
  // several plates, and each occurrence is its own piece of evidence. The
  // specimen named in the URL comes first so a deep link lands on it.
  const traces = useMemo(() => {
    if (!text) return [];
    const needle = text.trim().toLowerCase();
    return workbench.wordRows
      .filter((row) => row.word.toLowerCase() === needle && workbench.sampleById.has(row.specimen_id))
      .sort((a, b) => {
        if (a.specimen_id === specimenId) return -1;
        if (b.specimen_id === specimenId) return 1;
        return badness(b) - badness(a);
      });
  }, [text, specimenId, workbench.wordRows, workbench.sampleById]);

  const letterKeys = useMemo(() => (text ? keysOfText(text) : []), [text]);
  const joinKeys = useMemo(() => (text ? joinsOfText(text) : []), [text]);

  const runScore = (sampleId: string) => {
    setScores((prev) => ({ ...prev, [sampleId]: 'busy' }));
    getWordSampleScore(sourceId, sampleId)
      .then((score) => setScores((prev) => ({ ...prev, [sampleId]: score })))
      .catch(() => setScores((prev) => ({ ...prev, [sampleId]: 'error' })));
  };

  const input = (
    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, flexWrap: 'wrap' }}>
      <TextField
        size="small"
        label={t.freeTextLabel}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') focus(draft.trim() || null);
        }}
        helperText={t.freeTextHint}
        sx={{ width: { xs: '100%', sm: 300 } }}
      />
      <Button size="small" variant="contained" sx={{ mt: 0.5 }} onClick={() => focus(draft.trim() || null)}>
        {t.freeTextSubmit}
      </Button>
    </Box>
  );

  if (!text) {
    return (
      <Box sx={{ p: { xs: 2, md: 3 }, overflowY: 'auto' }}>
        <ViewHeader eyebrow={de.admin.shell.startEyebrow} title={t.overviewTitle} intro={t.overviewIntro} />
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'flex-start', mb: 2 }}>
          {input}
          <TextField
            size="small"
            label={t.filterLabel}
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            sx={{ width: 200 }}
          />
          <ToggleButtonGroup
            size="small"
            exclusive
            value={mode}
            onChange={(_e, next: WordCompareMode | null) => next && setMode(next)}
            sx={{ mt: 0.25 }}
          >
            <ToggleButton value="words">{de.admin.compare.tabWords}</ToggleButton>
            <ToggleButton value="other">{de.admin.compare.tabOther}</ToggleButton>
          </ToggleButtonGroup>
          {/* The registered overlay is the sharpest error-finding view the
              project has — engine ink projected onto the specimen pixels — so
              it stays one switch away and ON by default, as it was before. */}
          <FormControlLabel
            sx={{ mt: 0.25 }}
            control={<Switch size="small" checked={overlay} onChange={(e) => setOverlay(e.target.checked)} />}
            label={<Typography variant="caption">{de.admin.compare.overlayToggle}</Typography>}
          />
        </Box>
        <WordComparison
          mode={mode}
          overlay={overlay}
          filterText={filter}
          onPick={(sample) => focus(sample.word, sample.id)}
        />
      </Box>
    );
  }

  return (
    <Box sx={{ p: { xs: 2, md: 3 }, overflowY: 'auto' }}>
      <ViewHeader
        eyebrow={de.admin.shell.areaWords}
        title={<Typography sx={{ fontFamily: garamond, fontSize: 28, lineHeight: 1.2 }}>{text}</Typography>}
        chips={
          <>
            <Chip
              size="small"
              variant="outlined"
              label={fmt(traces.length === 1 ? t.traceCountOne : t.traceCount, { count: traces.length })}
            />
            {missing.length > 0 && (
              <Chip size="small" color="warning" label={`${de.admin.compare.missingPrefix}${missing.join(', ')}`} />
            )}
            {traces.length > 0 && (
              <ToggleButtonGroup
                size="small"
                value={[...(showTrace ? ['trace'] : []), ...(overlay ? ['engine'] : [])]}
                onChange={(_e, next: string[]) => {
                  setShowTrace(next.includes('trace'));
                  setOverlay(next.includes('engine'));
                }}
                aria-label={de.admin.werkbank.layersLabel}
              >
                {/* A colour dot rather than coloured text: the swatch is the
                    legend for the line in the crop and stays readable in both
                    states, where a tinted label made an unselected button look
                    active. MUI keeps the selected background as the state. */}
                <ToggleButton value="trace">
                  <LayerDot color={WERKBANK_COLORS.traceOverInk} />
                  {de.admin.werkbank.layerTrace}
                </ToggleButton>
                <ToggleButton value="engine">
                  <LayerDot color={WERKBANK_COLORS.engine} />
                  {de.admin.werkbank.layerEngine}
                </ToggleButton>
              </ToggleButtonGroup>
            )}
          </>
        }
      >
        <Button size="small" onClick={() => focus(null)}>
          {t.toOverview}
        </Button>
        <Button size="small" variant="text" onClick={() => fileMark({ target: { kind: 'word', word: text } })}>
          {`⚑ ${de.admin.werkbank.markWord}`}
        </Button>
      </ViewHeader>

      <Box sx={{ mb: 2 }}>{input}</Box>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {/* 1 — the engine's answer, for ANY text. */}
        <Panel title={t.writtenTitle} caption={t.writtenCaption}>
          <Box
            sx={{
              bgcolor: '#fff',
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
              p: 1,
              overflowX: 'auto',
            }}
          >
            <WrittenWord
              key={text}
              text={text}
              sourceId={sourceId}
              height={WORD_H}
              maxWidth={9999}
              animate={false}
              showLineature
              onResolved={(info) => setMissing(info.missing)}
            />
          </Box>
        </Panel>

        {/* 2 — what it is made of: the way into the other two views, for a
            typed word exactly as for a harvested one. */}
        <Panel title={t.partsTitle} caption={t.partsCaption}>
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
            {letterKeys.map((key, i) => (
              <Chip
                key={`${key}-${i}`}
                size="small"
                variant="outlined"
                clickable
                color={missing.includes(key) ? 'warning' : 'default'}
                label={key}
                onClick={() => navigate(lettersUrl(key))}
              />
            ))}
          </Box>
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            {joinKeys.length === 0 ? (
              <Typography variant="caption" color="text.disabled">
                {t.noJoins}
              </Typography>
            ) : (
              joinKeys.map((join, i) => (
                <Chip
                  key={`${join.leftKey}-${join.rightKey}-${i}`}
                  size="small"
                  variant="outlined"
                  clickable
                  label={`${join.leftKey}→${join.rightKey}`}
                  onClick={() => navigate(joinsUrl(join.leftKey, join.rightKey))}
                />
              ))
            )}
          </Box>
        </Panel>

        {/* 3 — the measured side, where a plate of this hand wrote the word. */}
        {workbench.error ? (
          <Alert severity="warning">{de.admin.shell.evidenceError}</Alert>
        ) : workbench.loading ? (
          <Box sx={{ p: 3, display: 'flex', justifyContent: 'center' }}>
            <CircularProgress size={24} />
          </Box>
        ) : traces.length === 0 ? (
          <Alert severity="info">{t.noSpecimen}</Alert>
        ) : (
          traces.map((row) => {
            const sample = workbench.sampleById.get(row.specimen_id);
            if (!sample) return null;
            const score = scores[sample.id];
            return (
              <WordSpineCard
                key={`${row.kind}:${row.specimen_id}`}
                row={row}
                sample={sample}
                sourceId={sourceId}
                boxes={workbench.boxesBySpecimen.get(row.specimen_id) ?? []}
                // The card always gets the composition — its right-hand face
                // IS the engine's answer. The switch only decides whether the
                // same ink is additionally projected onto the plate pixels.
                composed={composed}
                overlay={overlay}
                showTrace={showTrace}
                onOpenLetter={(glyphKey) => navigate(lettersUrl(glyphKey))}
                onOpenPair={(leftKey, rightKey) => navigate(joinsUrl(leftKey, rightKey))}
                onMark={fileMark}
                actions={
                  <>
                    {score === 'busy' ? (
                      <CircularProgress size={16} />
                    ) : score === 'error' ? (
                      <Chip size="small" color="error" variant="outlined" label={de.admin.compare.scoreFailed} />
                    ) : score ? (
                      <Tooltip title={t.scoreHint}>
                        <Chip size="small" variant="outlined" label={`Loss ${score.loss.toFixed(2)}`} />
                      </Tooltip>
                    ) : (
                      <Button size="small" onClick={() => runScore(sample.id)}>
                        {t.scoreButton}
                      </Button>
                    )}
                    <Button size="small" onClick={() => setEditing(row.specimen_id)}>
                      {de.admin.belege.editOpen}
                    </Button>
                  </>
                }
              />
            );
          })
        )}
      </Box>

      {editing &&
        (() => {
          const row = traces.find((r) => r.specimen_id === editing);
          const sample = row ? workbench.sampleById.get(row.specimen_id) : undefined;
          if (!row || !sample) return null;
          return (
            <WordTraceEditorDialog
              open
              row={row}
              sample={sample}
              sourceId={sourceId}
              // The row's own hand wins inside the dialog; this is the fallback
              // for traces harvested before the hands wiring existed.
              fallbackHandId={source?.hand_id ?? null}
              onClose={() => setEditing(null)}
              // A saved authored trace replaces the row the workbench holds —
              // the URL re-navigation is the cheapest honest refresh: it lands
              // on the same word and remounts the evidence.
              onSaved={() => {
                setEditing(null);
                navigate(wordsUrl(text, sample.id), { replace: true });
              }}
            />
          );
        })()}
    </Box>
  );
}
