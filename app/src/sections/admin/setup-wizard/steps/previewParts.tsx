// Shared building block for the wizard's optimisation/verification surfaces:
// the crop-pixel silhouette overlay. Used by the inline Weg preview
// (WegPreview, Weg step) and the Übersicht verification panel (OverviewVerify)
// so both render the comparison identically.
//
// The score chip and the per-category penalty breakdown moved to
// sections/admin/quality/scoreParts — they are shown outside the wizard too
// (Diagnose modal, Buchstaben overview) and had started to drift.

import { ringsToPathD } from '@/lib/svg';
import type { WrittenPreviewData } from '@/lib/api';

// Silhouette rings (crop pixels) as one evenodd SVG path per pen-stroke — loop
// counters stay open. silhouette_px is the per-stroke ring list from the
// preview payload (the optimized render in crop coordinates, aligned to the crop
// image so it overlays exactly).
export function SilhouetteSvg({
  data,
  w,
  h,
  fill,
  fillOpacity = 1,
}: {
  data: WrittenPreviewData;
  w: number;
  h: number;
  fill: string;
  fillOpacity?: number;
}) {
  const strokes = data.silhouette_px ?? [];
  return (
    <svg width={w} height={h} viewBox={`0 0 ${data.crop_size.w} ${data.crop_size.h}`} style={{ display: 'block' }}>
      {strokes.map((rings, i) => (
        <path key={i} d={ringsToPathD(rings)} fill={fill} fillOpacity={fillOpacity} fillRule="evenodd" />
      ))}
    </svg>
  );
}
