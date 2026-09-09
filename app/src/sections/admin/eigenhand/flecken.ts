// The eraser's arithmetic — where a click lands and what it does there.
//
// Kept beside the panel rather than inside it because this is where an eraser
// can go wrong invisibly: a circle placed against the wrong origin or scale
// still LOOKS like a circle, and the mask it writes would paint paper over the
// author's own ink somewhere he never clicked. So the millimetre conversion
// and the click semantics are pinned by tests instead of by the eye.
//
// One coordinate system throughout: millimetres from the strip crop's own
// top-left corner, exactly what `core/eigenhand/flecken.py` stores and what
// the server applies on read. The zoom is a display factor and never reaches
// the data.

import type { EigenhandFleck } from '@/lib/api';

// The brush sizes the author picks from. A toner speck is ≲ 0.5 mm across, so
// 0.3 mm covers a single one, 0.6 mm a fat one with its halo, and 1.0 mm a
// cluster. 1.5 mm is for the smear class the first real sheet showed (B0001,
// S0181: several particles fused into one blot 2.3 mm across) — the automatic
// pass leaves it to the brush by design, and one click should cover it rather
// than a row of small ones. Anything larger is no longer „a speck" and belongs
// to the Siebung, not to the eraser; the server's ceiling stays 3.0 mm.
export const BRUSH_RADII_MM = [0.3, 0.6, 1.0, 1.5] as const;
export type BrushRadiusMm = (typeof BRUSH_RADII_MM)[number];

// The server's own ceiling (`core.eigenhand.flecken.FLECK_MAX_R_MM`), repeated
// here so the view can refuse before the round trip rather than after it.
export const FLECK_MAX_R_MM = 3.0;

export interface PointMm {
  x_mm: number;
  y_mm: number;
}

/** Display pixels per millimetre: the strip's own scale times the shown zoom. */
export function displayScale(dpi: number, zoom: number): number {
  return (dpi / 25.4) * zoom;
}

/**
 * A pointer position inside the image, in the strip's millimetres.
 *
 * `offsetX`/`offsetY` are relative to the image element, which is drawn at
 * `displayScale` — so the conversion is one division and the origin is the
 * image corner, the same corner the mask is measured from.
 */
export function pointAt(offsetX: number, offsetY: number, scale: number): PointMm {
  return { x_mm: offsetX / scale, y_mm: offsetY / scale };
}

/**
 * The index of the circle under a point, or -1. The LAST match wins: circles
 * are drawn in order, so the one on top is the one the eye is aiming at.
 */
export function circleAt(circles: readonly EigenhandFleck[], point: PointMm): number {
  let hit = -1;
  circles.forEach((circle, index) => {
    const dx = circle.x_mm - point.x_mm;
    const dy = circle.y_mm - point.y_mm;
    if (dx * dx + dy * dy <= circle.r_mm * circle.r_mm) hit = index;
  });
  return hit;
}

/**
 * One click: on an existing circle it removes that circle (the automatic ones
 * too — a detector finding is a proposal, and taking one back has to be as
 * cheap as making one), anywhere else it adds a hand circle.
 *
 * Returns the same array when nothing changes, so a caller can tell a no-op
 * from an edit without comparing contents.
 */
export function toggleAt(
  circles: readonly EigenhandFleck[],
  point: PointMm,
  radiusMm: number,
): EigenhandFleck[] {
  const hit = circleAt(circles, point);
  if (hit >= 0) return circles.filter((_, index) => index !== hit);
  return [
    ...circles,
    {
      x_mm: round3(point.x_mm),
      y_mm: round3(point.y_mm),
      r_mm: round3(Math.min(radiusMm, FLECK_MAX_R_MM)),
      quelle: 'hand',
    },
  ];
}

/** Is this point inside the strip at all — a click on the margin adds nothing. */
export function insideStrip(point: PointMm, widthMm: number, heightMm: number): boolean {
  return point.x_mm >= 0 && point.y_mm >= 0 && point.x_mm <= widthMm && point.y_mm <= heightMm;
}

function round3(value: number): number {
  return Math.round(value * 1000) / 1000;
}
