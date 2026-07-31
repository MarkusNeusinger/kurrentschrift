// The Werkbank's context lens (optimierungs-werkbank.md §2): whatever was
// clicked in the word spine gets its cross-cutting view here — a LETTER with
// its chart form and every stored word occurrence as a thumbnail, or a JOIN
// with every dissected occurrence and the way into the pair editor. Clicking
// an occurrence jumps back into its word; the ⚑ buttons file an Auftrag.

import { Alert, Box, Button, Chip, Typography } from '@mui/material';
import type { ReactNode } from 'react';

import { cropUrl, wordSampleCropUrl } from '@/lib/api';
import type { InstanceOut, PairInstanceOut, WordSampleOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { garamond } from '@/styles/paper';

import { WERKBANK_COLORS, cropBoxOf, type Mark, type Selection } from './model';

const THUMB_H = 64; // px — tall enough to judge a letter's run form
const THUMB_PAD = 4; // crop px of air around the occurrence box

interface Props {
  sourceId: string;
  selection: Selection | null;
  // Already filtered to the selected element (and sorted worst-first) by the
  // view, which owns the grouped occurrence maps.
  letterOccurrences: InstanceOut[];
  pairOccurrences: PairInstanceOut[];
  sampleById: Map<string, WordSampleOut>;
  onJump: (specimenId: string) => void;
  onMark: (mark: Mark) => void;
  onOpenWizard: (glyphKey: string) => void;
  // Undefined when the pair has no editable join (e.g. the two letters fold
  // into a closed-set ligature, which has no Übergang to override).
  onOpenPairEditor?: () => void;
}

// One occurrence as a cut-out of its specimen crop: the crop is a background
// image, scaled and offset so exactly the occurrence box (plus a little air)
// shows through the tile.
function OccurrenceThumb({
  inst,
  sample,
  sourceId,
  onJump,
}: {
  inst: InstanceOut;
  sample: WordSampleOut;
  sourceId: string;
  onJump: () => void;
}) {
  const b = cropBoxOf(inst, sample.rect);
  if (!b) return null;
  const x = Math.max(0, b.x - THUMB_PAD);
  const y = Math.max(0, b.y - THUMB_PAD);
  const w = Math.min(sample.width - x, b.w + 2 * THUMB_PAD);
  const h = Math.min(sample.height - y, b.h + 2 * THUMB_PAD);
  if (w <= 0 || h <= 0) return null;
  const scale = THUMB_H / h;
  const rmse = inst.measurements.geo_rmse_px;

  return (
    <Box
      component="button"
      type="button"
      onClick={onJump}
      sx={{
        p: 0,
        border: 0,
        bgcolor: 'transparent',
        cursor: 'pointer',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 0.25,
      }}
    >
      <Box
        sx={{
          width: w * scale,
          height: THUMB_H,
          borderRadius: 1,
          border: 1,
          borderColor: 'divider',
          bgcolor: '#fff',
          backgroundImage: `url(${wordSampleCropUrl(sourceId, sample.id)})`,
          backgroundRepeat: 'no-repeat',
          backgroundSize: `${sample.width * scale}px ${sample.height * scale}px`,
          backgroundPosition: `${-x * scale}px ${-y * scale}px`,
        }}
      />
      <Typography variant="caption" color="text.secondary" sx={{ fontSize: 10, lineHeight: 1.2 }}>
        {sample.id}
        {rmse === undefined ? '' : ` · ${rmse.toFixed(1)} px`}
      </Typography>
    </Box>
  );
}

export function ContextLens({
  sourceId,
  selection,
  letterOccurrences,
  pairOccurrences,
  sampleById,
  onJump,
  onMark,
  onOpenWizard,
  onOpenPairEditor,
}: Props) {
  const t = de.admin.werkbank;

  const frame = (children: ReactNode) => (
    <Box
      sx={{
        border: 1,
        borderColor: 'divider',
        borderRadius: 2,
        p: 2,
        bgcolor: 'background.paper',
        position: 'sticky',
        top: (theme) => theme.spacing(2),
      }}
    >
      {children}
    </Box>
  );

  if (!selection) return frame(<Alert severity="info">{t.lensEmpty}</Alert>);

  if (selection.target.kind === 'letter') {
    const glyphKey = selection.target.glyphKey;
    const mark: Mark = { target: selection.target, specimen: selection.specimen };
    return frame(
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, flexWrap: 'wrap' }}>
          <Typography variant="subtitle1" sx={{ fontFamily: garamond }}>
            {fmt(t.lensLetterHeading, { key: glyphKey })}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {fmt(t.lensSeenIn, { word: selection.specimen.word })}
          </Typography>
        </Box>

        <Box>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
            {t.chartFormLabel}
          </Typography>
          <Box sx={{ bgcolor: '#fff', borderRadius: 1, border: 1, borderColor: 'divider', p: 0.5, width: 'fit-content' }}>
            <img
              src={cropUrl(sourceId, glyphKey)}
              alt={fmt(t.chartFormAlt, { key: glyphKey })}
              height={90}
              loading="lazy"
              decoding="async"
              style={{ display: 'block', maxWidth: '100%', objectFit: 'contain' }}
            />
          </Box>
        </Box>

        <Box>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
            {fmt(t.occurrencesLabel, { count: letterOccurrences.length })}
          </Typography>
          {letterOccurrences.length === 0 ? (
            <Typography variant="caption" color="text.disabled">
              {t.noOccurrences}
            </Typography>
          ) : (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {letterOccurrences.map((inst) => {
                const sample = sampleById.get(inst.measurements.specimen_id ?? '');
                if (!sample) return null;
                return (
                  <OccurrenceThumb
                    key={`${inst.measurements.specimen_id}:${inst.measurements.slot}`}
                    inst={inst}
                    sample={sample}
                    sourceId={sourceId}
                    onJump={() => onJump(sample.id)}
                  />
                );
              })}
            </Box>
          )}
        </Box>

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Button size="small" variant="outlined" onClick={() => onOpenWizard(glyphKey)}>
            {t.openWizard}
          </Button>
          <Button size="small" variant="text" onClick={() => onMark(mark)}>
            {`⚑ ${t.markLetter}`}
          </Button>
        </Box>
      </Box>,
    );
  }

  const { leftKey, rightKey } = selection.target;
  const pairMark: Mark = { target: selection.target, specimen: selection.specimen };
  return frame(
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
      <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, flexWrap: 'wrap' }}>
        <Typography variant="subtitle1" sx={{ fontFamily: garamond }}>
          {fmt(t.lensPairHeading, { left: leftKey, right: rightKey })}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {fmt(t.lensSeenIn, { word: selection.specimen.word })}
        </Typography>
      </Box>

      <Box>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
          {fmt(t.occurrencesLabel, { count: pairOccurrences.length })}
        </Typography>
        {pairOccurrences.length === 0 ? (
          <Typography variant="caption" color="text.disabled">
            {t.noOccurrences}
          </Typography>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            {pairOccurrences.map((occ) => (
              <Box
                key={`${occ.kind}:${occ.specimen_id}:${occ.slot}`}
                sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}
              >
                <Chip size="small" variant="outlined" clickable label={occ.specimen_id} onClick={() => onJump(occ.specimen_id)} />
                {occ.measurements.gen_chamfer !== undefined && (
                  <Typography variant="caption" color="text.secondary">
                    {fmt(t.genChamfer, { value: occ.measurements.gen_chamfer.toFixed(3) })}
                  </Typography>
                )}
                {occ.measurements.fit_ok === false && (
                  <Typography variant="caption" sx={{ color: WERKBANK_COLORS.selected }}>
                    {t.fitDoubtful}
                  </Typography>
                )}
              </Box>
            ))}
          </Box>
        )}
      </Box>

      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        {onOpenPairEditor && (
          <Button size="small" variant="outlined" onClick={onOpenPairEditor}>
            {t.openPairEditor}
          </Button>
        )}
        <Button size="small" variant="text" onClick={() => onMark(pairMark)}>
          {`⚑ ${t.markPair}`}
        </Button>
      </Box>
    </Box>,
  );
}
