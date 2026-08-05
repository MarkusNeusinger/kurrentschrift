// Übergänge — the second view. A join is not a letter and not a word: it is
// the thing the engine GENERATES between two letters, and the whole doctrine
// hangs on judging it before anyone reaches for an override
// (optimierungs-werkbank.md §3/§4). So this view puts the composed join, what
// the plates actually wrote, and what those measurements condense to next to
// each other — and offers the pair editor last, not first.
//
// The free-text field is the other half of the brief: ANY two-letter
// combination can be typed, not only those a plate happens to contain. Most
// combinations were never written by hand anywhere; they still have to look
// right, and now they can be looked at and complained about.

import { Box, Button, Chip, Collapse, TextField, Typography } from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { WrittenWord } from '@/components/WrittenWord';
import { useAdmin } from '@/context/AdminContext';
import { getPairs } from '@/lib/api';
import type { GlyphPairOut, WordSampleOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { WordComparison } from '@/sections/admin/compare/WordComparison';
import { PairEditorDialog } from '@/sections/admin/pairs/PairEditorDialog';
import { PairMatrix } from '@/sections/admin/pairs/PairMatrix';
import { PairStats } from '@/sections/admin/shell/LensStats';
import { LetterPicker } from '@/sections/admin/shell/LetterPicker';
import { CropThumb } from '@/sections/admin/shell/OccurrenceThumb';
import { useFileMark } from '@/sections/admin/shell/KorbContext';
import { Panel, ViewHeader } from '@/sections/admin/shell/Panel';
import { useWorkbench } from '@/sections/admin/shell/WorkbenchData';
import {
  lettersUrl,
  pairKeysOfText,
  readJoinFocus,
  textForKey,
  textForPair,
  wordsUrl,
} from '@/sections/admin/shell/focus';
import { WERKBANK_COLORS, joinCropBoxOf, pairKeyOf, type CropBox } from '@/sections/admin/shell/model';
import { garamond } from '@/styles/paper';

const PREVIEW_H = 150; // px — a join needs room, but stays scannable

export function JoinView() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const { sourceId } = useAdmin();
  const workbench = useWorkbench();
  const fileMark = useFileMark();
  const t = de.admin.joins;

  const { leftKey, rightKey } = readJoinFocus(params);
  const [freeText, setFreeText] = useState('');
  const [freeError, setFreeError] = useState<string | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [matrixOpen, setMatrixOpen] = useState(false);
  const [specimensOpen, setSpecimensOpen] = useState(false);
  // Bumped after a save in the editor: the override row and the composed
  // preview both have to be re-read, and so do the matrix badges.
  const [pairTick, setPairTick] = useState(0);
  const [overrideRow, setOverrideRow] = useState<GlyphPairOut | null>(null);

  const focus = (left: string | null, right: string | null) =>
    setParams(left && right ? { l: left, r: right } : {}, { replace: false });

  // The override row of exactly this join (drafts included — the admin fetch
  // carries the auth header), so the view can say whether the engine is still
  // generating this join or a stored row replaced it.
  useEffect(() => {
    if (!leftKey || !rightKey) {
      setOverrideRow(null);
      return;
    }
    let cancelled = false;
    getPairs(sourceId, { all: true }, { retries: 1 })
      .then((rows) => {
        if (cancelled) return;
        setOverrideRow(rows.find((r) => r.left_key === leftKey && r.right_key === rightKey) ?? null);
      })
      .catch(() => {
        if (!cancelled) setOverrideRow(null);
      });
    return () => {
      cancelled = true;
    };
  }, [sourceId, leftKey, rightKey, pairTick]);

  // A typed combination is identified exactly like a harvested one: shaped into
  // keys. Two characters that fold into a ligature (ſt, ch, …) are ONE glyph
  // and have no join — saying so is more useful than showing an empty view.
  const submitFreeText = () => {
    const text = freeText.trim();
    if (!text) return;
    const keys = pairKeysOfText(text);
    if (!keys) {
      setFreeError(t.freeTextInvalid);
      return;
    }
    setFreeError(null);
    focus(keys[0], keys[1]);
  };

  const pairText = leftKey && rightKey ? textForPair(leftKey, rightKey) : '';
  const occurrences = leftKey && rightKey ? (workbench.pairsByKey.get(pairKeyOf(leftKey, rightKey)) ?? []) : [];
  const aggregate = leftKey && rightKey ? workbench.pairAggregateByKey.get(pairKeyOf(leftKey, rightKey)) : undefined;

  // The dissected occurrences split by whether their ink can be shown. A
  // `pair_instance` stores no pixel box (its geometry is in the glyph_pairs
  // frame, relative to the left glyph's exit), but it names the specimen and
  // the LEFT glyph's slot, and the letter occurrences of the same plate carry
  // those slots as boxes — so the join's crop is the union of the two letters
  // it runs between. On an Abb.-20 pair drill the whole cell IS the join and
  // needs no cut, which is the only way those rows get a tile at all: the
  // letter harvest never fitted the drill plates.
  const { cropped, plain } = useMemo(() => {
    const cropped: { occ: (typeof occurrences)[number]; sample: WordSampleOut; box: CropBox }[] = [];
    const plain: { occ: (typeof occurrences)[number]; sample?: WordSampleOut }[] = [];
    for (const occ of occurrences) {
      const sample = workbench.sampleById.get(occ.specimen_id);
      const box = !sample
        ? null
        : (joinCropBoxOf(occ, workbench.boxesBySpecimen.get(occ.specimen_id), sample.rect) ??
          (occ.kind === 'pair' ? { x: 0, y: 0, w: sample.width, h: sample.height } : null));
      if (sample && box) cropped.push({ occ, sample, box });
      else plain.push({ occ, sample });
    }
    return { cropped, plain };
  }, [occurrences, workbench.sampleById, workbench.boxesBySpecimen]);

  // The words this join was measured in — the way over into the Wörter view.
  const relatedWords = useMemo(() => {
    const out = new Map<string, { specimenId: string; word: string }>();
    for (const occ of occurrences) {
      const sample = workbench.sampleById.get(occ.specimen_id);
      if (sample) out.set(sample.id, { specimenId: sample.id, word: sample.word });
    }
    return [...out.values()];
  }, [occurrences, workbench.sampleById]);

  const picker = (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
      <LetterPicker activeKey={leftKey} onPick={(key) => focus(key, rightKey ?? key)}>
        {(open) => (
          <Chip
            clickable
            onClick={open}
            label={
              <Typography component="span" sx={{ fontFamily: garamond, fontSize: 20 }}>
                {leftKey ? textForKey(leftKey) : t.pickLeft}
              </Typography>
            }
          />
        )}
      </LetterPicker>
      <Typography color="text.secondary">→</Typography>
      <LetterPicker
        activeKey={rightKey}
        // The right side of a join is never a capital: Kurrent/Sütterlin
        // capitals start a word (docs/concepts/architektur.md §4), so the
        // matrix and the composer only ever place them on the left.
        isDisabled={(letter) => letter.group === 'upper'}
        onPick={(key) => focus(leftKey ?? key, key)}
      >
        {(open) => (
          <Chip
            clickable
            onClick={open}
            label={
              <Typography component="span" sx={{ fontFamily: garamond, fontSize: 20 }}>
                {rightKey ? textForKey(rightKey) : t.pickRight}
              </Typography>
            }
          />
        )}
      </LetterPicker>
    </Box>
  );

  const freeInput = (
    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, flexWrap: 'wrap' }}>
      <TextField
        size="small"
        label={t.freeTextLabel}
        value={freeText}
        error={Boolean(freeError)}
        helperText={freeError ?? t.freeTextHint}
        onChange={(e) => {
          setFreeText(e.target.value);
          setFreeError(null);
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter') submitFreeText();
        }}
        sx={{ width: 220 }}
      />
      <Button size="small" variant="outlined" sx={{ mt: 0.5 }} onClick={submitFreeText}>
        {t.freeTextSubmit}
      </Button>
    </Box>
  );

  if (!leftKey || !rightKey) {
    return (
      <Box sx={{ p: { xs: 2, md: 3 }, overflowY: 'auto' }}>
        <ViewHeader eyebrow={de.admin.shell.startEyebrow} title={t.overviewTitle} intro={t.overviewIntro} />
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 3 }}>
          {picker}
          {freeInput}
        </Box>
        <PairMatrix onPickPair={focus} refreshKey={pairTick} />

        {/* The Abb.-20 letter-pair plates: the only specimens that are pure
            JOINS, so they belong under Übergänge rather than with the words.
            They carry the „Gemessen" chips of the H2 layer and the editor deep
            link, which is why the whole card list is reused as-is. */}
        <Box sx={{ mt: 4 }}>
          <Button size="small" onClick={() => setSpecimensOpen((v) => !v)}>
            {specimensOpen ? t.hideSpecimens : t.showSpecimens}
          </Button>
          <Collapse in={specimensOpen} unmountOnExit>
            <Box sx={{ mt: 2 }}>
              <WordComparison
                mode="pairs"
                overlay={false}
                onPick={(sample) => {
                  const keys = pairKeysOfText(sample.word);
                  if (keys) focus(keys[0], keys[1]);
                }}
              />
            </Box>
          </Collapse>
        </Box>
      </Box>
    );
  }

  return (
    <Box sx={{ p: { xs: 2, md: 3 }, overflowY: 'auto' }}>
      <ViewHeader
        eyebrow={de.admin.shell.areaJoins}
        title={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            {picker}
            <Typography variant="caption" color="text.secondary">
              {`${leftKey}→${rightKey}`}
            </Typography>
            {/* The free-text field stays reachable INSIDE the detail, like the
                word field does — typing the next combination must not mean
                going back to the overview first. */}
            {freeInput}
          </Box>
        }
        chips={
          <>
            <Chip
              size="small"
              variant="outlined"
              color={overrideRow ? (overrideRow.approved ? 'success' : 'warning') : 'default'}
              label={
                overrideRow
                  ? overrideRow.approved
                    ? de.admin.pairs.badgeApproved
                    : de.admin.pairs.badgeDraft
                  : t.generated
              }
            />
            <Chip size="small" variant="outlined" label={fmt(t.occurrenceCount, { count: occurrences.length })} />
          </>
        }
      >
        <Button size="small" onClick={() => focus(null, null)}>
          {t.toOverview}
        </Button>
        <Button
          size="small"
          variant="text"
          onClick={() => fileMark({ target: { kind: 'pair', leftKey, rightKey } })}
        >
          {`⚑ ${de.admin.werkbank.markPair}`}
        </Button>
      </ViewHeader>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 2, alignItems: 'start' }}>
        {/* 1 — what the engine writes today. */}
        <Panel title={t.writtenTitle} caption={overrideRow?.approved ? t.writtenCaptionOverride : t.writtenCaption}>
          <Box
            sx={{
              bgcolor: '#fff',
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
              p: 1,
              display: 'flex',
              justifyContent: 'center',
            }}
          >
            <WrittenWord
              // Keyed on the save counter so an approved override shows up in
              // the preview immediately instead of behind a cached composition.
              key={`${pairText}-${pairTick}`}
              text={pairText}
              sourceId={sourceId}
              height={PREVIEW_H}
              animate={false}
              showLineature
            />
          </Box>
          {/* The two letters first — checking whether the fault is already in
              one of them is the earlier stage of the triage. The editor comes
              last and quietly (a `text` button under the doctrine line): the
              layout must not make the last resort look like the first move. */}
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1.5 }}>
            <Button size="small" variant="outlined" onClick={() => navigate(lettersUrl(leftKey))}>
              {fmt(t.toLetter, { key: leftKey })}
            </Button>
            <Button size="small" variant="outlined" onClick={() => navigate(lettersUrl(rightKey))}>
              {fmt(t.toLetter, { key: rightKey })}
            </Button>
          </Box>
          <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mt: 1.5 }}>
            {t.overrideLastResort}
          </Typography>
          <Button size="small" sx={{ mt: 0.5, px: 0.5 }} onClick={() => setEditorOpen(true)}>
            {de.admin.werkbank.openPairEditor}
          </Button>
        </Panel>

        {/* 2 — the measured median over the occurrences it condenses. */}
        <Panel title={t.statsTitle} caption={t.statsCaption}>
          <PairStats
            key={`${leftKey}:${rightKey}`}
            aggregate={aggregate}
            occurrences={occurrences}
            stats={workbench.pairStats}
            onRebuild={workbench.rebuildPairStats}
          />
        </Panel>

        {/* 3 — the raw dissections, one row per occurrence. */}
        <Panel title={fmt(t.occurrencesTitle, { count: occurrences.length })} caption={t.occurrencesCaption}>
          {workbench.loading ? (
            <Typography variant="caption" color="text.disabled">
              {t.loadingOccurrences}
            </Typography>
          ) : occurrences.length === 0 ? (
            <Typography variant="caption" color="text.disabled">
              {t.noOccurrences}
            </Typography>
          ) : (
            <>
              {/* The tiles first, as one grid. Interleaving them with the
                  box-less rows made a ragged column of half-pictures — the
                  point of the panel is the comparison BETWEEN the plates, and
                  that only works when the crops stand side by side. */}
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, alignItems: 'flex-start' }}>
                {cropped.map(({ occ, sample, box }) => (
                  <CropThumb
                    key={`${occ.kind}:${occ.specimen_id}:${occ.slot}`}
                    box={box}
                    sample={sample}
                    sourceId={sourceId}
                    onJump={() => navigate(wordsUrl(sample.word, occ.specimen_id))}
                    label={occ.specimen_id}
                    detail={
                      occ.measurements.gen_chamfer === undefined
                        ? undefined
                        : fmt(de.admin.werkbank.genChamferShort, {
                            value: occ.measurements.gen_chamfer.toFixed(3),
                          })
                    }
                    note={
                      occ.measurements.fit_ok === false ? (
                        <Typography variant="caption" sx={{ color: WERKBANK_COLORS.selected, lineHeight: 1.2 }}>
                          {de.admin.werkbank.fitDoubtful}
                        </Typography>
                      ) : undefined
                    }
                  />
                ))}
              </Box>

              {/* Everything with no crop to show: the plate is a pair drill the
                  letter harvest never fitted, or the two harvests disagree
                  about this word's slotting. Listed rather than dropped — the
                  occurrence is counted in the heading and stays reachable —
                  and said out loud, because a shorter grid than the count
                  would otherwise read as missing data. */}
              {plain.length > 0 && (
                <Box sx={{ mt: cropped.length > 0 ? 1.5 : 0 }}>
                  {cropped.length > 0 && (
                    <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mb: 0.5 }}>
                      {fmt(t.occurrencesNoCrop, { count: plain.length })}
                    </Typography>
                  )}
                  {plain.map(({ occ, sample }) => (
                    <Box
                      key={`${occ.kind}:${occ.specimen_id}:${occ.slot}`}
                      sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', py: 0.25 }}
                    >
                      <Chip
                        size="small"
                        variant="outlined"
                        clickable
                        label={occ.specimen_id}
                        onClick={() => navigate(wordsUrl(sample?.word ?? '', occ.specimen_id))}
                      />
                      {occ.measurements.gen_chamfer !== undefined && (
                        <Typography variant="caption" color="text.secondary">
                          {fmt(de.admin.werkbank.genChamfer, { value: occ.measurements.gen_chamfer.toFixed(3) })}
                        </Typography>
                      )}
                      {occ.measurements.fit_ok === false && (
                        <Typography variant="caption" sx={{ color: WERKBANK_COLORS.selected }}>
                          {de.admin.werkbank.fitDoubtful}
                        </Typography>
                      )}
                    </Box>
                  ))}
                </Box>
              )}
            </>
          )}
        </Panel>

        {/* 4 — where the join appears in running text. */}
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

      {/* The systematic grid stays available under the focused join — that is
          how a single odd join is checked against the whole class it belongs
          to, which is the step the doctrine asks for before an override. */}
      <Box sx={{ mt: 2 }}>
        <Button size="small" onClick={() => setMatrixOpen((v) => !v)}>
          {matrixOpen ? t.hideMatrix : t.showMatrix}
        </Button>
        <Collapse in={matrixOpen} unmountOnExit>
          <Box sx={{ mt: 2 }}>
            <Box sx={{ mb: 1 }}>{freeInput}</Box>
            <PairMatrix activeGlyphKey={leftKey} onPickPair={focus} refreshKey={pairTick} />
          </Box>
        </Collapse>
      </Box>

      {editorOpen && (
        <PairEditorDialog
          open
          onClose={() => setEditorOpen(false)}
          pairText={pairText}
          leftKey={leftKey}
          rightKey={rightKey}
          sourceId={sourceId}
          onChanged={() => setPairTick((n) => n + 1)}
        />
      )}
    </Box>
  );
}
