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
  MenuItem,
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
import { useAdmin } from '@/context/adminState';
import { fetchRenderWord, getWordSampleScore } from '@/lib/api';
import type { ComposedWordOut, WordSampleScoreOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { WordComparison, type WordCompareMode } from '@/sections/admin/compare/WordComparison';
import { WordTraceEditorDialog } from '@/sections/admin/belege/WordTraceEditorDialog';
import { useFileMark } from '@/sections/admin/shell/korbState';
import { LayerDot } from '@/sections/admin/shell/LayerDot';
import { Panel, ViewHeader } from '@/sections/admin/shell/Panel';
import { useWorkbench } from '@/sections/admin/shell/workbenchState';
import { joinsOfText, joinsUrl, keysOfText, lettersUrl, readWordFocus, wordsUrl } from '@/sections/admin/shell/focus';
import {
  canTraceByHand,
  ownHandEvidence,
  seedWordInstance,
  wordEvidenceOf,
  type TraceFilter,
} from '@/sections/admin/shell/model';
import { garamond, layer, layerDash } from '@/styles/paper';

import { AuthoredTraceReview } from './AuthoredTraceReview';
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
  // The overview's third tab is not a compare mode: it stacks the hand-authored
  // traces alone, as a quality pass over one's own pen work.
  const [mode, setMode] = useState<WordCompareMode | 'authored'>('words');
  const [filter, setFilter] = useState('');
  // Which specimens of the tab to list, by their standing in the manual
  // tracing pass. „Offen" is the whole point: without it the still-to-trace
  // rows are only findable by scrolling the full list looking for a missing
  // chip — and the ones that can NEVER be traced (clipped ink) sit in there
  // indistinguishably. Default stays „Alle": the overview is first of all an
  // overview.
  const [traceFilter, setTraceFilter] = useState<TraceFilter>('all');
  // What is drawn OVER the specimen crop. The overview defaults to the plain
  // side-by-side (crop | wie geschrieben) — the same first look the letters
  // grid gives — and the overlay is one switch away for when the exact
  // deviation is the question. In the detail the two layers are separately
  // switchable: three inks over one crop is a lot, and which pair matters
  // (ink↔trace, ink↔engine, trace↔engine) changes with the question.
  const [overlay, setOverlay] = useState(false);
  const [showTrace, setShowTrace] = useState(true);
  // „Pfad" reads the SAME stored line as a movement — order, direction, lifts.
  // Off by default: the plain line is the first look, and three inks plus
  // arrows over one crop is a lot when the question is only „trifft der Fit".
  const [showPath, setShowPath] = useState(false);
  const [composed, setComposed] = useState<ComposedWordOut | null>(null);
  const [missing, setMissing] = useState<string[]>([]);
  const [editing, setEditing] = useState<string | null>(null);
  const [scores, setScores] = useState<Record<string, WordSampleScoreOut | 'busy' | 'error'>>({});

  // The field mirrors the focused word: a navigation (a link, the back button)
  // re-seeds the draft and drops the previous word's missing-glyph list. Done
  // DURING RENDER — React's "adjusting state when a prop changes"
  // (react-hooks/set-state-in-effect) — so the field never shows the old word
  // for a frame. `text` is compared raw rather than through a key, because
  // „nothing focused" (null) is a state of its own here.
  const [mirrored, setMirrored] = useState(text);
  if (mirrored !== text) {
    setMirrored(text);
    setDraft(text ?? '');
    setMissing([]);
  }

  // Same, for the overlay's composition: it must not outlive the word or the
  // source it was composed for.
  const loadKey = `${sourceId} ${text ?? ''}`;
  const [composedFor, setComposedFor] = useState(loadKey);
  if (composedFor !== loadKey) {
    setComposedFor(loadKey);
    setComposed(null);
  }

  // The composed payload for the evidence overlay. WrittenWord keeps its own
  // internally, so this goes through the SAME shared render cache — one
  // request per text for the panel above and the overlay below.
  useEffect(() => {
    // Nothing focused: the guard above has already cleared the payload.
    if (!text) return;
    let cancelled = false;
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

  // Every WORTPROBE of this word — usually one, but a word can appear on
  // several plates, and each occurrence is its own piece of evidence. Each
  // carries its stored trace where the hand has drawn one; the specimen named
  // in the URL comes first so a deep link lands on it.
  //
  // The list is built from the samples, not from the stored traces: the
  // overview already shows an untraced Wortprobe with its crop, and the detail
  // — the one place where the tracing actually happens — used to answer the
  // deep link into it with „gibt es nicht".
  const evidence = useMemo(
    () => wordEvidenceOf(workbench.samples, workbench.wordRows, text ?? '', specimenId),
    [text, specimenId, workbench.samples, workbench.wordRows],
  );
  // What the head may count. A foreign writer's sample (Abb. 22) stands in the
  // list as context but never in a number of THIS hand — V4 —, so the counts
  // run over the plate's own evidence and the foreign ones get a chip of their
  // own rather than being folded in or silently dropped.
  const own = useMemo(() => ownHandEvidence(evidence), [evidence]);
  const tracedCount = useMemo(() => own.filter((e) => e.row).length, [own]);
  const foreignCount = evidence.length - own.length;

  // What the editor is opened on. A Wortprobe that has never been traced gets a
  // SEEDED row — the same shape the dialog already takes —, so the tested write
  // flow is called rather than rebuilt: no new prop, no new branch, and the
  // first authored trace for a specimen is the upsert the server has always
  // accepted. The memo keeps the seed's object identity stable while the dialog
  // is open.
  // Through `canTraceByHand`, so a refetch that turns a sample into context —
  // a re-harvest dropping a row, a sidecar marking the ink clipped — closes an
  // open dialog instead of leaving a write path standing that the list itself
  // no longer offers.
  const editingEvidence = useMemo(
    () => (editing ? (evidence.find((e) => e.sample.id === editing && canTraceByHand(e)) ?? null) : null),
    [editing, evidence],
  );
  const editingRow = useMemo(
    () => (editingEvidence ? (editingEvidence.row ?? seedWordInstance(editingEvidence.sample)) : null),
    [editingEvidence],
  );

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
          {/* The Nachfahr-Übersicht is the authored rows BY DEFINITION — a
              status filter over it would only ever have one non-empty entry. */}
          {mode !== 'authored' && (
            <TextField
              select
              size="small"
              label={de.admin.compare.statusLabel}
              value={traceFilter}
              onChange={(e) => setTraceFilter(e.target.value as TraceFilter)}
              sx={{ width: 190 }}
            >
              <MenuItem value="all">{de.admin.compare.statusAll}</MenuItem>
              <MenuItem value="open">{de.admin.compare.statusOpen}</MenuItem>
              <MenuItem value="authored">{de.admin.compare.statusAuthored}</MenuItem>
              <MenuItem value="incomplete">{de.admin.compare.statusIncomplete}</MenuItem>
            </TextField>
          )}
          <ToggleButtonGroup
            size="small"
            exclusive
            value={mode}
            onChange={(_e, next: WordCompareMode | 'authored' | null) => next && setMode(next)}
            sx={{ mt: 0.25 }}
          >
            <ToggleButton value="words">{de.admin.compare.tabWords}</ToggleButton>
            <ToggleButton value="other">{de.admin.compare.tabOther}</ToggleButton>
            <ToggleButton value="authored">{t.tabAuthored}</ToggleButton>
          </ToggleButtonGroup>
          {/* The registered overlay is the sharpest error-finding view the
              project has — engine ink projected onto the specimen pixels — so
              it stays one switch away and ON by default, as it was before.
              The authored review has no engine layer, so the switch hides. */}
          {mode !== 'authored' && (
            <FormControlLabel
              sx={{ mt: 0.25 }}
              control={<Switch size="small" checked={overlay} onChange={(e) => setOverlay(e.target.checked)} />}
              label={<Typography variant="caption">{de.admin.compare.overlayToggle}</Typography>}
            />
          )}
        </Box>
        {mode === 'authored' ? (
          <AuthoredTraceReview filterText={filter} onPickWord={(word, sampleId) => focus(word, sampleId)} />
        ) : (
          <WordComparison
            mode={mode}
            overlay={overlay}
            filterText={filter}
            traceFilter={traceFilter}
            onPick={(sample) => focus(sample.word, sample.id)}
          />
        )}
      </Box>
    );
  }

  return (
    <Box sx={{ p: { xs: 2, md: 3 }, overflowY: 'auto' }}>
      <ViewHeader
        eyebrow={de.admin.shell.areaWords}
        titleText={fmt(t.wordHeading, { text })}
        title={<Typography sx={{ fontFamily: garamond, fontSize: 28, lineHeight: 1.2 }}>{text}</Typography>}
        chips={
          <>
            {/* Two counts, because they are two things: how many Wortproben
                the plate has of this text, and how many of them already carry
                a stored Bahn. One number could only ever have been one of the
                two, and the gap between them IS the remaining work. Both count
                THIS hand only. */}
            <Chip
              size="small"
              variant="outlined"
              label={fmt(own.length === 1 ? t.sampleCountOne : t.sampleCount, { count: own.length })}
            />
            <Chip
              size="small"
              variant="outlined"
              label={fmt(tracedCount === 1 ? t.traceCountOne : t.traceCount, { count: tracedCount })}
            />
            {/* The foreign writer's samples are announced, not hidden and not
                folded in — a separate number under their own name is the only
                way both statements stay true. */}
            {foreignCount > 0 && (
              <Tooltip title={de.admin.werkbank.foreignSetHint}>
                <Chip
                  size="small"
                  variant="outlined"
                  label={fmt(de.admin.werkbank.foreignCount, { count: foreignCount })}
                />
              </Tooltip>
            )}
            {missing.length > 0 && (
              <Chip size="small" color="warning" label={`${de.admin.compare.missingPrefix}${missing.join(', ')}`} />
            )}
            {evidence.length > 0 && (
              <ToggleButtonGroup
                size="small"
                value={[
                  ...(showTrace ? ['trace'] : []),
                  ...(showPath ? ['path'] : []),
                  ...(overlay ? ['engine'] : []),
                ]}
                onChange={(_e, next: string[]) => {
                  // „Pfad" is a reading of the trace, so it brings its line
                  // with it: switching it on without the layer it decorates
                  // would leave the arrows floating over bare ink.
                  const path = next.includes('path');
                  setShowPath(path);
                  setShowTrace(path || next.includes('trace'));
                  setOverlay(next.includes('engine'));
                }}
                aria-label={de.admin.werkbank.layersLabel}
              >
                {/* A swatch rather than coloured text: it is the legend for
                    the line in the crop and stays readable in both states,
                    where a tinted label made an unselected button look active.
                    MUI keeps the selected background as the state. The swatch
                    carries the line's STROKE STYLE too — two of the three hues
                    are one colour for a deuteranope, so the label and the dash
                    are what actually tell them apart. */}
                <ToggleButton value="trace">
                  <LayerDot color={layer.trace} dash={layerDash.trace} />
                  {de.admin.werkbank.layerTrace}
                </ToggleButton>
                <Tooltip title={de.admin.werkbank.layerPathHint}>
                  <ToggleButton value="path">
                    <LayerDot color={layer.path} dash={layerDash.path} />
                    {de.admin.werkbank.layerPath}
                  </ToggleButton>
                </Tooltip>
                <ToggleButton value="engine">
                  <LayerDot color={layer.engine} dash={layerDash.engine} />
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
        ) : evidence.length === 0 ? (
          <Alert severity="info">{t.noSpecimen}</Alert>
        ) : (
          evidence.map((item) => {
            const { sample, row } = item;
            const score = scores[sample.id];
            return (
              <WordSpineCard
                key={`${sample.kind}:${sample.id}`}
                row={row}
                sample={sample}
                sourceId={sourceId}
                boxes={workbench.boxesBySpecimen.get(sample.id) ?? []}
                // The card always gets the composition — its right-hand face
                // IS the engine's answer. The switch only decides whether the
                // same ink is additionally projected onto the plate pixels.
                composed={composed}
                overlay={overlay}
                showTrace={showTrace}
                showPath={showPath}
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
                    {/* Also on a Wortprobe without a stored Bahn — that entry
                        IS the point of this card being here. Which samples are
                        context rather than work, and why, is `canTraceByHand`;
                        the card carries the reason beside this gap, as the
                        „andere Hand" and „Unvollständig" chips. */}
                    {canTraceByHand(item) && (
                      <Button size="small" onClick={() => setEditing(sample.id)}>
                        {de.admin.belege.editOpen}
                      </Button>
                    )}
                  </>
                }
              />
            );
          })
        )}
      </Box>

      {editingEvidence && editingRow && (
        <WordTraceEditorDialog
          open
          row={editingRow}
          sample={editingEvidence.sample}
          sourceId={sourceId}
          // The row's own hand wins inside the dialog. A seeded row has none, so
          // the fallback has to resolve one: the hand the workbench derived from
          // this source's own occurrences (the same tally that names the hand
          // for the statistics layers), and only then the source's registration.
          // Resolves neither — no occurrence names a hand and `sources.hand_id`
          // is unset — the dialog says so in German and keeps saving disabled,
          // which is the honest state rather than a write under a guessed hand.
          // A foreign writer's sample never gets the plate hand: the entry is
          // not offered for one, and if it were ever reached the dialog keeps
          // saving disabled with its own reason rather than mislabelling a hand.
          fallbackHandId={
            editingEvidence.sample.sample_set ? null : (workbench.handId ?? source?.hand_id ?? null)
          }
          onClose={() => setEditing(null)}
          // A saved authored trace replaces the row the workbench holds —
          // refetch the traces so the evidence shows the stored state, and
          // re-navigate so the URL still names the specimen.
          onSaved={() => {
            setEditing(null);
            workbench.refreshWordTraces();
            navigate(wordsUrl(text, editingEvidence.sample.id), { replace: true });
          }}
        />
      )}
    </Box>
  );
}
