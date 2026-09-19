// ONE letter as FOUR faces — the whole pipeline of that letter in one block:
//
//   Original          the unaltered chart crop — the goal
//   Tafel-Form        what the engine writes from the authored ductus (variant 0)
//   Laufform          what it writes inside running words (variant 100)
//   Median & Vorkommen the statistics both are judged against: the per-anchor
//                     median over every measured occurrence, the occurrence
//                     chains thin behind it, the currently rendered Laufform
//                     dashed against it
//
// Split out of `GlyphComparison` when the Buchstaben overview became a work
// list: the card is now mounted from TWO places — the gallery grid, and an
// expanded row of the compact list — and a list module that had to import the
// whole grid to get at it would pull the grid's prefetch and score read along.
// A pure move: the component is prop-only and gates its own painting.
//
// Everything below the header is heavy (three SVG renders plus a crop image),
// so it hangs behind `useInView`. In an expanded row that fires immediately —
// the row is on screen when it opens, which is exactly the intent: no image
// loads for a collapsed row.

import { Box, Button, Chip, CircularProgress, Typography } from '@mui/material';
import { useEffect, useState } from 'react';

import { InfoHint } from '@/components/InfoHint';
import { WrittenGlyph } from '@/components/WrittenGlyph';
import { useInView } from '@/hooks/useInView';
import { ApiError, cropUrl, getDiagnostic } from '@/lib/api';
import type { AggregateOut, DiagnosticData, InstanceOut, QualityData } from '@/lib/api';
import { ringsToPathD } from '@/lib/svg';
import { de, fmt } from '@/locales/admin';
import { ScoreBreakdownInline, ScoreChip, ScoreHelp } from '@/sections/admin/quality/scoreParts';
import { AggregateSketch } from '@/sections/admin/shell/AggregateSketch';
import { WERKBANK_COLORS } from '@/sections/admin/shell/model';
import { isPoint, letterSketchAnchors, occurrenceChainsOf } from '@/sections/admin/shell/sketchGeometry';
import { TOUCH_TARGET } from '@/styles/hitArea';
import { garamond, layerAlpha } from '@/styles/paper';

// px — four faces have to fit beside each other on a laptop, so each is about
// half the height the two-face row used. Still large enough to judge a ductus:
// the detail view's faces are 190.
const FACE_H = 170;
// The Laufform is stored as this template variant (core/database LAUFFORM_VARIANT).
const LAUFFORM_VARIANT = 100;

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
      {/* The legend of a face — four layers in one sketch — used to be a hover
          on a `Typography` carrying a bare `tabIndex={0}`: a tab stop with no
          focus ring, and nothing at all for a finger. `InfoHint` is a real
          button with the shared ring and a 44 px target (V25, §9.4). */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        <Typography variant="caption" color="textSecondary">
          {heading}
        </Typography>
        {headingHint && <InfoHint title={heading}>{headingHint}</InfoHint>}
      </Box>
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
          <Typography variant="caption" color="textDisabled" sx={{ p: 1, textAlign: 'center' }}>
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
            <path
              key={i}
              d={ringsToPathD(rings)}
              fill={WERKBANK_COLORS.engine}
              fillOpacity={layerAlpha.engineOverlay}
              fillRule="evenodd"
            />
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

  // Drop the previous glyph's diagnostic DURING RENDER instead of in the effect
  // below — React's "adjusting state when a prop changes"
  // (react-hooks/set-state-in-effect). The guard carries the effect's inputs, so
  // a card swap never paints one frame of the old letter's rings.
  const loadKey = `${sourceId} ${glyphKey} ${cropCacheBust} ${reloadKey}`;
  const [shownFor, setShownFor] = useState(loadKey);
  if (shownFor !== loadKey) {
    setShownFor(loadKey);
    setData(null);
    setError(null);
  }

  useEffect(() => {
    let cancelled = false;
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
      <Typography variant="caption" color="textDisabled" sx={{ p: 1, textAlign: 'center' }}>
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

export function CompareCard({
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
  framed = true,
  header = true,
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
  // Inside an expanded work-list row the card sits in the row's own frame, and
  // the row already carries the glyph, the key, the chips and the way in — a
  // second border and a second header would say everything twice.
  framed?: boolean;
  header?: boolean;
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
        ...(framed
          ? { border: 1, borderColor: 'divider', borderRadius: 2, p: 2, bgcolor: 'background.paper' }
          : { pt: 1 }),
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
      }}
    >
      {header && (
        <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, flexWrap: 'wrap' }}>
          <Typography sx={{ fontFamily: garamond, fontSize: 28, lineHeight: 1 }}>{letterGlyph}</Typography>
          <Typography variant="caption" color="textSecondary">
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
                {/* What „Fit ⌀" means is a line of `ScoreHelp` now — it hung in
                    a tooltip on a plain `div`, which is neither keyboard- nor
                    touch-reachable (V25). */}
                {rmse !== null && (
                  <Chip size="small" variant="outlined" label={fmt(t.fitMean, { value: rmse.toFixed(2) })} />
                )}
              </>
            ) : (
              <Typography variant="caption" color="textDisabled">
                {t.occurrencesUnknown}
              </Typography>
            )}
            {/* No chip at all while the score read is still in flight: „kein
                Score" is an answer about the ROW, and claiming it before the
                request lands would report every letter as unscored for a moment.
                `quality === undefined` is that in-flight state, `null` the
                answered „this row carries none". */}
            {quality === undefined ? null : quality ? (
              <ScoreChip score={quality.score} />
            ) : (
              <>
                <Chip size="small" variant="outlined" label={t.scoreNone} />
                <ScoreHelp />
              </>
            )}
          </Box>
          {/* The grid doubles as the Buchstaben view's overview, so a tile is the
              way INTO that letter — as an explicit button, not a click target on
              the whole card (which also carries the faces). */}
          {onPick && (
            // 64×32.5 until the first sweep of the ADMIN routes (2026-09-19):
            // the list's own „Öffnen" grew to the §9.3 floor when the work list
            // was built, and the gallery's twin — twenty of them on one page —
            // was never measured, because no route list reached this view.
            <Button
              size="small"
              onClick={() => onPick(glyphKey)}
              aria-label={fmt(t.openLetterFor, { key: glyphKey })}
              sx={{ minHeight: TOUCH_TARGET }}
            >
              {t.openLetter}
            </Button>
          )}
        </Box>
      )}

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
      {header && quality && <ScoreBreakdownInline quality={quality} />}
    </Box>
  );
}
