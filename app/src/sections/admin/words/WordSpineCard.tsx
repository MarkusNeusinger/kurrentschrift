// One traced word over its specimen crop, with the INTERACTIVE occurrence layer
// on top — a dashed box per fitted letter, a dot per join between two adjacent
// letters. Errors become visible in words, so this card is where the walk into
// the other two views starts: a box opens the letter, a dot the join, ⚑ (or
// shift-click) files the element as an Auftrag.

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
  type Mark,
  type SpecimenRef,
} from '@/sections/admin/shell/model';
import { garamond } from '@/styles/paper';

const FACE_H = 220; // px per card face — same scale as the compare/Belege cards

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
  // The engine's composition of the same word, drawn over the specimen pixels
  // when present. THE comparison the whole bench exists for: the sidecar
  // carries the specimen's crop-local baseline/midband, the composed word
  // lives in template units (baseline = 0, 1 unit = x-height), so the map is a
  // pure scale+translate — no eyeballing.
  composed?: ComposedWordOut | null;
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
}: Props) {
  const [ref, inView] = useInView<HTMLDivElement>();
  const t = de.admin.werkbank;

  const m = row.measurements;
  const reg = m.registration_px;
  const xh = m.xh_px ?? sample.baseline_y - sample.midband_y;
  const tx = reg?.tx ?? 0;
  const baselineRow = (reg?.baseline_row ?? sample.baseline_y) + (reg?.ty ?? 0);
  // Trace units → crop px: px = (u·xh + tx, baseline_row + ty − v·xh).
  const matrix = `matrix(${xh} 0 0 ${-xh} ${tx} ${baselineRow})`;

  const fitted = m.fitted_slots?.length ?? null;
  const unfitted = (m.unfitted_slots ?? []).map((i) => row.slots[i] ?? String(i));
  const meanRmse = rmseMean(row);
  const cropW = (FACE_H / sample.height) * sample.width;
  // One display pixel in viewBox units — keeps hairlines and hit targets the
  // same visual size across crops of very different resolutions.
  const px = sample.height / FACE_H;

  // Engine ink → specimen pixels. Same transform WordComparison's overlay uses
  // (kept in step with it): px per template unit = baseline − midband, the
  // engine's left edge aligned to the crop's, y flipped.
  const unitPx = sample.baseline_y - sample.midband_y;
  const engineMatrix = composed
    ? `matrix(${unitPx} 0 0 ${-unitPx} ${-composed.bounds.min_x * unitPx} ${sample.baseline_y})`
    : null;

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
            {row.strokes.map((stroke, i) => (
              <path
                key={i}
                d={stroke.map(([x, y], j) => `${j === 0 ? 'M' : 'L'}${x},${y}`).join(' ')}
                fill="none"
                stroke={WERKBANK_COLORS.trace}
                strokeOpacity={0.8}
                strokeWidth={0.07}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            ))}
          </g>
          {/* The engine's own answer, registered onto the same ink. Red and
              translucent, exactly as in the comparison list, so „where does
              the composition leave the original?" is one look. */}
          {engineMatrix && composed && (
            <g transform={engineMatrix}>
              {composed.items.map((it, i) =>
                it.rings ? (
                  <path key={i} d={ringsToPathD(it.rings)} fill="#e02030" fillOpacity={0.42} fillRule="evenodd" />
                ) : (
                  <path
                    key={i}
                    d={polylineToPathD(it.centerline)}
                    fill="none"
                    stroke="#e02030"
                    strokeOpacity={0.42}
                    strokeWidth={it.stroke_width ?? it.mask_width}
                    strokeLinecap="round"
                  />
                ),
              )}
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
      ) : (
        <Box sx={{ height: FACE_H }} />
      )}
    </Box>
  );
}
