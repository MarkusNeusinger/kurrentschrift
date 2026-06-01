// Lineature (Hilfslinien) geometry for German cursive practice sheets.
//
// Pure and framework-free: emits line primitives in millimetre page
// coordinates (origin top-left, y downwards — the SVG/screen convention).
// Both the on-screen SVG preview and the PDF writer consume the same output,
// so the printout matches the preview exactly.
//
// The writing row is the classic four-line system:
//   ascender top ── waist (x-height top) ── baseline ── descender bottom
// The waist+baseline pair bounds the Mittelband (x-height); the ascender and
// descender bands sit above and below. Band heights follow a configurable
// ratio ascender : x-height : descender (architektur.md §15, vision.md §2):
// 2:1:2 is the default, with per-script presets below.
//
// Note: this is the geometry-only worksheet (Lineatur). The content-aware
// variant that typesets Kurrent glyphs into the lines (WeasyPrint backend,
// architektur.md §15 `POST /worksheet`) is a separate, later piece — this
// tool ships now, fully client-side.

export const A4 = { widthMm: 210, heightMm: 297 } as const;

export type LineRole = 'baseline' | 'waist' | 'ascender' | 'descender' | 'slant';

export interface Segment {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  role: LineRole;
}

export interface LineatureConfig {
  // band ratio (ascender : x-height : descender)
  ratioAscender: number;
  ratioXHeight: number;
  ratioDescender: number;
  xHeightMm: number; // physical height of the Mittelband (drives overall scale)
  rowGapMm: number; // blank gap between consecutive writing rows
  marginMm: number; // page margin on all four sides
  showSlant: boolean;
  slantDeg: number; // slant from vertical; 0 = upright, positive = leans right
  slantSpacingMm: number; // horizontal spacing between slant guides
}

export interface ScriptPreset extends LineatureConfig {
  id: string;
  label: string;
  note: string;
}

// The three start scripts (naming-und-setup.md §"Start-Schriftfamilien").
// Kurrent is the project's baseline (pointed pen, strong slant); Sütterlin is
// upright with an even stroke and the famous 1:1:1 proportion; the Offenbacher
// script (Rudolf Koch, broad nib) sits between them with a gentle slant.
export const PRESETS: ScriptPreset[] = [
  {
    id: 'kurrent',
    label: 'Kurrent',
    note: '2 : 1 : 2 · ~30° geneigt · Spitzfeder',
    ratioAscender: 2,
    ratioXHeight: 1,
    ratioDescender: 2,
    xHeightMm: 5,
    rowGapMm: 6,
    marginMm: 15,
    showSlant: true,
    slantDeg: 30,
    slantSpacingMm: 10,
  },
  {
    id: 'suetterlin',
    label: 'Sütterlin',
    note: '1 : 1 : 1 · aufrecht · gleichmäßige Strichstärke',
    ratioAscender: 1,
    ratioXHeight: 1,
    ratioDescender: 1,
    xHeightMm: 6,
    rowGapMm: 6,
    marginMm: 15,
    showSlant: false,
    slantDeg: 0,
    slantSpacingMm: 10,
  },
  {
    id: 'offenbacher',
    label: 'Offenbacher',
    note: '2 : 1 : 2 · leicht geneigt · Breitfeder',
    ratioAscender: 2,
    ratioXHeight: 1,
    ratioDescender: 2,
    xHeightMm: 5,
    rowGapMm: 7,
    marginMm: 15,
    showSlant: true,
    slantDeg: 12,
    slantSpacingMm: 12,
  },
];

export interface RoleStyle {
  color: string; // hex
  widthMm: number; // stroke width in mm
  dash?: [number, number]; // dash pattern in mm (on, off)
}

// Typographic hierarchy: the baseline is the anchor (darkest, thickest), the
// waist marks the x-height (medium), ascender/descender bounds are quiet dashed
// hairlines, and slant guides are the faintest layer. Colours track the
// warm-paper palette in theme.ts.
export const ROLE_STYLES: Record<LineRole, RoleStyle> = {
  baseline: { color: '#1A1A17', widthMm: 0.35 },
  waist: { color: '#6B6A63', widthMm: 0.25 },
  ascender: { color: '#B8B6AE', widthMm: 0.18, dash: [1.6, 1.6] },
  descender: { color: '#B8B6AE', widthMm: 0.18, dash: [1.6, 1.6] },
  slant: { color: '#D6D4CB', widthMm: 0.15, dash: [1, 1.6] },
};

