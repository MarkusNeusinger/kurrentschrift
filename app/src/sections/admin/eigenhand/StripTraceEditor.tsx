// Der Streifen-Editor — the surface the whole Phase-2 slice was built toward:
// where the author draws a Bahn by hand over his own writing.
//
// A SECOND, slim editor beside the plate one (author decision G, 2026-09-20),
// sharing its building blocks rather than its code path: the drawing surface is
// `shell/TraceCanvas`, the registration maths `belege/registration.ts`, and the
// tested plate write flow is not touched at all. Three things differ, and they
// are the whole reason this exists rather than a props seam on the plate
// dialog:
//
//  1. THE UNDERLAY IS A BLOB. The strip crop route is admin-gated and
//     `private, no-store`, so a bare `<image href>` — which is what the plate
//     editor can use, because the specimen crop route is deliberately public —
//     cannot load it. The strip surface already fetches its pixels as blobs
//     (`useStripImage`), and this reuses exactly that loader. A blob is also a
//     second read that can be SLOW or fail, so the picture gates the surface:
//     no canvas until this box's crop is under it.
//  2. THE FRAME IS THE BAHN'S, MINUS THE BOX. A Streifen-Pfad's registration is
//     the STRIP's frame; the editor works on the word crop, so the box
//     rectangle comes off (`stripTraceFrame`). A box with no Bahn at all falls
//     back to the printed ruling and SAYS so — „Saat", never a measurement.
//  3. „SPEICHERN & WEITER" walks the Nachfahr-Liste's current order without
//     leaving the surface. The per-box write answers with the whole list AND
//     the next `ETag` (#642), so two boxes of one Fassung cost one read.
//
// Two things it refuses to do, both deliberate:
//  * It never offers „kein Pfad hier". A per-box write cannot store a
//    Skip-Eintrag — `check_paths` refuses `status: skipped` together with the
//    `authored` this route stamps — so a button for it would be a 422 with a
//    friendly label.
//  * It never re-stamps a boundary the author did not move. `herkunft:
//    'authored'` survives every later re-follow, so claiming it for the
//    follower's own guess would freeze that guess as ground truth and feed it
//    to the Span-Zuordner as training material.

import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Slider,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useRef, useState, type Dispatch, type SetStateAction } from 'react';

import { InfoHint } from '@/components/InfoHint';
import { getEigenhandPfadeWithEtag, patchEigenhandPfad } from '@/lib/api';
import type { EigenhandPfadList, EigenhandPfadSpan } from '@/lib/api';
import { shapeText } from '@/domain/shaping';
import { de, fmt } from '@/locales/admin';
import { cropToTrace, sanitizeStrokes, type TracePoint } from '@/sections/admin/belege/registration';
import { LetterSpanLayer } from '@/sections/admin/eigenhand/LetterSpanLayer';
import {
  advanceDrawing,
  moveBoundary,
  nearestSample,
  savableStrokeIds,
  seedDrawing,
  seedStrokeIds,
  spansStillFit,
  seamAt,
  seamsOf,
  authoredSpanCount,
  type Drawing,
  type SpanSeam,
} from '@/sections/admin/eigenhand/letterSpans';
import { stripRegistration, stripTraceSeed, type StripTraceSeed } from '@/sections/admin/eigenhand/stripTraceFrame';
import type { StripTraceTarget } from '@/sections/admin/eigenhand/stripBoxRows';
import { useStripImage } from '@/sections/admin/eigenhand/useStripImage';
import { apiErrorText, type ApiErrorText } from '@/sections/admin/shell/apiErrorText';
import { ErrorText } from '@/sections/admin/shell/ErrorText';
import { TraceCanvas, type PointPhase, type TraceMode } from '@/sections/admin/shell/TraceCanvas';
import { TOUCH_TARGET } from '@/styles/hitArea';
import { garamond, paper } from '@/styles/paper';

// Anpassen falloff radius (x-height units) — the plate editor's range, because
// it is the same hand with the same pen on the same tablet.
const NUDGE_DEFAULT_XH = 0.25;
const NUDGE_MIN_XH = 0.1;
const NUDGE_MAX_XH = 0.8;

