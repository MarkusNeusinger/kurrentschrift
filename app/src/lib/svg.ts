// SVG path helpers for the backend's ring geometry (capsule-union silhouettes).

export type Ring = Array<[number, number]>;

// All rings of one stroke as a single path `d` (subpath per ring) — rendered
// with fill-rule evenodd the holes (loop counters) stay open without resolving
// exterior/hole pairing client-side. `flipY` negates y for template
// coordinates (y up) inside SVG (y down).
export function ringsToPathD(rings: Ring[], flipY = false): string {
  const sign = flipY ? -1 : 1;
  return rings
    .filter((ring) => ring.length > 2)
    .map(
      (ring) => ring.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x},${sign * y}`).join(' ') + ' Z',
    )
    .join(' ');
}

// Polyline → SVG path `d`, optionally x-translated by `tx`. The single home for
// the reveal centerline path — the three "as written" surfaces used to each
// redeclare this (`pathD` / `lineD`).
//
// `flipY` negates y for template coordinates (y up) inside SVG (y down), and it
// defaults to TRUE where `ringsToPathD`'s defaults to false — an asymmetry that
// silently mirrored geometry wherever a surface drew both kinds of item under
// one y-flipping transform: the letters (rings, not negated) landed right side
// up, the generated connectors (polylines, negated) were flipped a second time
// and appeared as loose strokes UNDER the baseline. Pass `flipY: false`
// whenever the enclosing `<g>` already flips — the flag is not cosmetic.
export function polylineToPathD(points: Ring, tx = 0, flipY = true): string {
  const sign = flipY ? -1 : 1;
  return points.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x + tx},${sign * y}`).join(' ');
}
