// Admin comparison view — every authored letter as FOUR faces side by side,
// which is the whole pipeline of one letter in one row:
//
//   Original          the unaltered chart crop — the goal
//   Tafel-Form        what the engine writes from the authored ductus (variant 0)
//   Laufform          what it writes inside running words (variant 100)
//   Median & Vorkommen the statistics both are judged against: the per-anchor
//                     median over every measured occurrence, the occurrence
//                     chains thin behind it, the currently rendered Laufform
//                     dashed against it
//
// Two faces used to be the whole story, which meant the derived stages — the
// running form and the measured median — were only ever visible one letter at a
// time in the detail view. The difference between the Tafel form and the
// Laufform is exactly what this grid is for.
//
// Beside them the key numbers (how many occurrences, how well they fit, the
// stored image-space score with its per-category deductions) — enough to see
// WHICH letter needs work; the details stay in the detail view and the Diagnose
// modal.
//
// Cost: the render payloads come from two batch requests for the whole
// alphabet (variant 0 and variant 100), the statistics from the shared
// workbench layer (no request at all) and the scores from ONE admin read of the
// stamped values. The expensive per-glyph /diagnostic is fetched lazily and
// ONLY for the overlay mode that actually needs its outline geometry.
//
// One tile per LETTER — one glyph_key, one authored form.

import RefreshIcon from '@mui/icons-material/Refresh';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  FormControlLabel,
  Switch,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { WrittenGlyph } from '@/components/WrittenGlyph';
import { useAdmin } from '@/context/AdminContext';
import { glyphKeyFor, LETTERS } from '@/domain/glyphs';
import { useInView } from '@/hooks/useInView';
import { ApiError, cropUrl, fetchRenderGlyphs, getDiagnostic, getTemplateQuality } from '@/lib/api';
import type { AggregateOut, DiagnosticData, InstanceOut, QualityData } from '@/lib/api';
import { ringsToPathD } from '@/lib/svg';
import { de, fmt } from '@/locales/admin';
import { ScoreBreakdownInline, ScoreChip } from '@/sections/admin/quality/scoreParts';
import { AggregateSketch } from '@/sections/admin/shell/AggregateSketch';
import { isPoint, letterSketchAnchors, occurrenceChainsOf } from '@/sections/admin/shell/sketchGeometry';
import { useWorkbench } from '@/sections/admin/shell/WorkbenchData';
import { garamond } from '@/styles/paper';

// px — four faces have to fit beside each other on a laptop, so each is about
// half the height the two-face row used. Still large enough to judge a ductus:
// the detail view's faces are 190.
const FACE_H = 170;
// The Laufform is stored as this template variant (core/database LAUFFORM_VARIANT).
const LAUFFORM_VARIANT = 100;
// The write endpoint takes at most 80 keys per request (api/routers/write.py);
// stay clear of the limit so a fully authored source (letters + digits +
// punctuation + ligatures) still prefetches in whole batches.
const PREFETCH_CHUNK = 60;

type SortMode = 'alpha' | 'worst';

interface Tile {
  key: string;
  letterGlyph: string;
}

function buildTiles(glyphsByKey: Record<string, { has_data: boolean }>): Tile[] {
  const tiles: Tile[] = [];
  for (const letter of LETTERS) {
    const key = glyphKeyFor(letter);
    if (glyphsByKey[key]?.has_data !== true) continue;
    tiles.push({ key, letterGlyph: letter.glyph });
  }
  return tiles;
}

