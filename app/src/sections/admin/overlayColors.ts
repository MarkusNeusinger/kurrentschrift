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
