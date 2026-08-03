// One stored letter occurrence as a cut-out of its specimen crop: the crop is a
// background image, scaled and offset so exactly the occurrence box (plus a
// little air) shows through the tile. Clicking it goes to the word the letter
// was written in — the way back from "how does this hand form the letter?" to
// "where did I see it?".
//
// Extracted from the old Werkbank context lens so the Buchstaben view and any
// other surface showing occurrences draw them identically.
//
// The air around the box is deliberately generous: the stored occurrence box
// comes from the M4 fit and therefore hugs the CENTERLINE, while the ink runs
// on for half a stroke width beyond it on every side — measured on the
// suetterlin-1922 crops the strokes are ~6 crop px wide (median dark run, both
// axes), so ~3 px of ink sit outside the box, and the fit residual adds up to
// another 2,2 px (`geo_rmse_px`: median 1,0 · p90 1,6 · max 2,2). A fixed 4 px
// pad cut into the letter; it also ignored that a crop's scale varies.

import { Box, Typography } from '@mui/material';

import { wordSampleCropUrl } from '@/lib/api';
import type { InstanceOut, WordSampleOut } from '@/lib/api';

import { cropBoxOf } from './model';

const THUMB_H = 80; // px — tall enough to judge a letter's run form, and raised
// with the pad below so the extra air does not shrink the letter itself.

// Floor and proportional share of the air around the occurrence box, in crop px.
// The floor covers the constant part of the shortfall (ink half-width + fit
// residual ≈ 5 px on these plates) and still leaves ~2 px of white; the share
// scales the air with the box, because 4 px is a lot on a small crop and
// nothing on a large one. The share is taken on the box's GEOMETRIC MEAN, not
// its long side: the stored boxes are extreme in both aspects (`m` 86 × 29 px,
// `longs` 16 × 87 px over the 218 occurrences of suetterlin-1922), and a share
// of the long side would pad the flat `m` by half its own height while barely
// widening `longs`. sqrt(w·h) gives 7 px (x-height letters) … 13 px (capitals),
// and at that pad the letter itself is still drawn no smaller than with the old
// flat 4 px (checked per glyph key against the stored boxes; only the widest
// forms `m` and `W` lose ~1 %), while no tile fills up with its neighbours.
const THUMB_PAD_MIN = 7;
const THUMB_PAD_SHARE = 0.18;

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
  const pad = Math.max(THUMB_PAD_MIN, THUMB_PAD_SHARE * Math.sqrt(b.w * b.h));
  const x = Math.max(0, b.x - pad);
  const y = Math.max(0, b.y - pad);
  const w = Math.min(sample.width - x, b.w + 2 * pad);
  const h = Math.min(sample.height - y, b.h + 2 * pad);
  if (w <= 0 || h <= 0) return null;
  const scale = THUMB_H / h;
  const tileW = w * scale;
  const rmse = inst.measurements.geo_rmse_px;
  const caption = `${sample.id}${rmse === undefined ? '' : ` · ${rmse.toFixed(1)} px`}`;

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
          width: tileW,
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
      {/* Caption at the binding 14 px floor (design-system.md §Lesbarkeit), held
          to the tile's width — a long specimen id would otherwise stretch the
          tile and tear the wrapped row apart. The two halves are laid out
          separately on purpose: the word truncates, the fit residual never
          does. It is the number the list is SORTED by (worst fit first), so
          losing it to an ellipsis would hide exactly what the order means. The
          full text stays reachable as the title tooltip. */}
      <Box sx={{ display: 'flex', gap: 0.5, maxWidth: tileW, width: '100%', justifyContent: 'center' }} title={caption}>
        <Typography variant="caption" color="text.secondary" noWrap sx={{ minWidth: 0, lineHeight: 1.2 }}>
          {sample.id}
        </Typography>
        {rmse !== undefined && (
          <Typography variant="caption" color="text.secondary" sx={{ flexShrink: 0, lineHeight: 1.2 }}>
            {`· ${rmse.toFixed(1)} px`}
          </Typography>
        )}
      </Box>
    </Box>
  );
}