// How close the pen has to come to a boundary handle to take it, in x-heights.
// Wide enough for a finger-sized pen target at a small zoom, far below the
// width of a letter, so the grab is never ambiguous between two seams.
const SEAM_GRAB_XH = 0.8;

const MODE_BUTTON_SX = { minWidth: TOUCH_TARGET, minHeight: TOUCH_TARGET, textTransform: 'none' } as const;

// The strip's own printed rulings are lifted to paper by default: what is
// being traced is the hand, and the cyan ruling under the ink is the print.
// The frame the Bahn is stored in is drawn by the canvas itself.
const OHNE_LINEATUR = true;

/** The day the Bahn was drawn, in the writer's own timezone — `erzeugt_am` is a
 * calendar date, and a UTC slice would date an evening session to the day
 * before for anyone east of Greenwich. */
function today(): string {
  const now = new Date();
  const pad = (value: number): string => String(value).padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

type Held = {
  /** `strip/fassung` — which Fassung's list is in hand. */
  fassungKey: string;
  list: EigenhandPfadList;
  /** The token the next write echoes; null where an intermediary dropped it. */
  etag: string | null;
  /** Bumped only where the drawing should be RE-SEEDED from this list — after
   * a save, never after the re-read a conflict asks for (which must leave the
   * author's unsaved line standing). */
  stamp: number;
};

export function StripTraceEditor({
  open,
  hand,
  targets,
  startKey,
  onClose,
  onSaved,
}: {
  open: boolean;
  hand: string;
  /** The boxes to walk, in the order the list shows them. */
  targets: readonly StripTraceTarget[];
  /** Which of them the author opened. */
  startKey: string;
  onClose: () => void;
  /** After a stored box, so the list's Ampel and the gallery re-read. */
  onSaved: (key: string) => void;
}) {
  const t = de.admin.eigenhand.editor;
  const [cursor, setCursor] = useState(() => {
    const found = targets.findIndex((candidate) => candidate.key === startKey);
    return found < 0 ? 0 : found;
  });
  const target = targets[cursor] ?? null;
  const fassungKey = target ? `${target.strip}/${target.fassung}` : '';

  const [held, setHeld] = useState<Held | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<ApiErrorText | null>(null);
  const stampRef = useRef(0);
  // The boundary drag in flight: the seam under the pen and the spans it
  // started from (see `onPoint`).
  const grabRef = useRef<{ seam: SpanSeam; snapshot: readonly EigenhandPfadSpan[] } | null>(null);

  // The drawing carries one id per run beside the coordinates: a letter
  // boundary names a run by its INDEX, and an index alone cannot tell an
  // Anpassen-warped run from one that was undone and drawn again.
  const [drawing, setDrawing] = useState<Drawing>(() => seedDrawing([]));
  const strokes = drawing.strokes;
  // The canvas knows nothing of the ids — it hands back coordinates, and the
  // lineage is carried across here, in ONE state so the update stays pure.
  const setStrokes: Dispatch<SetStateAction<TracePoint[][]>> = (action) =>
    setDrawing((prev) =>
      advanceDrawing(prev, typeof action === 'function' ? action(prev.strokes) : action),
    );
  const [spans, setSpans] = useState<readonly EigenhandPfadSpan[] | null>(null);
  const [dirty, setDirty] = useState(false);
  const [mode, setMode] = useState<TraceMode>('draw');
  const [zoom, setZoom] = useState(0.5);
  const [nudgeRadius, setNudgeRadius] = useState(NUDGE_DEFAULT_XH);
  const [showStored, setShowStored] = useState(true);
  const [grabbed, setGrabbed] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<ApiErrorText | null>(null);
  // Told apart on purpose: a 412 is not a failure of the save but a statement
  // about the list it was made on, and the answer to it is a re-read, not a
  // retry.
  const [conflict, setConflict] = useState<'stale' | 'token' | null>(null);
  const [askDiscard, setAskDiscard] = useState(false);

  // The Fassung this render wants in hand. The reset lives in RENDER (React's
  // "adjusting state when a prop changes"), so the spinner is up from the first
  // frame instead of one frame late.
  const wantKey = open && target ? fassungKey : '';
  const [loadingFor, setLoadingFor] = useState(wantKey);
  const holdsIt = held !== null && held.fassungKey === wantKey;
  if (loadingFor !== wantKey) {
    setLoadingFor(wantKey);
    setLoading(wantKey !== '' && !holdsIt);
    setLoadError(null);
  }

  useEffect(() => {
    if (wantKey === '' || !target) return undefined;
    // Already in hand: the per-box write answers with the whole list and the
    // NEXT token, so walking to another box of the same Fassung costs nothing.
    if (held !== null && held.fassungKey === wantKey) return undefined;
    let cancelled = false;
    getEigenhandPfadeWithEtag(hand, target.strip, target.fassung, { retries: 2 })
      .then(({ list, etag }) => {
        if (cancelled) return;
        stampRef.current += 1;
        setHeld({ fassungKey: wantKey, list, etag, stamp: stampRef.current });
      })
      .catch((err: unknown) => !cancelled && setLoadError(apiErrorText(err)))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
    // `held` is read, not depended on: adding it would re-run the effect with
    // the very list it just stored. The Fassung key is what decides.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wantKey, hand, target?.strip, target?.fassung]);

  const listFor = held !== null && held.fassungKey === fassungKey ? held : null;
  const fresh = useMemo(
    () => (listFor && target ? stripTraceSeed(listFor.list, target.boxIndex) : null),
    [listFor, target],
  );
  const seedKey = fresh && target && listFor ? `${target.key}|${listFor.stamp}` : null;
  const [seededFor, setSeededFor] = useState<string | null>(null);
  // The seed is FROZEN into state, not read live off the list: the drawing and
  // the frame it was drawn in have to stay one thing. A conflict re-read keeps
  // the stamp (so the line survives it) but delivers whatever the other writer
  // stored — a re-follow's own registration — and a live frame would then put
  // the author's coordinates into a stranger's frame, which the next save
  // writes out as a Bahn lying beside the ink.
  const [seed, setSeed] = useState<StripTraceSeed | null>(null);
  if (seedKey !== seededFor) {
    setSeededFor(seedKey);
    setSeed(fresh);
    setDrawing(seedDrawing(fresh ? fresh.strokes : []));
    setSpans(fresh ? fresh.spans : null);
    setDirty(false);
    setSaveError(null);
    setConflict(null);
    setGrabbed(null);
  }

  const {
    url,
    loading: imageLoading,
    error: imageError,
  } = useStripImage(
    hand,
    target?.strip ?? '',
    target?.fassung ?? '',
    target?.boxIndex ?? null,
    open && seed !== null,
    OHNE_LINEATUR,
  );
  // The picture is a CONDITION of the surface, not decoration on it. `url`
  // alone would not do: the hook clears the previous box's object URL in its
  // effect cleanup, which runs AFTER the render that walked to the next box —
  // so for one frame a ready-looking canvas would carry the neighbour's
  // picture. `loading` is set during that very render, and a fetch that fails
  // never leaves it. Drawing over a blank or a stranger's crop is worse than
  // no editor: the Bahn would be stored against ink it was never drawn on.
  const underlayReady = url !== null && !imageLoading;

  const savable = useMemo(() => sanitizeStrokes(strokes), [strokes]);
  const slotText = useMemo(() => {
    const slots = target ? shapeText(target.word) : [];
    return (slot: number): string => slots[slot]?.text ?? '';
  }, [target]);
  // The boundaries describe the samples of the run they sit on, so a REDRAWN
  // run gives up the boundaries that sat on it — but only those: a run drawn
  // BESIDE them (what the Absetzer warning asks for when a mark stroke is
  // missing) shifts no index, and giving the author's own corrected seams up
  // over it would delete ground truth. Asked of the ids of the runs a save
  // would SEND, because dropping a stray tap renumbers the rest.
  const seedIds = useMemo(() => seedStrokeIds(seed?.strokes.length ?? 0), [seed]);
  const sendIds = useMemo(() => savableStrokeIds(drawing), [drawing]);
  const spansHold = spans !== null && seed !== null && spansStillFit(seedIds, sendIds, spans);
  const seams = useMemo(() => (spansHold ? seamsOf(spans) : []), [spans, spansHold]);
  const effectiveMode: TraceMode = mode === 'point' && seams.length === 0 ? 'draw' : mode;
  const absetzerOk = target !== null && savable.length === target.absetzerSoll;

  const onPoint = (point: TracePoint, phase: PointPhase) => {
    if (!seed || spans === null) return;
    const trace = cropToTrace(seed.reg, point);
    if (phase === 'down') {
      const index = seamAt(seams, strokes, trace, SEAM_GRAB_XH);
      // The grabbed seam and the boundaries it started from live in a REF, the
      // way the plate editor keeps its nudge: pointer moves arrive faster than
      // React commits, so a drag that read them out of state would work on a
      // render that has not happened yet — measured as a drag that moved
      // nothing at all (2026-09-20, the tablet viewport). The snapshot also
      // makes every move idempotent: each one re-derives from the SAME spans,
      // so the boundary follows the pen instead of walking with it.
      grabRef.current = index === null ? null : { seam: seams[index], snapshot: spans };
      setGrabbed(index);
      return;
    }
    const grab = grabRef.current;
    if (phase === 'up') {
      grabRef.current = null;
      setGrabbed(null);
      return;
    }
    if (!grab) return;
    const stroke = strokes[grab.seam.stroke];
    if (!stroke) return;
    const moved = moveBoundary(grab.snapshot, grab.seam, nearestSample(stroke, trace, grab.seam.min, grab.seam.max));
    // By identity where the boundary did not move — a tap must not stamp the
    // follower's own assignment as the author's.
    if (moved !== grab.snapshot) {
      setSpans(moved);
      setDirty(true);
    }
  };

  const reread = () => {
    if (!target) return;
    getEigenhandPfadeWithEtag(hand, target.strip, target.fassung, { retries: 1 })
      .then(({ list, etag }) => {
        // The SAME stamp on purpose: this re-read exists to refresh the token a
        // save is made against, and re-seeding here would throw away the very
        // drawing the conflict interrupted.
        setHeld({ fassungKey: `${target.strip}/${target.fassung}`, list, etag, stamp: stampRef.current });
        setConflict(null);
      })
      .catch((err: unknown) => setLoadError(apiErrorText(err)));
  };

  const save = async (advance: boolean) => {
    if (!target || !seed || !listFor || savable.length === 0) return;
    if (!listFor.etag) {
      setConflict('token');
      return;
    }
    setSaving(true);
    setSaveError(null);
    try {
      const { list, etag } = await patchEigenhandPfad(
        hand,
        target.strip,
        target.fassung,
        target.boxIndex,
        {
          box_index: target.boxIndex,
          word: target.word,
          // `null`, never `'ok'`: format 2 reads a missing status as „ok" and
          // format 1 refuses the field outright, so one body serves both.
          status: null,
          grund: null,
          detail: null,
          strokes: savable,
          // Resent with the strokes they were drawn on, or given up with them:
          // the per-box write replaces the entry whole (`write_pfad_box`), so
          // leaving them out loses the ones the author corrected.
          letter_spans: spansHold && spans ? [...spans] : null,
          registration_px: stripRegistration(seed.reg, seed.rect),
          xh_px: seed.reg.xh,
          konfiguration: {},
          // Deliberately empty, and this is the one field where that matters:
          // `meta.tintenpfad` holds the sensors the FOLLOWER measured on the
          // Bahn this save replaces. Carrying them over would give a fresh
          // hand-drawn line a verdict measured on a line that no longer
          // exists; without them the Ampel greys the box as „von Hand
          // gezeichnet", which is what it is until the tool has run over it.
          meta: {},
          erzeugt_am: today(),
          // Null, not the Fassung's mask size: „Maske geändert" says a
          // FOLLOWER's numbers describe other ink than the picture now shows.
          // A drawing carries no numbers, and the author drew what he saw.
          flecken_n: null,
        },
        listFor.etag,
        // The ROW's own format, never the constant this bundle knows: a
        // format-1 row answers 409 to anything else.
        listFor.list.format,
      );
      stampRef.current += 1;
      setHeld({ fassungKey: listFor.fassungKey, list, etag, stamp: stampRef.current });
      onSaved(target.key);
      if (advance && cursor + 1 < targets.length) setCursor(cursor + 1);
    } catch (err: unknown) {
      const text = apiErrorText(err);
      if (text.status === 412) setConflict('stale');
      else setSaveError(text);
    } finally {
      setSaving(false);
    }
  };

  const canSave = Boolean(target && seed && listFor && savable.length > 0 && dirty && !saving);
  const hasNext = cursor + 1 < targets.length;

  // A hand-drawn Bahn exists nowhere else until it is stored — no follower run
  // recreates it — so the surface that creates it does not let a stray Escape
  // or a mis-hit „Schließen" take it silently. The plate editor has the same
  // gap; carrying the guard over there is its own change.
  const leave = () => (dirty ? setAskDiscard(true) : onClose());

  // Full screen with every control ABOVE the drawing surface, and the paper
  // suppressing selection and the context menu — the plate editor's two tablet
  // findings, which hold for the same hand on the same device.
  return (
    <Dialog
      open={open}
      onClose={leave}
      fullScreen
      // Not `disableEscapeKeyDown`: Escape should still be the way out, it just
      // has to ask first, and MUI routes the key through `onClose` — so the
      // guard sits in `leave` and covers the button and the key alike.
      slotProps={{
        paper: {
          sx: { userSelect: 'none' },
          onContextMenu: (e: React.MouseEvent) => e.preventDefault(),
        },
      }}
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', py: 1 }}>
        <Typography component="span" sx={{ fontFamily: garamond, fontSize: 24, lineHeight: 1 }}>
          {target?.word ?? ''}
        </Typography>
        <Typography component="span" variant="body2" color="textSecondary">
          {target
            ? fmt(t.place, { strip: target.strip, fassung: target.fassung, nr: target.boxIndex })
            : t.empty}
        </Typography>
        <Typography component="span" variant="caption" color="textSecondary">
          {fmt(t.queue, { nr: cursor + 1, total: targets.length })}
        </Typography>
        <InfoHint title={t.title} label={t.introAria}>
          <Typography variant="body2">{t.intro}</Typography>
        </InfoHint>
        {/* Prüfstein 7, beside the Bahn and not behind a hint: the drawn runs
            against the runs the SCRIPT writes this word in. */}
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center', ml: 'auto' }}>
          <Chip
            size="small"
            color={absetzerOk ? 'success' : 'warning'}
            variant={absetzerOk ? 'filled' : 'outlined'}
            label={`${fmt(t.strokeCount, { zuege: savable.length })} · ${fmt(t.absetzerSoll, {
              soll: target?.absetzerSoll ?? 0,
            })}`}
            sx={{ flexShrink: 0 }}
          />
          <Button size="small" onClick={leave} disabled={saving} sx={{ minHeight: TOUCH_TARGET }}>
            {t.close}
          </Button>
          <Button
            size="small"
            variant="outlined"
            onClick={() => void save(false)}
            disabled={!canSave}
            sx={{ minHeight: TOUCH_TARGET }}
          >
            {t.save}
          </Button>
          <Button
            size="small"
            variant="contained"
            onClick={() => void save(true)}
            disabled={!canSave || !hasNext}
            sx={{ minHeight: TOUCH_TARGET }}
          >
            {t.saveNext}
          </Button>
        </Stack>
      </DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', minHeight: 0, pb: 1 }}>
        <Box sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center', flexWrap: 'wrap' }}>
          <ToggleButtonGroup
            size="small"
            exclusive
            aria-label={t.modeGroup}
            value={effectiveMode}
            onChange={(_, next: TraceMode | null) => {
              if (next === null) return;
              setMode(next);
              // A mode change ends a boundary drag too — the canvas drops its
              // own gesture state, and a grabbed seam left behind here would
              // stay highlighted and move on the next stray sample.
              grabRef.current = null;
              setGrabbed(null);
            }}
          >
            {/* The 44 px floor on a surface that is operated with a finger
                beside the pen (§9.3). A group's buttons touch, so they grow in
                both edges rather than overlapping each other's hit areas. */}
            <ToggleButton value="draw" sx={MODE_BUTTON_SX}>
              {t.modeDraw}
            </ToggleButton>
            <ToggleButton value="adjust" sx={MODE_BUTTON_SX}>
              {t.modeAdjust}
            </ToggleButton>
            {/* „Grenzen" is the canvas's neutral `point` mode: the editor
                interprets the pen, the canvas stays the one place that knows
                about pointers. Disabled where there is nothing to move. */}
            <ToggleButton value="point" disabled={seams.length === 0} sx={MODE_BUTTON_SX}>
              {t.modeSpans}
            </ToggleButton>
            <ToggleButton value="pan" sx={MODE_BUTTON_SX}>
              {t.modePan}
            </ToggleButton>
          </ToggleButtonGroup>
          {effectiveMode === 'adjust' && (
            <>
              <Typography variant="caption" color="textSecondary" sx={{ minWidth: 88 }}>
                {t.nudgeRadius} {nudgeRadius.toLocaleString('de-DE', { maximumFractionDigits: 2 })}
              </Typography>
              <Slider
                size="small"
                value={nudgeRadius}
                min={NUDGE_MIN_XH}
                max={NUDGE_MAX_XH}
                step={0.05}
                onChange={(_, v) => setNudgeRadius(Math.round((v as number) * 20) / 20)}
                aria-label={t.nudgeRadius}
                sx={{ width: 140, flexShrink: 0, mx: 1 }}
              />
            </>
          )}
          <Typography variant="caption" color="textSecondary" sx={{ minWidth: 74 }}>
            {t.zoom} {zoom.toLocaleString('de-DE', { maximumFractionDigits: 2 })}×
          </Typography>
          <Slider
            size="small"
            value={zoom}
            min={0.1}
            max={2}
            step={0.05}
            // Snapped to the 0.05 grid: MUI accumulates min + k·step in floats.
            onChange={(_, v) => setZoom(Math.round((v as number) * 20) / 20)}
            aria-label={t.zoom}
            sx={{ width: 200, flexShrink: 0, mx: 1 }}
          />
          {/* The 44 px floor holds for these three too (§9.3): they sit on the
              same pen surface as the mode group, and „Alle Züge löschen" next
              to „Letzten Zug zurück" is the pair a mis-hit costs most. */}
          <Button
            size="small"
            sx={{ minHeight: TOUCH_TARGET }}
            onClick={() => {
              setStrokes((prev) => prev.slice(0, -1));
              setDirty(true);
            }}
            disabled={strokes.length === 0}
          >
            {t.undo}
          </Button>
          <Button
            size="small"
            sx={{ minHeight: TOUCH_TARGET }}
            onClick={() => {
              setStrokes([]);
              setDirty(true);
            }}
            disabled={strokes.length === 0}
          >
            {t.clear}
          </Button>
          <Button
            size="small"
            sx={{ minHeight: TOUCH_TARGET }}
            onClick={() => {
              if (!seed) return;
              // The seeded LINEAGE, not just the seeded coordinates: routed
              // through the tracker, a run restored where an undone one stood
              // would come back as a new one and take the boundaries with it.
              setDrawing(seedDrawing(seed.strokes));
              setSpans(seed.spans);
              setDirty(false);
            }}
            disabled={!dirty || !seed}
          >
            {t.reset}
          </Button>
          <FormControlLabel
            sx={{ mr: 0 }}
            control={<Checkbox size="small" checked={showStored} onChange={(e) => setShowStored(e.target.checked)} />}
            label={<Typography variant="caption">{t.showStored}</Typography>}
          />
          {/* Only while they would actually be SENT: a count standing over the
              „…werden nicht mitgeschickt" notice contradicts it. */}
          {spansHold && spans !== null && (
            <Typography variant="caption" color="textSecondary">
              {`${fmt(t.spansCount, { zahl: spans.length })} · ${fmt(t.spansAuthored, {
                zahl: authoredSpanCount(spans),
              })}`}
            </Typography>
          )}
          <Typography variant="caption" color="textSecondary">
            {effectiveMode === 'adjust' ? t.adjustHint : effectiveMode === 'point' ? t.spansHint : t.drawHint}
          </Typography>
        </Box>

        {!absetzerOk && target && (
          <Alert severity="warning" sx={{ mb: 1 }}>
            {fmt(t.absetzerMismatch, { zuege: savable.length, soll: target.absetzerSoll })}
          </Alert>
        )}
        {conflict !== null && (
          <Alert
            severity="error"
            sx={{ mb: 1 }}
            action={
              <Button color="inherit" size="small" onClick={reread} sx={{ minHeight: TOUCH_TARGET }}>
                {t.conflictAction}
              </Button>
            }
          >
            {conflict === 'stale' ? t.conflict : t.noToken}
          </Alert>
        )}
        {saveError && (
          <Alert severity="error" sx={{ mb: 1 }}>
            <ErrorText error={saveError} prefix={t.saveError} />
          </Alert>
        )}
        {loadError && (
          <Alert severity="warning" sx={{ mb: 1 }}>
            <ErrorText error={loadError} prefix={t.loadError} />
          </Alert>
        )}
        {imageError && (
          <Alert severity="warning" sx={{ mb: 1 }}>
            <ErrorText error={imageError} prefix={t.imageError} />
          </Alert>
        )}
        {seed?.herkunft === 'saat' && (
          <Alert severity="info" sx={{ mb: 1 }}>
            {t.saat}
          </Alert>
        )}
        {spans !== null && !spansHold && (
          <Alert severity="info" sx={{ mb: 1 }}>
            {t.spansDropped}
          </Alert>
        )}
        {spans === null && effectiveMode === 'draw' && seed?.herkunft === 'bahn' && (
          <Typography variant="caption" sx={{ display: 'block', mb: 1, color: paper.inkSoft }}>
            {t.spansNone}
          </Typography>
        )}
        {!hasNext && (
          <Typography variant="caption" sx={{ display: 'block', mb: 1, color: paper.inkSoft }}>
            {t.saveLast}
          </Typography>
        )}

        {loading && <CircularProgress size={20} aria-label={t.loading} />}
        {!loading && listFor && seed === null && (
          <Alert severity="warning" sx={{ mb: 1 }}>
            {t.noGeometry}
          </Alert>
        )}
        {/* No canvas until THIS box's picture is under it — see `underlayReady`.
            The spinner says which of the two reads is still out. */}
        {seed && !underlayReady && !imageError && <CircularProgress size={20} aria-label={t.imageLoading} />}
        {seed && underlayReady && (
          <TraceCanvas
            width={seed.width}
            height={seed.height}
            reg={seed.reg}
            strokes={strokes}
            onStrokes={setStrokes}
            onDirty={() => setDirty(true)}
            mode={effectiveMode}
            zoom={zoom}
            nudgeRadius={nudgeRadius}
            ghost={showStored && dirty ? seed.strokes : null}
            onPoint={onPoint}
            underlay={
              <image href={url} x={0} y={0} width={seed.width} height={seed.height} preserveAspectRatio="none" />
            }
            overlayNode={
              spansHold && spans !== null && spans.length > 0 ? (
                <LetterSpanLayer
                  spans={spans}
                  strokes={strokes}
                  reg={seed.reg}
                  seams={seams}
                  grabbed={grabbed}
                  labelOf={slotText}
                />
              ) : undefined
            }
          />
        )}
      </DialogContent>
      <Dialog open={askDiscard} onClose={() => setAskDiscard(false)}>
        <DialogTitle>{t.discardTitle}</DialogTitle>
        <DialogContent>
          <Typography variant="body2">{t.discardBody}</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAskDiscard(false)} sx={{ minHeight: TOUCH_TARGET }}>
            {t.discardStay}
          </Button>
          <Button
            color="warning"
            variant="contained"
            onClick={() => {
              setAskDiscard(false);
              onClose();
            }}
            sx={{ minHeight: TOUCH_TARGET }}
          >
            {t.discardLeave}
          </Button>
        </DialogActions>
      </Dialog>
    </Dialog>
  );
}
