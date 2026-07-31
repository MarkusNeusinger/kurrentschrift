// One word of the Werkbank spine: the specimen crop, the stored trace over it
// (like the Belege page), and on top the INTERACTIVE occurrence layer — a
// dashed box per fitted letter, a dot per join between two adjacent letters.
// Clicking switches the context lens; ⚑ (or shift-click) files the element as
// an Auftrag. Errors become visible in words, so this is where marking starts.

import { Box, Chip, Tooltip, Typography } from '@mui/material';

import { useInView } from '@/hooks/useInView';
import { wordSampleCropUrl } from '@/lib/api';
import type { InstanceOut, WordInstanceOut, WordSampleOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { garamond } from '@/styles/paper';

import {
  WERKBANK_COLORS,
  cardElementId,
  cropBoxOf,
  rmseMean,
  type Mark,
  type Selection,
  type SpecimenRef,
} from './model';

const FACE_H = 220; // px per card face — same scale as the compare/Belege cards

interface Props {
  row: WordInstanceOut;
  sample: WordSampleOut;
  sourceId: string;
  // This specimen's letter occurrences, ascending by composer slot.
  boxes: InstanceOut[];
  selection: Selection | null;
  onSelect: (selection: Selection) => void;
  onMark: (mark: Mark) => void;
}

// Is this box the element the lens currently shows? (The boxes are already
// this specimen's, so the id compare only has to rule out the same letter in
// another word.)
function isSelectedLetter(selection: Selection | null, specimenId: string, inst: InstanceOut): boolean {
  return (
    selection?.target.kind === 'letter' &&
    selection.target.glyphKey === inst.glyph_key &&
    selection.specimen.id === specimenId
  );
}

export function WordSpineCard({ row, sample, sourceId, boxes, selection, onSelect, onMark }: Props) {
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

  const specimen: SpecimenRef = { id: row.specimen_id, kind: row.kind, word: row.word };
  const selectLetter = (inst: InstanceOut) =>
    onSelect({ target: { kind: 'letter', glyphKey: inst.glyph_key }, specimen });
  const selectPair = (left: InstanceOut, right: InstanceOut) =>
    onSelect({ target: { kind: 'pair', leftKey: left.glyph_key, rightKey: right.glyph_key }, specimen });

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
        <Tooltip title={t.markWord}>
          <Chip
            size="small"
            variant="outlined"
            clickable
            label={`⚑ ${t.kindWord}`}
            onClick={() => onMark({ target: { kind: 'word', word: row.word }, specimen })}
            sx={{ ml: 'auto' }}
          />
        </Tooltip>
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
          {boxes.map((inst) => {
            const b = cropBoxOf(inst, sample.rect);
            const rmse = inst.measurements.geo_rmse_px;
            const selected = isSelectedLetter(selection, row.specimen_id, inst);
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
                  fill={selected ? WERKBANK_COLORS.selected : 'transparent'}
                  fillOpacity={selected ? 0.12 : 1}
                  stroke={selected ? WERKBANK_COLORS.selected : WERKBANK_COLORS.box}
                  strokeWidth={(selected ? 2 : 1) * px}
                  strokeDasharray={selected ? undefined : `${3 * px} ${3 * px}`}
                />
              </g>
            );
          })}
          {joins.map(({ left, right }) => {
            const lb = cropBoxOf(left, sample.rect);
            const rb = cropBoxOf(right, sample.rect);
            const selected =
              selection?.target.kind === 'pair' &&
              selection.target.leftKey === left.glyph_key &&
              selection.target.rightKey === right.glyph_key &&
              selection.specimen.id === row.specimen_id;
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
                  fill={selected ? WERKBANK_COLORS.selected : WERKBANK_COLORS.accent}
                  fillOpacity={selected ? 0.45 : 0.18}
                  stroke={selected ? WERKBANK_COLORS.selected : WERKBANK_COLORS.accent}
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