// Mean fit residual over the stored occurrences of one letter — the public
// number that says how well the authored form actually sits in the plates'
// words. `null` where no occurrence carries one (an absent measurement is
// never printed as a measured zero).
function meanRmse(occurrences: InstanceOut[]): number | null {
  // `!== undefined` is not enough: the measurement comes from JSONB, so a
  // stored null would pass that test and be summed as a measured 0.
  const values = occurrences
    .map((o) => o.measurements.geo_rmse_px)
    .filter((v): v is number => typeof v === 'number' && Number.isFinite(v));
  if (values.length === 0) return null;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function Face({
  heading,
  headingHint,
  hint,
  children,
}: {
  heading: string;
  // What the face draws, where the label alone cannot say it (the sketch has
  // four layers and no room for a legend).
  headingHint?: string;
  hint?: string;
  children?: React.ReactNode;
}) {
  return (
    // `flex: 1 1 150px` keeps the four faces in ONE row wherever they fit and
    // lets them break into a 2×2 block on a phone instead of shrinking to
    // strips. Bottom-aligned by the row, so a label that wraps to two lines
    // does not push its own frame out of line with the others.
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, flex: '1 1 150px', minWidth: 0 }}>
      {/* describeChild — a label tooltip would replace the visible face heading
          in the accessibility tree instead of describing it. */}
      {headingHint ? (
        <Tooltip title={headingHint} describeChild>
          <Typography variant="caption" color="text.secondary" tabIndex={0} sx={{ cursor: 'help', width: 'fit-content' }}>
            {heading}
          </Typography>
        </Tooltip>
      ) : (
        <Typography variant="caption" color="text.secondary">
          {heading}
        </Typography>
      )}
      <Box
        sx={{
          height: FACE_H,
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: '#fff',
          border: 1,
          borderColor: 'divider',
          borderRadius: 1,
          px: 1,
          overflow: 'hidden',
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

// Written silhouette projected back onto the crop pixels and drawn translucent
// over the original ink — direct coverage check. The canonical is normalised
// (baseline=0, midband=1, x-origin at the first sample); the inverse map is a
// pure scale+translate for an upright source (Sütterlin 90°): 1 template unit =
// (baseline_y_crop - midband_y_crop) px, pinned by the first anchor.
function CropWrittenOverlay({
  data,
  sourceId,
  glyphKey,
  cropCacheBust,
  height,
}: {
  data: DiagnosticData;
  sourceId: string;
  glyphKey: string;
  cropCacheBust: number;
  height: number;
}) {
  const cropW = data.crop_size.w;
  const cropH = data.crop_size.h;
  const unitPx = data.baseline_y_crop - data.midband_y_crop; // px per template unit
  const a0px = data.anchors_px[0];
  const a0t = data.anchors_template[0];
  const canMap = !!a0px && !!a0t && Number.isFinite(unitPx) && unitPx > 0;
  // template (x,y up) -> crop px: px_x = unitPx*x + ex ; px_y = -unitPx*y + baseline
  const ex = canMap ? a0px[0] - a0t[0] * unitPx : 0;
  const matrix = `matrix(${unitPx} 0 0 ${-unitPx} ${ex} ${data.baseline_y_crop})`;
  const scale = height / cropH;
  return (
    <svg
      width={cropW * scale}
      height={height}
      viewBox={`0 0 ${cropW} ${cropH}`}
      style={{ display: 'block', background: '#fff', maxWidth: '100%' }}
    >
      <image href={cropUrl(sourceId, glyphKey, cropCacheBust)} x={0} y={0} width={cropW} height={cropH} preserveAspectRatio="none" />
      {canMap && (
        <g transform={matrix}>
          {(data.outline_paths ?? []).map((rings, i) => (
            <path key={i} d={ringsToPathD(rings)} fill="#e02030" fillOpacity={0.42} fillRule="evenodd" />
          ))}
        </g>
      )}
    </svg>
  );
}

// The overlay's own lazy /diagnostic fetch — the ONE face that needs the heavy
// admin payload (outline rings + the crop's baseline calibration). Split out so
// the other three faces never wait on it and the request is not even made while
// the toggle is off.
function OverlayFace({
  glyphKey,
  sourceId,
  cropCacheBust,
  reloadKey,
}: {
  glyphKey: string;
  sourceId: string;
  cropCacheBust: number;
  reloadKey: number;
}) {
  const [data, setData] = useState<DiagnosticData | null>(null);
  // notFound = no canonical traced yet (typed ApiError 404); anything else is a
  // real load error. Branching on the typed status avoids parsing String(e).
  const [error, setError] = useState<{ notFound: boolean } | null>(null);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setError(null);
    getDiagnostic(sourceId, glyphKey)
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e) => {
        if (!cancelled) setError({ notFound: e instanceof ApiError && e.status === 404 });
      });
    return () => {
      cancelled = true;
    };
  }, [sourceId, glyphKey, cropCacheBust, reloadKey]);

  if (error) {
    return (
      <Typography variant="caption" color="text.disabled" sx={{ p: 1, textAlign: 'center' }}>
        {error.notFound ? de.admin.compare.noCanonical : de.admin.compare.loadError}
      </Typography>
    );
  }
  if (!data) return <CircularProgress size={20} />;
  return (
    <CropWrittenOverlay
      data={data}
      sourceId={sourceId}
      glyphKey={glyphKey}
      cropCacheBust={cropCacheBust}
      height={FACE_H}
    />
  );
}

