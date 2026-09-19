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

import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Collapse,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { InfoHint } from '@/components/InfoHint';
import { WrittenWord } from '@/components/WrittenWord';
import { TOUCH_TARGET } from '@/styles/hitArea';
import { useAdmin } from '@/context/adminState';
import { glyphKeyFor, LETTERS } from '@/domain/glyphs';
import { getPairs, getWordSampleScore } from '@/lib/api';
import type { ComposedWordOut, GlyphPairOut, InstanceOut, WordInstanceOut, WordSampleOut, WordSampleScoreOut } from '@/lib/api';
import { fetchRenderWord } from '@/lib/api/renderCache';
import { de, fmt } from '@/locales/admin';
import { WordComparison } from '@/sections/admin/compare/WordComparison';
import { PairEditorDialog } from '@/sections/admin/pairs/PairEditorDialog';
import { PairMatrix } from '@/sections/admin/pairs/PairMatrix';
import { findPairRow } from '@/sections/admin/pairs/pairRow';
import { authoredLetters } from '@/sections/admin/pairs/pairRows';
import { PairStats } from '@/sections/admin/shell/LensStats';
import { LayerDot } from '@/sections/admin/shell/LayerDot';
import { LetterPicker } from '@/sections/admin/shell/LetterPicker';
import { CropThumb } from '@/sections/admin/shell/OccurrenceThumb';
import { useFileMark } from '@/sections/admin/shell/korbState';
import { Panel, ViewHeader } from '@/sections/admin/shell/Panel';
import { SubjectStepper } from '@/sections/admin/shell/SubjectStepper';
import { neighboursInOrder, orderCaption, stepOrder, useSubjectNav } from '@/sections/admin/shell/subjectNav';
import { useWorkbench } from '@/sections/admin/shell/workbenchState';
import {
  FOCUS_PARAMS,
  lettersUrl,
  pairKeysOfText,
  readJoinFocus,
  textForKey,
  textForPair,
  wordsUrl,
} from '@/sections/admin/shell/focus';
import { joinCropBoxOf, pairKeyOf, type CropBox, type Mark } from '@/sections/admin/shell/model';
import { WordSpineCard } from '@/sections/admin/words/WordSpineCard';
import { garamond, layer, layerDash } from '@/styles/paper';

const PREVIEW_H = 150; // px — a join needs room, but stays scannable

// The traced drill plate of THIS pair, shown exactly like a word's evidence
// card in the Wörter view: the traced Spur and the engine's ink share the
// row's measured registration, the engine's own face sits beside at the same
// scale. Fetches its own composition — the drill's word is normally the pair
// text, so the shared render cache makes this one request per join.
function DrillSpecimenCard({
  row,
  sample,
  sourceId,
  bust,
  overlay,
  showTrace,
  boxes,
  onOpenLetter,
  onOpenPair,
  onMark,
  onOpenWord,
}: {
  row: WordInstanceOut;
  sample: WordSampleOut;
  sourceId: string;
  bust: number;
  overlay: boolean;
  showTrace: boolean;
  boxes: InstanceOut[];
  onOpenLetter: (glyphKey: string) => void;
  onOpenPair: (leftKey: string, rightKey: string) => void;
  onMark: (mark: Mark) => void;
  onOpenWord: () => void;
}) {
  const [composed, setComposed] = useState<ComposedWordOut | null>(null);
  const [score, setScore] = useState<WordSampleScoreOut | 'busy' | 'error' | null>(null);

  // Dropping the previous card's engine face happens DURING RENDER — React's
  // "adjusting state when a prop changes" (react-hooks/set-state-in-effect) —
  // so a re-keyed card never shows the old join's ink while the new
  // composition is on its way. The word goes last in the key: it is the only
  // free-form part, so no value can straddle a separator.
  const loadKey = `${sourceId} ${bust} ${row.word}`;
  const [shownFor, setShownFor] = useState(loadKey);
  if (shownFor !== loadKey) {
    setShownFor(loadKey);
    setComposed(null);
  }

  useEffect(() => {
    let cancelled = false;
    fetchRenderWord(sourceId, row.word, bust)
      .then((c) => {
        if (!cancelled) setComposed(c);
      })
      .catch(() => {
        // The written panel above reports a compose failure already — the
        // card's engine face just stays pending rather than alarming twice.
        if (!cancelled) setComposed(null);
      });
    return () => {
      cancelled = true;
    };
  }, [sourceId, row.word, bust]);

  const runScore = () => {
    setScore('busy');
    getWordSampleScore(sourceId, sample.id)
      .then(setScore)
      .catch(() => setScore('error'));
  };

  return (
    <WordSpineCard
      row={row}
      sample={sample}
      sourceId={sourceId}
      boxes={boxes}
      composed={composed}
      overlay={overlay}
      showTrace={showTrace}
      onOpenLetter={onOpenLetter}
      onOpenPair={onOpenPair}
      onMark={onMark}
      actions={
        <>
          {score === 'busy' ? (
            <CircularProgress size={16} />
          ) : score === 'error' ? (
            <Chip size="small" color="error" variant="outlined" label={de.admin.compare.scoreFailed} />
          ) : score ? (
            <>
              <Chip size="small" variant="outlined" label={`Loss ${score.loss.toFixed(2)}`} />
              {/* What the ruler IS belongs to a control, not to a hover over a
                  `div` chip (V25). */}
              <InfoHint title={de.admin.compare.scoreLossTitle} label={de.admin.compare.scoreLossAria}>
                {de.admin.words.scoreHint}
              </InfoHint>
            </>
          ) : (
            <Button size="small" onClick={runScore}>
              {de.admin.words.scoreButton}
            </Button>
          )}
          <Button size="small" onClick={onOpenWord}>
            {de.admin.compare.openWord}
          </Button>
        </>
      }
    />
  );
}

