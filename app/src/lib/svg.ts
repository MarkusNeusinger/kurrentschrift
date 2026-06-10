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
