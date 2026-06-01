// Geometry for German-cursive practice sheets: the ruled guide lines
// (German: Hilfslinien) of a writing worksheet.
//
// Pure and framework-free: emits line primitives in millimetre page
// coordinates (origin top-left, y downwards — the SVG/screen convention).
// Both the on-screen SVG preview and the PDF writer consume the same output,
// so the printout matches the preview exactly.
//
// The writing row is the classic four-line system:
//   ascender top ── waist (x-height top) ── baseline ── descender bottom
// The waist+baseline pair bounds the x-height band (German: Mittelband); the
// ascender and descender bands sit above and below. Band heights follow a
// configurable ratio ascender : x-height : descender (architektur.md §15,
// vision.md §2): 2:1:2 is the default, with per-script presets below.
//
// Note: this is the geometry-only worksheet. The content-aware variant that
// typesets Kurrent glyphs into the lines (WeasyPrint backend, architektur.md
// §15 `POST /worksheet`) is a separate, later piece — this tool ships now,
// fully client-side.

export const A4 = { widthMm: 210, heightMm: 297 } as const;

export type LineRole = 'baseline' | 'waist' | 'ascender' | 'descender' | 'slant' | 'pen';

export interface Segment {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  role: LineRole;
}

// A small positioned text label (e.g. the pen-angle gauge degree).
export interface TextMark {
  x: number;
  y: number; // text baseline, mm (top-left origin)
  sizeMm: number;
  text: string;
  color?: string;
}

// Everything needed to render one page: line segments plus standalone labels.
export interface Lineature {
  segments: Segment[];
  marks: TextMark[];
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
  showPenAngle: boolean;
  penAngleDeg: number; // nib/pen-hold angle from the writing line (horizontal)
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
    // Pointed pen: stroke width comes from pressure (Schwellzug), not nib
    // angle, so the pen-angle gauge is off by default here.
    showPenAngle: false,
    penAngleDeg: 45,
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
    showPenAngle: false,
    penAngleDeg: 30,
  },
  {
    id: 'offenbacher',
    label: 'Offenbacher',
    note: '2 : 1 : 2 · leicht geneigt · Breitfeder ~35°',
    ratioAscender: 2,
    ratioXHeight: 1,
    ratioDescender: 2,
    xHeightMm: 5,
    rowGapMm: 7,
    marginMm: 15,
    showSlant: true,
    slantDeg: 12,
    slantSpacingMm: 12,
    // Broad nib: the pen-hold angle defines the thick/thin distribution.
    showPenAngle: true,
    penAngleDeg: 35,
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
  // Instructional reference (the pen-angle gauge): dark ink so it prints
  // reliably in black & white (the worksheet's normal output) — no brand
  // colour, which would just become a faint grey on a mono printer.
  pen: { color: '#1A1A17', widthMm: 0.35 },
};

// Render order: faint layers first so darker lines sit on top at crossings.
// Shared by the SVG preview and the PDF writer so the two never diverge.
export const DRAW_ORDER: LineRole[] = [
  'slant',
  'ascender',
  'descender',
  'waist',
  'baseline',
  'pen',
];

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

// Pen-angle gauge: a small reference mark in the top-left margin showing the
// nib/pen-hold angle relative to the writing line (horizontal), with a degree
// label. The nib edge tilts *downward* toward the first writing line (its tip
// just above the line), mirroring how the pen actually meets the paper so it
// can guide the hand. Lives entirely in the top margin (never crosses the
// writing lines). Returns null if disabled, non-finite, or the margin is too
// tight to show it legibly.
function penGauge(cfg: LineatureConfig, left: number, top: number): Lineature | null {
  if (!cfg.showPenAngle || !Number.isFinite(cfg.penAngleDeg)) return null;
  const gap = 1.5; // clearance between the gauge tip and the first line
  const edgeClear = 3; // clearance from the page top edge
  const theta = (cfg.penAngleDeg * Math.PI) / 180;
  const sin = Math.sin(theta);
  const cos = Math.cos(theta);
  const tipY = top - gap; // lowest point, just above the first writing line
  // Longest mark whose pivot still clears the page top edge, capped at 8 mm.
  const maxByEdge = sin > 1e-3 ? (tipY - edgeClear) / sin : 8;
  const len = Math.min(8, maxByEdge);
  if (!(len >= 3)) return null;
  const pivotY = tipY - len * sin; // pivot sits above the tip by the drop
  return {
    segments: [
      // horizontal reference (the writing-line direction)
      { x1: left, y1: pivotY, x2: left + len, y2: pivotY, role: 'pen' },
      // nib edge tilting down-right from the pivot to the tip near the line
      { x1: left, y1: pivotY, x2: left + len * cos, y2: tipY, role: 'pen' },
    ],
    marks: [
      { x: left + len + 2, y: pivotY + 1, sizeMm: 3, text: `${cfg.penAngleDeg}°`, color: ROLE_STYLES.pen.color },
    ],
  };
}

// Build all line segments + labels for one A4 page from a config. Defensive
// against pathological input (zero/negative sizes, extreme slants) so the live
// preview never hangs while the user is typing.
export function buildLineature(cfg: LineatureConfig): Lineature {
  const segs: Segment[] = [];
  const marks: TextMark[] = [];
  const empty: Lineature = { segments: segs, marks };

  // Bail out on non-finite input (e.g. a field the user has cleared mid-edit);
  // the preview just goes blank until the value is valid again.
  const inputs = [
    cfg.ratioAscender,
    cfg.ratioXHeight,
    cfg.ratioDescender,
    cfg.xHeightMm,
    cfg.rowGapMm,
    cfg.marginMm,
  ];
  if (!inputs.every(Number.isFinite)) return empty;

  const left = cfg.marginMm;
  const right = A4.widthMm - cfg.marginMm;
  const top = cfg.marginMm;
  const bottom = A4.heightMm - cfg.marginMm;

  const unit = cfg.xHeightMm / cfg.ratioXHeight; // mm per ratio part
  const asc = cfg.ratioAscender * unit;
  const desc = cfg.ratioDescender * unit;
  const rowH = asc + cfg.xHeightMm + desc;

  if (!(unit > 0) || !(rowH > 0) || right <= left || bottom <= top) return empty;

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

  const gauge = penGauge(cfg, left, top);
  if (gauge) {
    segs.push(...gauge.segments);
    marks.push(...gauge.marks);
  }

  return { segments: segs, marks };
}