function CompareCard({
  glyphKey,
  letterGlyph,
  sourceId,
  cropCacheBust,
  reloadKey,
  overlay,
  quality,
  aggregate,
  occurrences,
  statsHint,
  occurrencesKnown,
  onPick,
}: {
  glyphKey: string;
  letterGlyph: string;
  sourceId: string;
  cropCacheBust: number;
  reloadKey: number;
  overlay: boolean;
  quality?: QualityData | null;
  aggregate?: AggregateOut;
  occurrences: InstanceOut[];
  // Why the sketch face would be empty — one sentence, computed once for the
  // whole grid rather than per card.
  statsHint: string;
  // Has the public occurrence layer answered at all? A count is only printable
  // once it has.
  occurrencesKnown: boolean;
  onPick?: (glyphKey: string) => void;
}) {
  const t = de.admin.compare;
  // Everything below the header is heavy to paint (three SVG renders plus a
  // crop image per card, ~60 cards) — mount it only once the card scrolls
  // (near) into view. The DATA is already there; this gates the painting.
  const [cardRef, inView] = useInView<HTMLDivElement>();
  const [noLaufform, setNoLaufform] = useState(false);

  const rmse = meanRmse(occurrences);
  const anchors = aggregate ? letterSketchAnchors(aggregate) : [];
  const occurrenceChains = occurrenceChainsOf(occurrences);
  const laufformAnchors = (aggregate?.laufform_anchors ?? []).filter(isPoint);

  return (
    <Box
      ref={cardRef}
      sx={{
        border: 1,
        borderColor: 'divider',
        borderRadius: 2,
        p: 2,
        bgcolor: 'background.paper',
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, flexWrap: 'wrap' }}>
        <Typography sx={{ fontFamily: garamond, fontSize: 28, lineHeight: 1 }}>{letterGlyph}</Typography>
        <Typography variant="caption" color="text.secondary">
          {glyphKey}
        </Typography>
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', alignItems: 'center', flex: 1, minWidth: 0 }}>
          {/* „0 Vorkommen" is an ANSWER about the plates; it must not be shown
              while the occurrence read is in flight or after it failed. Then
              the tile says nothing about occurrences at all. */}
          {occurrencesKnown ? (
            <>
              <Chip
                size="small"
                variant="outlined"
                label={fmt(de.admin.letters.occurrenceCount, { count: occurrences.length })}
              />
              {rmse !== null && (
                <Tooltip title={t.fitMeanHint} describeChild>
                  <Chip size="small" variant="outlined" label={fmt(t.fitMean, { value: rmse.toFixed(2) })} />
                </Tooltip>
              )}
            </>
          ) : (
            <Typography variant="caption" color="text.disabled">
              {t.occurrencesUnknown}
            </Typography>
          )}
          {/* No chip at all while the score read is still in flight: „kein
              Score" is an answer about the ROW, and claiming it before the
              request lands would report every letter as unscored for a moment.
              `quality === undefined` is that in-flight state, `null` the
              answered „this row carries none". */}
          {quality === undefined ? null : quality ? (
            <ScoreChip score={quality.score} title={t.scoreHint} />
          ) : (
            <Tooltip title={t.scoreNoneHint} describeChild>
              <Chip size="small" variant="outlined" label={t.scoreNone} />
            </Tooltip>
          )}
        </Box>
        {/* The grid doubles as the Buchstaben view's overview, so a tile is the
            way INTO that letter — as an explicit button, not a click target on
            the whole card (which also carries the faces). */}
        {onPick && (
          <Button size="small" onClick={() => onPick(glyphKey)}>
            {t.openLetter}
          </Button>
        )}
      </Box>

      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        {overlay ? (
          <Face heading={t.overlayHeading}>
            {inView && (
              <OverlayFace
                glyphKey={glyphKey}
                sourceId={sourceId}
                cropCacheBust={cropCacheBust}
                reloadKey={reloadKey}
              />
            )}
          </Face>
        ) : (
          <>
            <Face heading={t.colCrop}>
              {inView && (
                <img
                  src={cropUrl(sourceId, glyphKey, cropCacheBust)}
                  alt={fmt(de.admin.werkbank.chartFormAlt, { key: glyphKey })}
                  loading="lazy"
                  decoding="async"
                  style={{ display: 'block', height: FACE_H, width: 'auto', maxWidth: '100%', objectFit: 'contain' }}
                />
              )}
            </Face>
            <Face heading={t.colWritten}>
              {inView && (
                <WrittenGlyph
                  glyphKey={glyphKey}
                  sourceId={sourceId}
                  height={FACE_H}
                  cacheBust={cropCacheBust}
                  tight
                  maxWidth={9999}
                  animate={false}
                />
              )}
            </Face>
          </>
        )}

        {/* The derived running form. Most letters have none yet — that is
            information, not a gap, so the face says so instead of silently
            repeating the Tafel form. */}
        <Face heading={t.colLaufform} hint={noLaufform ? t.noLaufformShort : undefined}>
          {inView && !noLaufform && (
            <WrittenGlyph
              key={`laufform-${glyphKey}`}
              glyphKey={glyphKey}
              sourceId={sourceId}
              variant={LAUFFORM_VARIANT}
              height={FACE_H}
              cacheBust={cropCacheBust}
              tight
              maxWidth={9999}
              animate={false}
              onUnavailable={() => setNoLaufform(true)}
            />
          )}
        </Face>

        {/* What the two written faces are judged against. Needs no request at
            all — the workbench layer holds both the occurrences and the hand's
            aggregate. An empty face must say WHY it is empty: „noch keine
            Statistik" is only true once the layer is actually there (it is an
            admin-gated read that may still be in flight, may 401, or may have
            no hand to key on). */}
        <Face heading={t.colSketch} headingHint={t.colSketchHint} hint={anchors.length < 2 ? statsHint : undefined}>
          {inView && anchors.length >= 2 && (
            <AggregateSketch
              anchors={anchors}
              glyphKey={glyphKey}
              occurrences={occurrenceChains}
              laufform={laufformAnchors}
              height={FACE_H - 12}
            />
          )}
        </Face>
      </Box>

      {/* Where the score went — the same categories, wording and colours as the
          wizard's bar chart, in one line so it stays smaller than the letter. */}
      {quality && <ScoreBreakdownInline quality={quality} />}
    </Box>
  );
}

