// One traced word over its specimen crop, with the INTERACTIVE occurrence layer
// on top — a dashed box per fitted letter, a dot per join between two adjacent
// letters. Errors become visible in words, so this card is where the walk into
// the other two views starts: a box opens the letter, a dot the join, ⚑ (or
// shift-click) files the element as an Auftrag.
//
// TWO faces, like a letter tile: left the MEASUREMENT (specimen ink + the
// traced pen path over it — „trifft der Fit das Wort?"), right what the engine
// itself writes from that measurement („und was macht das System daraus?").
// Both faces are drawn at the SAME px-per-unit and share one baseline row, so
// width, slant and rhythm compare by eye without any mental rescaling.
//
// Registration: BOTH the green trace and the red engine ink use the row's own
// measured registration (`registration_px` + `xh_px`) — the trace and the
// composition live in the same frame (baseline = 0, 1 unit = x-height), so
// there is nothing to align by hand. The overlay used to pin the engine to the
// crop's LEFT EDGE instead, which shifted it a median 8.9 px (~0.3 xh) left of
// the ink across the 63 word rows and made every composition look worse than
// it is; on the measured registration that median error drops to 1.1 px, and
// what is left over at the right edge is the real width difference.

import { Box, Chip, Tooltip, Typography } from '@mui/material';

import { useInView } from '@/hooks/useInView';
import { wordSampleCropUrl } from '@/lib/api';
import type { ComposedWordOut, InstanceOut, WordInstanceOut, WordSampleOut } from '@/lib/api';
import { polylineToPathD, ringsToPathD } from '@/lib/svg';
import { de, fmt } from '@/locales/admin';
import {
  WERKBANK_COLORS,
  cardElementId,
  cropBoxOf,
  rmseMean,
  traceFrameOf,
  traceMatrix,
  type Mark,
  type SpecimenRef,
} from '@/sections/admin/shell/model';
import { garamond, paper } from '@/styles/paper';

const FACE_H = 220; // px per card face — same scale as the compare/Belege cards
const FACE_PAD = 6; // crop px of air around the engine face's own ink

// The engine's ink, in one place: overlay (translucent, over the specimen) and
// its own face (opaque, on white) draw the identical item list.
function EngineInk({ composed, opacity }: { composed: ComposedWordOut; opacity: number }) {
  return (
    <>
      {composed.items.map((it, i) =>
        it.rings ? (
          <path
            key={i}
            d={ringsToPathD(it.rings)}
            fill={WERKBANK_COLORS.engine}
            fillOpacity={opacity}
            fillRule="evenodd"
          />
        ) : (
          <path
            key={i}
            // flipY off: the enclosing <g> already carries the y flip, and
            // the rings beside it are not negated either. With the default,
            // every generated Übergang was mirrored below the baseline.
            d={polylineToPathD(it.centerline, 0, false)}
            fill="none"
            stroke={WERKBANK_COLORS.engine}
            strokeOpacity={opacity}
            strokeWidth={it.stroke_width ?? it.mask_width}
            strokeLinecap="round"
          />
        ),
      )}
    </>
  );
}

// The engine's word alone, at the specimen face's px-per-unit and on its
// baseline row — so the two faces are literally the same scale, and a width or
// slant difference is a difference, not a rendering artefact.
function EngineFace({
  composed,
  xh,
  baselineRow,
  cropHeight,
}: {
  composed: ComposedWordOut;
  xh: number;
  baselineRow: number;
  cropHeight: number;
}) {
  const { min_x: minX, max_x: maxX, min_y: minY, max_y: maxY } = composed.bounds;
  const width = Math.max(1, (maxX - minX) * xh + 2 * FACE_PAD);
  // The face is the crop's band, widened wherever the composition reaches past
  // it (a deep descender, a tall capital) — never cropped, never rescaled.
  const top = Math.min(0, baselineRow - maxY * xh - FACE_PAD);
  const bottom = Math.max(cropHeight, baselineRow - minY * xh + FACE_PAD);
  const scale = FACE_H / cropHeight; // identical to the specimen face's
  const px = 1 / scale; // one display pixel, in viewBox units
  return (
    <svg
      width={width * scale}
      height={(bottom - top) * scale}
      viewBox={`0 ${top} ${width} ${bottom - top}`}
      style={{ display: 'block', background: '#fff', maxWidth: '100%' }}
      aria-label={`${de.admin.werkbank.faceWritten} ${composed.text}`}
    >
      {/* Grundlinie + Mittellinie, so the face is readable without the crop's
          own ruling behind it. */}
      {[baselineRow, baselineRow - xh].map((y, i) => (
        <line key={i} x1={0} x2={width} y1={y} y2={y} stroke={paper.line} strokeWidth={px} />
      ))}
      <g transform={`matrix(${xh} 0 0 ${-xh} ${FACE_PAD - minX * xh} ${baselineRow})`}>
        <EngineInk composed={composed} opacity={0.85} />
      </g>
    </svg>
  );
}

