// The Bahn over the picture: the stored pen path, drawn in the image's own
// pixel frame.

import { Box } from '@mui/material';

import type { EigenhandBahn } from '@/sections/admin/eigenhand/pfadBahnen';
import type { Zoom } from '@/sections/admin/eigenhand/stripZoom';
import { PathOverlay } from '@/sections/admin/shell/PathOverlay';
import type { Stroke } from '@/sections/admin/shell/pathOverlay';

/**
 * The followed pen paths laid over a strip image — or over one word cut out of
 * it. The stored registration is the STRIP's own pixel frame, so a word crop
 * is served by subtracting that crop's rectangle: one stored frame, both views,
 * and nothing about the crop's padding has to be remembered with the path.
 *
 * `EigenhandBahn`, not `EigenhandPfad`: since format 2 a stored entry may be a
 * Skip-Eintrag with no frame and no scale at all, and a layer is not where that
 * is noticed. `bahnenOf` takes them out where the list is read.
 */
export function PfadLayer({
  pfade,
  widthPx,
  heightPx,
  zoom,
  originX = 0,
  originY = 0,
  showIndex = false,
}: {
  pfade: EigenhandBahn[];
  widthPx: number;
  heightPx: number;
  zoom: Zoom;
  originX?: number;
  originY?: number;
  showIndex?: boolean;
}) {
  return (
    <Box
      component="svg"
      viewBox={`0 0 ${widthPx} ${heightPx}`}
      width={widthPx * zoom}
      height={heightPx * zoom}
      // Over the image, never in its way: the strip's own click opens the Lupe.
      sx={{ position: 'absolute', left: 0, top: 0, pointerEvents: 'none' }}
    >
      {pfade.map((pfad) => {
        const xh = pfad.xh_px;
        const tx = pfad.registration_px.tx - originX;
        const baseline = pfad.registration_px.baseline_row + pfad.registration_px.ty - originY;
        return (
          <g key={pfad.box_index} transform={`matrix(${xh} 0 0 ${-xh} ${tx} ${baseline})`}>
            <PathOverlay
              strokes={pfad.strokes as Stroke[]}
              // One DISPLAYED pixel in path units — the image is scaled by the
              // shared zoom, so a hairline stays a hairline at ¼ and at 2×.
              unit={1 / (zoom * xh)}
              detail
              showIndex={showIndex}
            />
          </g>
        );
      })}
    </Box>
  );
}
