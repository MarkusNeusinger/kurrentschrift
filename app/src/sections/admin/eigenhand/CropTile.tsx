// One tile of the Belege gallery: the written word a coverage cell or a search
// led to, cut out of its strip.

import { Box, Chip, CircularProgress, Stack, Typography } from '@mui/material';
import { useRef } from 'react';

import type { EigenhandPfadBox, EigenhandStrip, EigenhandStripBox } from '@/lib/api';
import { InfoHint } from '@/components/InfoHint';
import { de } from '@/locales/admin';
import { AmpelChip } from '@/sections/admin/eigenhand/AmpelChip';
import type { LupeTarget } from '@/sections/admin/eigenhand/Lupe';
import { bahnenOf } from '@/sections/admin/eigenhand/pfadBahnen';
import { PfadLayer } from '@/sections/admin/eigenhand/PfadLayer';
import { PfadRohzahlenChips } from '@/sections/admin/eigenhand/PfadRohzahlenChips';
import { StripImage } from '@/sections/admin/eigenhand/StripImage';
import { TINTENTREUE_GRUND } from '@/sections/admin/eigenhand/stripBoxRows';
import type { Zoom } from '@/sections/admin/eigenhand/stripZoom';
import { useNearViewport } from '@/sections/admin/eigenhand/useNearViewport';
import { useStripImage } from '@/sections/admin/eigenhand/useStripImage';
import { useStripPfade } from '@/sections/admin/eigenhand/useStripPfade';
import { mono, paper } from '@/styles/paper';

/** One written word that holds the filter — fetched once it comes near the viewport. */
export function CropTile({
  hand,
  row,
  box,
  zoom,
  ohneLineatur,
  pfade: wantPfade,
  ampel,
  onLupe,
  rowProps,
}: {
  hand: string;
  row: EigenhandStrip;
  box: EigenhandStripBox;
  zoom: Zoom;
  ohneLineatur: boolean;
  pfade: boolean;
  /** This box's Tintentreue from the hand-wide read, or null where that read
   * has not answered — a tile then shows no chip at all rather than claiming
   * „nicht beurteilt", which is a verdict of its own. */
  ampel: EigenhandPfadBox | null;
  onLupe: (target: LupeTarget) => void;
  /** This tile's place in the gallery's Roving-Liste. */
  rowProps: Record<string, string>;
}) {
  const t = de.admin.eigenhand;
  const ref = useRef<HTMLDivElement | null>(null);
  const near = useNearViewport(ref);
  const { url, loading, error } = useStripImage(hand, row.strip, row.fassung, box.index, near, ohneLineatur);
  // Gated on the SAME „near the viewport" the image is: with the layer on, a
  // page of 24 tiles asks for exactly the paths of the tiles one can see.
  const cut = box.rect_px ?? null;
  const pfade = useStripPfade(hand, row.strip, row.fassung, wantPfade && near && cut !== null);
  const drawn = bahnenOf(pfade.pfade).filter((p) => p.box_index === box.index);
  const title = `${row.strip} · ${row.fassung} · ${box.word}`;
  return (
    <Box
      ref={ref}
      {...rowProps}
      sx={{ border: 1, borderColor: 'divider', borderRadius: 1, p: 1, maxWidth: '100%', minHeight: '4rem' }}
    >
      <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 0.5 }}>
        <Typography variant="caption" sx={{ color: paper.ink, fontWeight: 600 }}>
          {box.word}
        </Typography>
        <Typography variant="caption" sx={{ color: paper.inkSoft }}>
          {row.strip} · {row.fassung}
        </Typography>
        {loading && <CircularProgress size={12} />}
      </Stack>
      {/* The box's own verdict, beside its picture. The tile lost this when the
          free-standing „Maske geändert" chip gave way to the Ampel in the list
          (#643); §7.2 wants it on both surfaces, so the hand-wide read reaches
          down here too. The mask state stands BESIDE the step where the step
          does not already say it — the Ampel shows one grey state at a time. */}
      {ampel && (
        <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center', flexWrap: 'wrap', rowGap: 0.5, mb: 0.5 }}>
          <AmpelChip urteil={ampel.tintentreue} />
          {ampel.stale && ampel.tintentreue.grund !== TINTENTREUE_GRUND.maske && (
            <Chip size="small" color="warning" variant="outlined" label={t.pfadStale} sx={{ flexShrink: 0 }} />
          )}
          <Typography variant="caption" sx={{ color: paper.inkSoft }}>
            {ampel.tintentreue.grund}
          </Typography>
        </Stack>
      )}
      {url ? (
        <StripImage
          url={url}
          alt={title}
          heightPx={row.height_px}
          zoom={zoom}
          onLupe={onLupe}
          overlay={
            drawn.length > 0 && cut ? (
              <PfadLayer
                pfade={drawn}
                widthPx={cut[2] - cut[0]}
                heightPx={cut[3] - cut[1]}
                zoom={zoom}
                originX={cut[0]}
                originY={cut[1]}
                showIndex
              />
            ) : undefined
          }
        />
      ) : (
        // The strip's height is known before a byte arrives, so the tile takes
        // its final height at once: tiles below the fold then really ARE below
        // the fold, and the observer above decides on the true layout instead
        // of on a row of collapsed captions.
        <Box sx={{ height: `${row.height_px * zoom}px`, minWidth: '8rem', bgcolor: paper.hi, borderRadius: 1 }} />
      )}
      {/* The same numbers as in the strip view, under the one Kasten this tile
          IS — the gallery is where a coverage cell leads, so the question „did
          the follower get this word" is asked here just as often. The tile IS
          the box, so the reading needs no prefix to say which one it belongs
          to. */}
      {drawn.length > 0 && <PfadRohzahlenChips pfade={drawn} showBox={false} />}
      {/* The layer is on and nothing is drawn: say WHICH of the empty answers
          this is, rather than leaving the tile looking as if the switch had
          not worked. */}
      {wantPfade && drawn.length === 0 && !pfade.loading && !pfade.error && (
        <Typography variant="caption" sx={{ display: 'block', mt: 0.5, color: paper.inkSoft }}>
          {cut === null ? t.pfadNoBox : pfade.pfade === null ? t.pfadNoneShort : t.pfadNotInBox}
        </Typography>
      )}
      {/* A tile in a gallery has no room for a fold-out, so the sentence stands
          alone and the raw line sits behind the tile's one InfoHint. It used to
          ride on a native `title=`, which is a hover and nothing else — and the
          raw line is what says WHICH request failed. */}
      {error && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, flexWrap: 'wrap' }}>
          <Typography variant="caption" sx={{ color: 'warning.main' }}>
            {t.stripImagesError} {error.sentence}
          </Typography>
          <InfoHint title={t.stripImagesError} label={t.stripErrorAria}>
            <Typography variant="body2" sx={{ fontFamily: mono, wordBreak: 'break-word' }}>
              {error.detail}
            </Typography>
          </InfoHint>
        </Box>
      )}
    </Box>
  );
}