// Liang–Barsky segment clip against an axis-aligned rectangle (xmin<xmax,
// ymin<ymax). Returns the clipped segment, or null if it lies fully outside.
function clipToRect(
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  xmin: number,
  ymin: number,
  xmax: number,
  ymax: number,
): Omit<Segment, 'role'> | null {
  let t0 = 0;
  let t1 = 1;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const p = [-dx, dx, -dy, dy];
  const q = [x1 - xmin, xmax - x1, y1 - ymin, ymax - y1];
  for (let i = 0; i < 4; i++) {
    if (p[i] === 0) {
      if (q[i] < 0) return null; // parallel and outside this edge
    } else {
      const r = q[i] / p[i];
      if (p[i] < 0) {
        if (r > t1) return null;
        if (r > t0) t0 = r;
      } else {
        if (r < t0) return null;
        if (r < t1) t1 = r;
      }
    }
  }
  return { x1: x1 + t0 * dx, y1: y1 + t0 * dy, x2: x1 + t1 * dx, y2: y1 + t1 * dy };
}

// Build all line segments for one A4 page from a config. Defensive against
// pathological input (zero/negative sizes, extreme slants) so the live preview
// never hangs while the user is typing.
export function buildLineature(cfg: LineatureConfig): Segment[] {
  const segs: Segment[] = [];

  const left = cfg.marginMm;
  const right = A4.widthMm - cfg.marginMm;
  const top = cfg.marginMm;
  const bottom = A4.heightMm - cfg.marginMm;

  const unit = cfg.xHeightMm / cfg.ratioXHeight; // mm per ratio part
  const asc = cfg.ratioAscender * unit;
  const desc = cfg.ratioDescender * unit;
  const rowH = asc + cfg.xHeightMm + desc;

  if (!(unit > 0) || !(rowH > 0) || right <= left || bottom <= top) return segs;

  const tan = Math.tan((cfg.slantDeg * Math.PI) / 180);

  let rowTop = top;
  let rowGuard = 0;
  while (rowTop + rowH <= bottom + 1e-6 && rowGuard < 200) {
    rowGuard++;
    const yAscTop = rowTop;
    const yWaist = rowTop + asc;
    const yBase = yWaist + cfg.xHeightMm;
    const yDescBot = yBase + desc;

    segs.push({ x1: left, y1: yAscTop, x2: right, y2: yAscTop, role: 'ascender' });
    segs.push({ x1: left, y1: yWaist, x2: right, y2: yWaist, role: 'waist' });
    segs.push({ x1: left, y1: yBase, x2: right, y2: yBase, role: 'baseline' });
    segs.push({ x1: left, y1: yDescBot, x2: right, y2: yDescBot, role: 'descender' });

    if (cfg.showSlant && cfg.slantSpacingMm > 0) {
      // Slant guides span the full row height. Screen y grows downward, so the
      // top point (smaller y) shifts right by dx for a right-leaning script.
      // dx = 0 (upright) yields vertical guides, which is also useful.
      const dx = rowH * tan;
      const startXb = Math.min(left, left - dx) - cfg.slantSpacingMm;
      const endXb = Math.max(right, right - dx) + cfg.slantSpacingMm;
      let slantGuard = 0;
      for (let xb = startXb; xb <= endXb && slantGuard < 1000; xb += cfg.slantSpacingMm) {
        slantGuard++;
        const clipped = clipToRect(
          xb,
          yDescBot,
          xb + dx,
          yAscTop,
          left,
          yAscTop,
          right,
          yDescBot,
        );
        if (clipped) segs.push({ ...clipped, role: 'slant' });
      }
    }

    rowTop = yDescBot + cfg.rowGapMm;
  }

  return segs;
}
