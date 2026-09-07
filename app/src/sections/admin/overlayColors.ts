// Functional colors for the admin work surfaces (the dark chart canvas and the
// white glyph crops). These are deliberately OUTSIDE the paper & ink identity
// tokens: per style-guide §8 the work surfaces stay neutral so the scan/crop
// reads true, and the overlay colors are signal colors on top of that — state
// markers, not identity. Shared by the chart overlay and the setup wizard
// canvas (eraser/draft/canvas background).

export const overlay = {
  // Locked (finished) glyphs read green; the active one stays orange; unfinished
  // ones are blue (dashed on the chart).
  locked: '#37c871',
  active: '#ffae00',
  idle: '#5da8ff',
  // Freeform eraser strokes (Ausschluss/Radierer).
  eraser: '#ff6b35',
  // Manual ink brush strokes (Tinten-Pinsel) — the eraser's positive twin.
  ink: '#2b50e0',
  // Inserted donor cell (Zelle einsetzen): the placement rect on the crop and
  // the donor-picker selection. Distinct from eraser/ink/draft/slant.
  patch: '#c057ff',
  // In-progress drawing (the rubber-band rect while drawing a new bbox; the
  // wizard's slant handles use the same accent).
  draft: '#00d2ff',
  // Dark outline on the orange resize grips so they read on any background.
  gripOutline: '#1a1200',
  // The neutral dark canvas behind the chart scan / wizard crop.
  canvasBg: '#111',
} as const;

// The Landmarken-Linse's own set (optimierungs-werkbank.md §8): one hue per
// DETECTED structure, drawn over black-brown ink on a white crop. Chosen apart
// from the palette above rather than reused from it, because these mean
// something else — `overlay.locked` says "this glyph is finished", and a green
// ring on a crossing would read as "this crossing is fine", which the lens
// never claims. All seven clear WCAG AA (>= 3:1) against the white work
// surface, and none of them is the ink's own near-black.
export const landmarkColors = {
  crossing: '#d81b60', // Kreuzung — a ring at the point
  retrace: '#0277bd', // Retrace-Zone — the path shaded along itself
  touch: '#00838f', // Berührung — the same shading, cooler: past, not over
  overlap: '#6a1b9a', // Verschmelzung — hatched, two strokes in one place
  lift: '#ef6c00', // Absetzen — a tick where the pen came down again
  corner: '#2e7d32', // Umkehrecke — a square on the anchor
  loop: '#c62828', // Kringel — a circle scaled to D0
} as const;

export type LandmarkColorKey = keyof typeof landmarkColors;
