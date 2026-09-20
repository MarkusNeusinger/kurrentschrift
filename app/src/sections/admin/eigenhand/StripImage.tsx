// A strip — or one word cut out of it — as it stands in a tile.

import { Box, ButtonBase } from '@mui/material';

import { de, fmt } from '@/locales/admin';
import type { LupeTarget } from '@/sections/admin/eigenhand/Lupe';
import type { Zoom } from '@/sections/admin/eigenhand/stripZoom';
import { paper } from '@/styles/paper';

/**
 * A strip or word image at the shared zoom; a click hands it to the Lupe.
 *
 * `overlay` is drawn ON TOP at the same scale — the Streifen-Pfad, which is
 * positioned in the image's own pixels and therefore has to travel with it
 * through the zoom and the horizontal scroll.
 */
export function StripImage({
  url,
  alt,
  heightPx,
  zoom,
  onLupe,
  overlay,
}: {
  url: string;
  alt: string;
  heightPx: number;
  zoom: Zoom;
  onLupe: (target: LupeTarget) => void;
  overlay?: React.ReactNode;
}) {
  return (
    <Box sx={{ overflowX: 'auto', bgcolor: paper.hi, borderRadius: 1 }}>
      <Box sx={{ position: 'relative', display: 'inline-block', lineHeight: 0 }}>
        {/* The one way into the Lupe. It was `<Box component="img" onClick>`:
            no role, no tabIndex, no key handler — the gallery's only affordance
            was unreachable by keyboard entirely, and it slipped past
            `jsx-a11y/click-events-have-key-events` only because the JSX element
            is `Box` rather than `img`. A `ButtonBase` makes it a real button
            with the theme's focus ring and a name of its own (V24 „jeder
            Öffner"); the image keeps its optics, so the tile looks unchanged.
            `alt=""` because the button is already named — a screen reader would
            otherwise read the same words twice. */}
        <ButtonBase
          onClick={() => onLupe({ url, title: alt, heightPx })}
          aria-label={fmt(de.admin.eigenhand.stripLupeOpen, { was: alt })}
          sx={{ display: 'block', cursor: 'zoom-in', borderRadius: 1 }}
        >
          <Box
            component="img"
            src={url}
            alt=""
            sx={{ display: 'block', maxWidth: 'none', height: `${heightPx * zoom}px` }}
          />
        </ButtonBase>
        {overlay}
      </Box>
    </Box>
  );
}