interface Props {
  row: WordInstanceOut;
  sample: WordSampleOut;
  sourceId: string;
  // This specimen's letter occurrences, ascending by composer slot.
  boxes: InstanceOut[];
  onOpenLetter: (glyphKey: string) => void;
  onOpenPair: (leftKey: string, rightKey: string) => void;
  onMark: (mark: Mark) => void;
  // Extra actions in the card header (the word editor, a score button) — owned
  // by the view, since what can be done with a trace is its business.
  actions?: React.ReactNode;
  // The engine's composition of the same word. Drawn on its own face beside
  // the specimen always, and — when `overlay` is set — additionally into the
  // specimen face on top of the ink. THE comparison the whole bench exists for.
  composed?: ComposedWordOut | null;
  // Project the engine ink onto the specimen pixels as well. Off, the two faces
  // stay separate and each stays legible; on, the deviation is exact.
  overlay?: boolean;
  // Draw the stored trace on the specimen face. Separately switchable from the
  // engine ink: three lines over one crop is a lot, and which pair you want to
  // compare — ink vs. trace, ink vs. engine, trace vs. engine — changes with
  // the question being asked.
  showTrace?: boolean;
}

export function WordSpineCard({
  row,
  sample,
  sourceId,
  boxes,
  onOpenLetter,
  onOpenPair,
  onMark,
  actions,
  composed,
  overlay = false,
  showTrace = true,
}: Props) {
  const [ref, inView] = useInView<HTMLDivElement>();
  const t = de.admin.werkbank;

  const m = row.measurements;
  // ONE frame for both inks — the trace and the engine ride the same matrix.
  const frame = traceFrameOf(row, sample);
  const { xh, baselineRow } = frame;
  const matrix = traceMatrix(frame);

  const fitted = m.fitted_slots?.length ?? null;
  const unfitted = (m.unfitted_slots ?? []).map((i) => row.slots[i] ?? String(i));
  const meanRmse = rmseMean(row);
  const cropW = (FACE_H / sample.height) * sample.width;
  // One display pixel in viewBox units — keeps hairlines and hit targets the
  // same visual size across crops of very different resolutions.
  const px = sample.height / FACE_H;

  const specimen: SpecimenRef = { id: row.specimen_id, kind: row.kind, word: row.word };
  const selectLetter = (inst: InstanceOut) => onOpenLetter(inst.glyph_key);
  const selectPair = (left: InstanceOut, right: InstanceOut) => onOpenPair(left.glyph_key, right.glyph_key);

  // Shift-click is the mockup's shortcut: mark without going through the lens.
  const activate = (event: { shiftKey?: boolean }, select: () => void, mark: Mark) =>
    event.shiftKey ? onMark(mark) : select();

  // Joins sit between two letters the fit placed CONSECUTIVELY (composer slot
  // space) — a gap means an unfitted letter or a space in between, and there is
  // no join to inspect across it.
  const joins = boxes.flatMap((left, i) => {
    const right = boxes[i + 1];
    const leftSlot = left.measurements.slot;
    const rightSlot = right?.measurements.slot;
    if (!right || leftSlot === undefined || rightSlot === undefined || rightSlot !== leftSlot + 1) return [];
    return [{ left, right }];
  });

  return (
    <Box
      ref={ref}
      id={cardElementId(row.specimen_id)}
      sx={{ border: 1, borderColor: 'divider', borderRadius: 2, p: 2, bgcolor: 'background.paper' }}
    >
      <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, flexWrap: 'wrap', mb: 1 }}>
        <Typography sx={{ fontFamily: garamond, fontSize: 24, lineHeight: 1 }}>{row.word}</Typography>
        <Typography variant="caption" color="text.secondary">
          {row.specimen_id}
        </Typography>
        <Chip
          size="small"
          variant="outlined"
          color={row.provenance === 'authored' ? 'success' : 'default'}
          label={row.provenance === 'authored' ? t.provenanceAuthored : t.provenanceTraced}
        />
        {fitted !== null && (
          <Chip
            size="small"
            variant="outlined"
            label={fmt(t.fittedChip, { fitted, total: fitted + unfitted.length })}
          />
        )}
        {unfitted.length > 0 && (
          <Chip size="small" color="warning" label={`${t.unfittedPrefix}${unfitted.join(' ')}`} />
        )}
        {meanRmse !== null && (
          <Chip size="small" variant="outlined" label={fmt(t.rmseChip, { value: meanRmse.toFixed(2) })} />
        )}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 'auto' }}>
          {actions}
          <Tooltip title={t.markWord}>
            <Chip
              size="small"
              variant="outlined"
              clickable
              label={`⚑ ${t.kindWord}`}
              onClick={() => onMark({ target: { kind: 'word', word: row.word }, specimen })}
            />
          </Tooltip>
        </Box>
      </Box>
      {inView ? (
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', alignItems: 'flex-start' }}>
          {/* Face 1 — the measurement: plate ink, the traced pen path over it,
              and the clickable occurrence layer. */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, minWidth: 0, flex: '1 1 320px' }}>
            <Typography variant="caption" color="text.secondary">
              {/* The caption names exactly the layers actually drawn — with
                  both switched off it says so rather than promising ink that
                  is not there. */}
              {[t.faceSpecimenBase, showTrace && t.faceLayerTrace, overlay && composed && t.faceLayerEngine]
                .filter(Boolean)
                .join(' + ')}
            </Typography>
            <svg
              width={cropW}
              height={FACE_H}
              viewBox={`0 0 ${sample.width} ${sample.height}`}
              style={{ display: 'block', background: '#fff', maxWidth: '100%', height: 'auto' }}
              aria-label={`${t.cropAlt} ${row.word}`}
            >
              <image
                href={wordSampleCropUrl(sourceId, sample.id)}
                x={0}
                y={0}
                width={sample.width}
                height={sample.height}
                preserveAspectRatio="none"
              />
              <g transform={matrix}>
                {(showTrace ? row.strokes : []).map((stroke, i) => (
                  <path
                    key={i}
                    d={stroke.map(([x, y], j) => `${j === 0 ? 'M' : 'L'}${x},${y}`).join(' ')}
                    fill="none"
                    stroke={WERKBANK_COLORS.traceOverInk}
                    strokeOpacity={0.95}
                    // ~2/3 of a hairline stroke's own width: thick enough to
                    // read over black ink, thin enough that the ink it follows
                    // still shows on both sides of it.
                    strokeWidth={0.11}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                ))}
              </g>
              {overlay && composed && (
                <g transform={matrix}>
                  <EngineInk composed={composed} opacity={0.42} />
                </g>
              )}
              {boxes.map((inst) => {
                const b = cropBoxOf(inst, sample.rect);
                if (!b) return null;
                const rmse = inst.measurements.geo_rmse_px;
                const mark: Mark = { target: { kind: 'letter', glyphKey: inst.glyph_key }, specimen };
                return (
                  <g
                    key={`${inst.glyph_key}:${inst.measurements.slot}`}
                    role="button"
                    tabIndex={0}
                    aria-label={fmt(t.letterBoxAria, { key: inst.glyph_key, word: row.word })}
                    style={{ cursor: 'pointer' }}
                    onClick={(e) => activate(e, () => selectLetter(inst), mark)}
                    onKeyDown={(e) => {
                      if (e.key !== 'Enter' && e.key !== ' ') return;
                      e.preventDefault();
                      activate(e, () => selectLetter(inst), mark);
                    }}
                  >
                    <title>
                      {rmse === undefined
                        ? fmt(t.letterBoxTitleNoRmse, { key: inst.glyph_key })
                        : fmt(t.letterBoxTitle, { key: inst.glyph_key, rmse: rmse.toFixed(2) })}
                    </title>
                    <rect
                      x={b.x}
                      y={b.y}
                      width={b.w}
                      height={b.h}
                      fill="transparent"
                      stroke={WERKBANK_COLORS.box}
                      strokeWidth={px}
                      strokeDasharray={`${3 * px} ${3 * px}`}
                    />
                  </g>
                );
              })}
              {joins.map(({ left, right }) => {
                const lb = cropBoxOf(left, sample.rect);
                const rb = cropBoxOf(right, sample.rect);
                if (!lb || !rb) return null;
                const mark: Mark = {
                  target: { kind: 'pair', leftKey: left.glyph_key, rightKey: right.glyph_key },
                  specimen,
                };
                return (
                  <g
                    key={`${left.measurements.slot}-join`}
                    role="button"
                    tabIndex={0}
                    aria-label={fmt(t.joinDotAria, { left: left.glyph_key, right: right.glyph_key, word: row.word })}
                    style={{ cursor: 'pointer' }}
                    onClick={(e) => activate(e, () => selectPair(left, right), mark)}
                    onKeyDown={(e) => {
                      if (e.key !== 'Enter' && e.key !== ' ') return;
                      e.preventDefault();
                      activate(e, () => selectPair(left, right), mark);
                    }}
                  >
                    <title>{fmt(t.joinDotTitle, { left: left.glyph_key, right: right.glyph_key })}</title>
                    <circle
                      cx={(lb.x + lb.w + rb.x) / 2}
                      cy={sample.height * 0.55}
                      r={8 * px}
                      fill={WERKBANK_COLORS.accent}
                      fillOpacity={0.18}
                      stroke={WERKBANK_COLORS.accent}
                      strokeWidth={1.2 * px}
                    />
                  </g>
                );
              })}
            </svg>
          </Box>
          {/* Face 2 — the engine's own answer, same scale, same baseline. */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, minWidth: 0, flex: '1 1 320px' }}>
            <Typography variant="caption" color="text.secondary">
              {t.faceWritten}
            </Typography>
            {composed ? (
              <Box sx={{ overflowX: 'auto' }}>
                <EngineFace composed={composed} xh={xh} baselineRow={baselineRow} cropHeight={sample.height} />
              </Box>
            ) : (
              <Box
                sx={{
                  height: FACE_H,
                  minWidth: 160,
                  bgcolor: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  px: 2,
                }}
              >
                <Typography variant="caption" color="text.disabled">
                  {t.faceWrittenPending}
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      ) : (
        <Box sx={{ height: FACE_H }} />
      )}
    </Box>
  );
}
