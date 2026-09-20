// The Belege gallery: what a word search or a coverage cell turns the strip
// surface into — one tile per written WORD BOX that holds the filter, a page
// at a time.

import { Box, Button, Typography } from '@mui/material';

import type { EigenhandPfadBox, EigenhandStrip, EigenhandStripBox } from '@/lib/api';
import type { RovingList } from '@/hooks/useRovingList';
import { de, fmt } from '@/locales/admin';
import { CropTile } from '@/sections/admin/eigenhand/CropTile';
import type { LupeTarget } from '@/sections/admin/eigenhand/Lupe';
import type { Zoom } from '@/sections/admin/eigenhand/stripZoom';
import { stripBoxSpecimen } from '@/sections/admin/shell/focus';
import { paper } from '@/styles/paper';

/** How many tiles one page of the gallery shows, and what „mehr" adds. */
export const GALLERY_PAGE = 24;

/** One written word box, with the row it was cut from. */
export type Beleg = { row: EigenhandStrip; box: EigenhandStripBox };

export function StripGallery({
  hand,
  belege,
  shownCount,
  onMore,
  zoom,
  ohneLineatur,
  pfade,
  ampelByBox,
  onLupe,
  roving,
}: {
  hand: string;
  belege: Beleg[];
  shownCount: number;
  onMore: () => void;
  zoom: Zoom;
  ohneLineatur: boolean;
  pfade: boolean;
  /** The Tintentreue per box address, or null while the hand-wide read is
   * unknown — a tile then says nothing rather than „nicht beurteilt". */
  ampelByBox: ReadonlyMap<string, EigenhandPfadBox> | null;
  onLupe: (target: LupeTarget) => void;
  /** The gallery's one tab stop, owned by the panel so it outlives a filter. */
  roving: RovingList;
}) {
  const t = de.admin.eigenhand;
  return (
    <>
      {belege.length > 0 && (
        <Typography variant="caption" sx={{ display: 'block', mb: 1.5, color: paper.inkSoft }}>
          {t.stripBelegeIntro}
        </Typography>
      )}
      {/* A wrapping gallery of up to 24 tiles, each with a Lupe opener and,
          on a failed read, its own Erklärmarke — ~24–48 tab stops before
          this. Horizontal roving: ←/→ walk the tiles, Home/End jump. */}
      <Box {...roving.containerProps} sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
        {/* The hand belongs in every key: strip ids come from the frozen,
            hand-independent plan, and a tile reused across a hand switch
            would keep the previous hand's pixels on screen. */}
        {belege.slice(0, shownCount).map(({ row, box }) => (
          <CropTile
            key={`${hand}/${row.strip}/${row.fassung}/${box.index}`}
            rowProps={roving.rowProps(`${hand}/${row.strip}/${row.fassung}/${box.index}`)}
            hand={hand}
            row={row}
            box={box}
            zoom={zoom}
            ohneLineatur={ohneLineatur}
            pfade={pfade}
            ampel={ampelByBox?.get(stripBoxSpecimen(row.strip, row.fassung, box.index)) ?? null}
            onLupe={onLupe}
          />
        ))}
      </Box>
      {belege.length > shownCount && (
        <Button size="small" sx={{ mt: 1.5 }} onClick={onMore}>
          {fmt(t.stripMore, { count: Math.min(GALLERY_PAGE, belege.length - shownCount) })}
        </Button>
      )}
    </>
  );
}