export function GlyphComparison({ onPick }: { onPick?: (glyphKey: string) => void } = {}) {
  const { source, sourceId, glyphsByKey, cropCacheBust, refreshCrop } = useAdmin();
  const workbench = useWorkbench();
  const [reloadKey, setReloadKey] = useState(0);
  const [overlay, setOverlay] = useState(false);
  const [sort, setSort] = useState<SortMode>('alpha');
  const [quality, setQuality] = useState<Map<string, QualityData | null> | null>(null);
  // „Neu laden" has to move the version the render cache is keyed on, or the
  // written faces answer from the entries they already hold — the button would
  // refetch the scores and remount the cards while showing the same geometry.
  // `refreshCrop` is that version (the admin-wide crop/canonical stamp), so the
  // whole workbench reloads consistently rather than this grid alone.
  const reload = useCallback(() => {
    refreshCrop();
    setReloadKey((k) => k + 1);
  }, [refreshCrop]);

  const tiles = useMemo(() => buildTiles(glyphsByKey), [glyphsByKey]);

  // Both written faces of the WHOLE alphabet in two batch requests instead of
  // one request per face per card. The components then read the same cache and
  // paint without a round trip of their own.
  useEffect(() => {
    if (tiles.length === 0) return;
    const keys = tiles.map((t) => t.key);
    for (let i = 0; i < keys.length; i += PREFETCH_CHUNK) {
      const chunk = keys.slice(i, i + PREFETCH_CHUNK);
      for (const variant of [0, LAUFFORM_VARIANT]) {
        // Fire and forget: every consumer awaits the same cache entry, and a
        // failed batch is retried by the component that needs it.
        void fetchRenderGlyphs(sourceId, chunk, variant, cropCacheBust).catch(() => {});
      }
    }
  }, [tiles, sourceId, cropCacheBust, reloadKey]);

  // The stored score of every template in ONE admin read. Only variant 0 is
  // kept: a Laufform row inherits the chart row's trace_meta, so its stamped
  // score is a COPY of the chart form's — never a measurement of the median
  // geometry, and showing it as one would be a lie.
  useEffect(() => {
    let cancelled = false;
    setQuality(null);
    getTemplateQuality(sourceId, { retries: 1 })
      .then((rows) => {
        if (cancelled) return;
        setQuality(new Map(rows.filter((r) => r.variant === 0).map((r) => [r.glyph_key, r.quality])));
      })
      // Admin-gated: a 401 (or a source without scores) simply means no score
      // chips — the grid itself keeps working.
      .catch(() => {
        if (!cancelled) setQuality(new Map());
      });
    return () => {
      cancelled = true;
    };
  }, [sourceId, cropCacheBust, reloadKey]);

  // Both evidence layers must be able to say „I do not know yet" instead of
  // answering with a zero. The OCCURRENCE layer is public and loads with the
  // view; until it has answered, a tile has no count to print — and after a
  // failed read it has none either, which is not the same as „none exist".
  const occurrencesKnown = !workbench.loading && !workbench.error;

  // The statistics layer on top of it is admin-gated and loads on its own:
  // while it is in flight, has no hand to key on or came back 401, an empty
  // sketch face must not claim „noch keine Statistik" — that would report a
  // missing measurement where there is only a missing READ. The occurrence
  // layer is checked FIRST: the hand is derived from those rows, so „no hand"
  // is only meaningful once they are in.
  const statsHint = workbench.error
    ? de.admin.shell.evidenceError
    : !occurrencesKnown || workbench.letterStats.status === 'loading'
      ? de.admin.werkbank.statsLoading
      : workbench.letterStats.status === 'no-hand'
        ? de.admin.werkbank.statsNoHand
        : workbench.letterStats.status === 'unavailable'
          ? de.admin.werkbank.statsUnavailable
          : workbench.letterStats.layerEmpty
            ? de.admin.compare.noAggregateLayer
            : de.admin.compare.noAggregateShort;

  // The hand the numbers belong to — a grid that pools occurrences across two
  // writers and draws ONE hand's median beside them has to say so (the lens
  // blocks name their hand for the same reason).
  const handNote = workbench.handId
    ? fmt(de.admin.werkbank.statsHand, { hand: workbench.handId })
    : null;
  // `handsMixed` is not on the context itself — it travels with the stats
  // context, which is where the derivation lives.
  const mixedNote =
    workbench.letterStats.handsMixed && workbench.handId
      ? fmt(de.admin.werkbank.statsMixedHands, { hand: workbench.handId })
      : null;

  // Is there anything to rank BY? An unanswered read (null) and an answer with
  // no stored score anywhere both leave the worst-first order identical to the
  // alphabet.
  const scoresRanked = quality !== null && [...quality.values()].some((q) => q != null);

  const ordered = useMemo(() => {
    if (sort === 'alpha') return tiles;
    // Worst first — the work list. A letter without a stored score sorts to the
    // end rather than to the top: "unknown" is not "bad".
    return [...tiles].sort((a, b) => {
      const sa = quality?.get(a.key)?.score ?? Infinity;
      const sb = quality?.get(b.key)?.score ?? Infinity;
      return sa - sb;
    });
  }, [tiles, sort, quality]);

  if (!source) return null;

  return (
    // No own page padding/scroll container: since the redesign this grid is a
    // BLOCK inside the Buchstaben view, which owns both.
    <Box>
      {/* No own intro paragraph: the Buchstaben view's header already says
          what this grid is. Only its controls stay. */}
      <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 2, mb: 2 }}>
        {/* Which hand the occurrence counts and the medians belong to. The grid
            pools every stored occurrence of the source, and the sketch beside
            them is ONE hand's median — so the hand is named here rather than
            left to be assumed (optimierungs-werkbank.md §6). */}
        {/* Its own row on a phone — squeezed beside the controls the hand id
            wraps to one word per line. */}
        <Box sx={{ flex: { xs: '1 0 100%', sm: 1 }, minWidth: 0 }}>
          {handNote && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
              {handNote}
            </Typography>
          )}
          {mixedNote && (
            <Typography variant="caption" color="warning.main" sx={{ display: 'block' }}>
              {mixedNote}
            </Typography>
          )}
        </Box>
        <ToggleButtonGroup
          size="small"
          exclusive
          value={sort}
          onChange={(_, v: SortMode | null) => v && setSort(v)}
          aria-label={de.admin.compare.sortLabel}
        >
          <ToggleButton value="alpha">{de.admin.compare.sortAlpha}</ToggleButton>
          {/* Without scores the worst-first order would silently be the
              alphabet again — the button says so instead of pretending to
              sort (the read is admin-gated and may 401). */}
          <Tooltip title={scoresRanked ? '' : de.admin.compare.sortWorstUnavailable}>
            <span>
              <ToggleButton value="worst" disabled={!scoresRanked}>
                {de.admin.compare.sortWorst}
              </ToggleButton>
            </span>
          </Tooltip>
        </ToggleButtonGroup>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FormControlLabel
            control={<Switch size="small" checked={overlay} onChange={(e) => setOverlay(e.target.checked)} />}
            label={<Typography variant="caption">{de.admin.compare.overlayToggle}</Typography>}
          />
          <Button size="small" variant="outlined" startIcon={<RefreshIcon />} onClick={reload}>
            {de.admin.compare.reload}
          </Button>
        </Box>
      </Box>

      {tiles.length === 0 ? (
        <Alert severity="info">{de.admin.compare.empty}</Alert>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 1400 }}>
          {ordered.map((t) => (
            <CompareCard
              // Remount on a re-derive or „Neu laden": the per-card „this
              // letter has no Laufform" answer is a one-way flag, and an apply
              // (or a fresh trace) can make it wrong — a new key throws it away
              // instead of resetting state from an effect.
              key={`${t.key}:${cropCacheBust}:${reloadKey}`}
              glyphKey={t.key}
              letterGlyph={t.letterGlyph}
              sourceId={sourceId}
              cropCacheBust={cropCacheBust}
              reloadKey={reloadKey}
              overlay={overlay}
              aggregate={workbench.aggregatesByKey.get(t.key)}
              occurrences={workbench.instancesByKey.get(t.key) ?? []}
              // undefined = the score read has not answered yet; null = it
              // answered and this row carries none.
              quality={quality === null ? undefined : (quality.get(t.key) ?? null)}
              statsHint={statsHint}
              occurrencesKnown={occurrencesKnown}
              onPick={onPick}
            />
          ))}
        </Box>
      )}
    </Box>
  );
}
