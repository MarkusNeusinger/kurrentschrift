// One stored letter occurrence as a cut-out of its specimen crop: the crop is a
// background image, scaled and offset so exactly the occurrence box (plus a
// little air) shows through the tile. Clicking it goes to the word the letter
// was written in — the way back from "how does this hand form the letter?" to
// "where did I see it?".
//
// Extracted from the old Werkbank context lens so the Buchstaben view and any
// other surface showing occurrences draw them identically.

import { Box, Typography } from '@mui/material';

import { wordSampleCropUrl } from '@/lib/api';
import type { InstanceOut, WordSampleOut } from '@/lib/api';

import { cropBoxOf } from './model';

const THUMB_H = 64; // px — tall enough to judge a letter's run form
const THUMB_PAD = 4; // crop px of air around the occurrence box

export function OccurrenceThumb({
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