export function JoinView() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  // `ownHand`, never `handId`: the workbench's `handId` is the PLATE hand of
  // the statistics below — a different hand (P1-Q3 a).
  const { sourceId, handId: ownHand, glyphsByKey } = useAdmin();
  const workbench = useWorkbench();
  const fileMark = useFileMark();
  // The order the Übergänge matrix last showed — what ‹ › and Alt+Shift+←/→
  // step through (P1-Q12 a).
  const { order: published } = useSubjectNav();
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
  // The glyph_keys the composition could not write, reported by WrittenWord —
  // TAGGED with the pair they were reported for. Tagging rather than clearing in
  // an effect is what makes the chip honest during a switch: the callback only
  // fires once the NEW composition lands, so an untagged value would show the
  // previous join's gap in the meantime.
  const [missingFor, setMissingFor] = useState<{ text: string; keys: string[] }>({ text: '', keys: [] });

  // A focus change MERGES instead of rewriting the query: the overview's list
  // state (Ansicht · Filter · Sortierung) and anything else the URL carries —
  // the scope's `h=` among them — has to survive the hop into a join and back.
  // Still a PUSH: the subject is what the back button walks.
  //
  // The merge is what `keepHand` (focus.ts) was written for one PR earlier,
  // generalised: it kept the ONE parameter the scope needs while the rest of
  // the query was rewritten, and this keeps all of them — the Buchstaben
  // view's pattern, which that helper's own docstring already named as the
  // better one.
  const focus = (left: string | null, right: string | null) => {
    const next = new URLSearchParams(params);
    if (left && right) {
      next.set(FOCUS_PARAMS.left, left);
      next.set(FOCUS_PARAMS.right, right);
    } else {
      next.delete(FOCUS_PARAMS.left);
      next.delete(FOCUS_PARAMS.right);
    }
    setParams(next, { replace: false });
  };

  // „Alle Kombinationen" goes back to the matrix ANCHORED ON THE LEFT LETTER:
  // dropping `l=` with `r=` would land the reader on whichever letter happens
  // to come first, which is exactly the bug „Alle Kombinationen ansehen" had
  // coming the other way.
  const toOverview = () => {
    const next = new URLSearchParams(params);
    next.delete(FOCUS_PARAMS.right);
    setParams(next, { replace: false });
  };

  // Leaving the detail drops the row it belonged to, during render rather than
  // in the effect below (react-hooks/set-state-in-effect). Keyed on „is a join
  // focused" and not on the pair itself, because a SWITCH deliberately leaves
  // the previous row standing until the new one lands — clearing it there
  // would flip the „generiert/Entwurf" chip on every hop.
  const joinFocused = Boolean(leftKey && rightKey);
  const [rowFocused, setRowFocused] = useState(joinFocused);
  if (rowFocused !== joinFocused) {
    setRowFocused(joinFocused);
    if (!joinFocused) setOverrideRow(null);
  }

  // The override row of exactly this join (drafts included — the admin fetch
  // carries the auth header), so the view can say whether the engine is still
  // generating this join or a stored row replaced it.
  useEffect(() => {
    if (!leftKey || !rightKey) return;
    let cancelled = false;
    getPairs(sourceId, { all: true }, { retries: 1 })
      .then((rows) => {
        if (cancelled) return;
        setOverrideRow(findPairRow(rows, leftKey, rightKey));
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
  const missing = missingFor.text === pairText ? missingFor.keys : [];
  // Memoised for its identity, not for the lookup: the `?? []` produced a fresh
  // empty array on every render, which invalidated the two memos below each
  // time (react-hooks/exhaustive-deps).
  const occurrences = useMemo(
    () => (leftKey && rightKey ? (workbench.pairsByKey.get(pairKeyOf(leftKey, rightKey)) ?? []) : []),
    [leftKey, rightKey, workbench.pairsByKey],
  );
  const aggregate = leftKey && rightKey ? workbench.pairAggregateByKey.get(pairKeyOf(leftKey, rightKey)) : undefined;

  // The traced drill plates of exactly this pair (usually one) — identified by
  // shaping the sample's word, the same rule the pair cards and the editor
  // deep link use, so a drill can never attach to a different join than the
  // one its card links to.
  const drillRows = useMemo(() => {
    if (!leftKey || !rightKey) return [];
    return workbench.wordRows.filter((row) => {
      if (row.kind !== 'pair' || !workbench.sampleById.has(row.specimen_id)) return false;
      const keys = pairKeysOfText(row.word);
      return keys !== null && keys[0] === leftKey && keys[1] === rightKey;
    });
  }, [workbench.wordRows, workbench.sampleById, leftKey, rightKey]);

  // Layers over the drill specimen — the Wörter detail's switches, but BOTH on
  // by default: this panel exists precisely for trace vs. engine.
  const [drillTrace, setDrillTrace] = useState(true);
  const [drillEngine, setDrillEngine] = useState(true);

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

  // What ‹ › walks. The published order is the matrix as the reader last saw it
  // — both grids, its filter, its sort. The fallback is the registry one: the
  // anchor letter joined to every authored lowercase letter, which is exactly
  // the „{anchor} als erster Buchstabe" grid in alphabet order.
  const joinKey = leftKey && rightKey ? `${leftKey}→${rightKey}` : '';
  const registryJoins = useMemo(() => {
    if (!leftKey) return [];
    const authored = authoredLetters(LETTERS, (key) => glyphsByKey[key]?.has_data === true);
    return authored.lower.map((letter) => `${leftKey}→${glyphKeyFor(letter)}`);
  }, [leftKey, glyphsByKey]);
  const order = stepOrder(published, 'join', joinKey, {
    keys: registryJoins,
    caption: orderCaption(de.admin.liste.orderRegistry, false),
  });
  const { prev, next } = neighboursInOrder(order.keys, joinKey);
  // A step is a pair, and `focus` merges the query — so the list state and the
  // scope's `h=` survive it, exactly as a click on the matrix does.
  const stepJoin = (key: string) => {
    const [left, right] = key.split('→');
    if (left && right) focus(left, right);
  };

  const picker = (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
      {/* Both pickers grow to the §9.3 floor: they are the subject of the whole
          view and stood 32 px tall, and two invisible hit areas 8 px apart
          would overlap. */}
      <LetterPicker activeKey={leftKey} onPick={(key) => focus(key, rightKey ?? key)}>
        {(open) => (
          <Chip
            clickable
            onClick={open}
            aria-label={leftKey ? fmt(t.pickLeftChosen, { glyph: textForKey(leftKey) }) : t.pickLeftEmpty}
            sx={{ height: TOUCH_TARGET, minWidth: TOUCH_TARGET }}
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
            aria-label={rightKey ? fmt(t.pickRightChosen, { glyph: textForKey(rightKey) }) : t.pickRightEmpty}
            sx={{ height: TOUCH_TARGET, minWidth: TOUCH_TARGET }}
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
      <Button size="small" variant="outlined" sx={{ mt: 0.5, minHeight: TOUCH_TARGET }} onClick={submitFreeText}>
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
        {/* The anchor letter comes from the RAW `l=`, not from `readJoinFocus`:
            that reader nulls a half-given pair (which is right — half a pair is
            no join), and passing its result here is what made „Alle
            Kombinationen ansehen" open on whatever letter came first. */}
        <PairMatrix activeGlyphKey={params.get(FOCUS_PARAMS.left)} onPickPair={focus} refreshKey={pairTick} />

        {/* The Abb.-20 letter-pair plates: the only specimens that are pure
            JOINS, so they belong under Übergänge rather than with the words.
            They carry the „Gemessen" chips of the H2 layer and the editor deep
            link, which is why the whole card list is reused as-is. */}
        <Box sx={{ mt: 4 }}>
          <Button size="small" sx={{ minHeight: TOUCH_TARGET }} onClick={() => setSpecimensOpen((v) => !v)}>
            {specimensOpen ? t.hideSpecimens : t.showSpecimens}
          </Button>
          <Collapse in={specimensOpen} unmountOnExit>
            <Box sx={{ mt: 2 }}>
              <WordComparison
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
        titleText={fmt(t.joinHeading, { left: leftKey, right: rightKey })}
        note={order.caption}
        title={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            {/* New in the keyboard round: this head had no stepper at all, so
                „die nächste Verbindung" meant going back to the matrix and
                finding the next cell by eye. */}
            <SubjectStepper
              prev={prev}
              next={next}
              onStep={stepJoin}
              prevLabel={t.prevJoin}
              nextLabel={t.nextJoin}
              between={picker}
            />
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
        <Button size="small" onClick={toOverview}>
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
          {/* The view invites typing any pair, including ones no plate ever
              wrote — so an uncreated letter is a NORMAL outcome here, not a
              fault. WrittenWord renders null on empty items, which left a mute
              white box; the API knew all along and says so in `missing`. Both
              letters missing gets a full sentence, one gets the same chip the
              word cards already carry. */}
          {missing.length > 0 && (
            <Box sx={{ mb: 1.5 }}>
              {missing.length >= 2 ? (
                <Alert severity="info">{t.writtenNoneCreated}</Alert>
              ) : (
                <Chip
                  size="small"
                  color="warning"
                  label={`${de.admin.compare.missingPrefix}${missing.join(', ')}`}
                />
              )}
            </Box>
          )}
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
              onResolved={({ missing: keys }) => setMissingFor({ text: pairText, keys })}
            />
          </Box>
          {/* The two letters first — checking whether the fault is already in
              one of them is the earlier stage of the triage. The editor comes
              last and quietly (a `text` button under the doctrine line): the
              layout must not make the last resort look like the first move. */}
          {/* The floor on the row, not on each button: the two stand one gap
              apart, so they grow rather than overlay (§9.3). */}
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1.5, '& > *': { minHeight: TOUCH_TARGET } }}>
            <Button size="small" variant="outlined" onClick={() => navigate(lettersUrl(leftKey, ownHand))}>
              {fmt(t.toLetter, { key: leftKey })}
            </Button>
            <Button size="small" variant="outlined" onClick={() => navigate(lettersUrl(rightKey, ownHand))}>
              {fmt(t.toLetter, { key: rightKey })}
            </Button>
          </Box>
          <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mt: 1.5 }}>
            {t.overrideLastResort}
          </Typography>
          <Button size="small" sx={{ mt: 0.5, px: 0.5, minHeight: TOUCH_TARGET }} onClick={() => setEditorOpen(true)}>
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

        {/* 2b — the drill plate of exactly this pair, wherever one was traced:
            the same evidence card the Wörter view shows, so the traced Spur
            and the engine's ink meet the specimen HERE, not two clicks away. */}
        {drillRows.length > 0 && (
          <Box sx={{ gridColumn: '1 / -1' }}>
            <Panel
              title={t.drillTitle}
              caption={t.drillCaption}
              actions={
                <ToggleButtonGroup
                  size="small"
                  value={[...(drillTrace ? ['trace'] : []), ...(drillEngine ? ['engine'] : [])]}
                  onChange={(_e, next: string[]) => {
                    setDrillTrace(next.includes('trace'));
                    setDrillEngine(next.includes('engine'));
                  }}
                  aria-label={de.admin.werkbank.layersLabel}
                >
                  {/* The theme lifts a `small` ToggleButton only below `sm`;
                      at desktop and tablet width it is ~39 px (§9.3). */}
                  <ToggleButton value="trace" sx={{ minHeight: TOUCH_TARGET }}>
                    <LayerDot color={layer.trace} style={layerDash.trace} />
                    {de.admin.werkbank.layerTrace}
                  </ToggleButton>
                  <ToggleButton value="engine" sx={{ minHeight: TOUCH_TARGET }}>
                    <LayerDot color={layer.engine} style={layerDash.engine} />
                    {de.admin.werkbank.layerEngine}
                  </ToggleButton>
                </ToggleButtonGroup>
              }
            >
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {drillRows.map((row) => {
                  const sample = workbench.sampleById.get(row.specimen_id);
                  if (!sample) return null;
                  return (
                    <DrillSpecimenCard
                      // Keyed on the save counter: an override save must reset
                      // the card (fresh composition via `bust`, stale score
                      // dropped) rather than keep judging the old join.
                      key={`${row.kind}:${row.specimen_id}:${pairTick}`}
                      row={row}
                      sample={sample}
                      sourceId={sourceId}
                      bust={pairTick}
                      overlay={drillEngine}
                      showTrace={drillTrace}
                      boxes={workbench.boxesBySpecimen.get(row.specimen_id) ?? []}
                      onOpenLetter={(key) => navigate(lettersUrl(key, ownHand))}
                      onOpenPair={focus}
                      onMark={fileMark}
                      onOpenWord={() => navigate(wordsUrl(row.word, row.specimen_id, ownHand))}
                    />
                  );
                })}
              </Box>
            </Panel>
          </Box>
        )}

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
                    onJump={() => navigate(wordsUrl(sample.word, occ.specimen_id, ownHand))}
                    label={occ.specimen_id}
                    detail={
                      occ.measurements.gen_chamfer === undefined
                        ? undefined
                        : fmt(de.admin.werkbank.genChamferShort, {
                            value: occ.measurements.gen_chamfer.toFixed(3),
                          })
                    }
                    note={
                      // A doubtful fit is an error statement in TEXT, so it takes the theme's
                      // error red (Ochsenblut, 8.41:1 on the card) rather than the raw Zinnober
                      // it used to borrow from the overlay map, which reached 3.38:1 and is now
                      // the engine layer's own colour.
                      occ.measurements.fit_ok === false ? (
                        <Typography variant="caption" sx={{ color: 'error.main', lineHeight: 1.2 }}>
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
                        onClick={() => navigate(wordsUrl(sample?.word ?? '', occ.specimen_id, ownHand))}
                      />
                      {occ.measurements.gen_chamfer !== undefined && (
                        <Typography variant="caption" color="text.secondary">
                          {fmt(de.admin.werkbank.genChamfer, { value: occ.measurements.gen_chamfer.toFixed(3) })}
                        </Typography>
                      )}
                      {occ.measurements.fit_ok === false && (
                        <Typography variant="caption" sx={{ color: 'error.main' }}>
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
                  onClick={() => navigate(wordsUrl(w.word, w.specimenId, ownHand))}
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
        <Button size="small" sx={{ minHeight: TOUCH_TARGET }} onClick={() => setMatrixOpen((v) => !v)}>
          {matrixOpen ? t.hideMatrix : t.showMatrix}
        </Button>
        <Collapse in={matrixOpen} unmountOnExit>
          <Box sx={{ mt: 2 }}>
            <Box sx={{ mb: 1 }}>{freeInput}</Box>
            {/* `embedded`: this is a sub-block of the DETAIL, so it keeps the
                composed cells, picks its anchor in its own state and leaves the
                URL alone — inheriting the overview's chips would silently hide
                cells from a cross-check that was opened to see all of them. */}
            <PairMatrix activeGlyphKey={leftKey} onPickPair={focus} refreshKey={pairTick} embedded />
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
