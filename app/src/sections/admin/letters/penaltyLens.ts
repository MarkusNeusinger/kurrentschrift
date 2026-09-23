// The pure half of the Abzugs-Linse (optimierungs-werkbank.md §9): which mark a
// deduction site gets, what a legend chip says, when the stamp and today's
// re-score disagree, how big a mark is drawn — everything the panel and the
// overlay decide that does not need a DOM, kept here so it can be pinned by a
// test instead of by eye.
//
// The payload is the metric's own, in crop pixels (api/schemas.py
// `PenaltySitesOut`): the lens never recomputes a number, it only chooses how
// to show one. The rule every choice below serves: the sites of a category add
// up to the number shown for it, so nothing here rounds a value differently
// from the four places the payload apportioned it to.

import type {
  PenaltyCategoryKey,
  PenaltyCategoryOut,
  PenaltyFrameOut,
  PenaltyPinOut,
  PenaltySiteOut,
} from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { PENALTY_EPS } from '@/sections/admin/quality/scoreColors';
import type { PenaltyRef } from '@/sections/admin/shell/model';

/** The six deductions, in the metric's own order (`components`). */
export const PENALTY_CATEGORIES: readonly PenaltyCategoryKey[] = [
  'smoothness',
  'verticality',
  'corner',
  'collinearity',
  'retrace',
  'coverage',
];

/**
 * What a mark looks like. The SHAPE is the channel that tells categories apart
 * — every mark is drawn in the one penalty hue (`styles/paper.ts` `penalty`),
 * so a reader who cannot tell colours apart loses nothing (Strichart-Regel,
 * design-system.md §2). `none` is a site without a place: it counts in the
 * number and is listed, but nothing is painted for it.
 */
export type MarkerShape =
  | 'band' // Glätte — a band along the centreline, as wide as its share
  | 'bracket' // Senkrechte — a bracket beside the run, the ideal vertical dashed
  | 'square' // Ecken — the Landmarken corner square, same anchor
  | 'ring' // Kreuzungsflucht — a ring plus the two fitted lines
  | 'crosshatch' // Doppelzug — missed ink in the retrace zone
  | 'hatch' // Deckungslücke/Dice — deep missed ink
  | 'stipple' // Deckungslücke/Dice — render over paper
  | 'edgeDots' // Deckungslücke/Chamfer — boundary pixels
  | 'whiskers' // Deckungslücke/Geo — feelers from the centreline to the skeleton
  | 'none';

/** The legend's shape per category — Deckungslücke's first (and largest-area) mark stands for it. */
export const CATEGORY_SHAPE: Record<PenaltyCategoryKey, MarkerShape> = {
  smoothness: 'band',
  verticality: 'bracket',
  corner: 'square',
  collinearity: 'ring',
  retrace: 'crosshatch',
  coverage: 'hatch',
};

// Deckungslücke is three factors, and each gets its own mark: a Dice miss is
// pixels, a Chamfer part is a boundary, a Geo part is a distance.
const COVERAGE_SHAPE: Record<string, MarkerShape> = {
  missed_ink: 'hatch',
  excess_render: 'stipple',
  edge: 'edgeDots',
  off_skeleton: 'whiskers',
};

// Which factor of the coverage gate a Deckungslücke site belongs to.
const COVERAGE_PART: Record<string, 'dice' | 'chamfer' | 'geo'> = {
  missed_ink: 'dice',
  excess_render: 'dice',
  rim: 'dice',
  edge: 'chamfer',
  off_skeleton: 'geo',
};

export const isLocated = (site: PenaltySiteOut): site is PenaltySiteOut & { x: number; y: number } =>
  site.x !== null && site.y !== null;

/**
 * Whether a site carries a part of its number at the four places shown. One
 * apportioned 0.0000 is real but adds nothing to the number beside it — the
 * image leaves it out and the list counts it, so the dozens of such edge
 * pieces on a wide letter do not bury the sites that make up the number.
 */
export const isDrawn = (site: PenaltySiteOut): boolean => site.value > 0;

/** The marks drawn in the crop's pixel grid (cells, boundary dots) rather than along the centreline. */
export const isPixelShape = (shape: MarkerShape): boolean =>
  shape === 'hatch' || shape === 'stipple' || shape === 'crosshatch' || shape === 'edgeDots';

/**
 * How far the deviation of a Senkrechte run is blown up to be seen at all:
 * the measured wander is sub-pixel (0.03–0.2 px on the frozen letters), so
 * drawn true it would be the ideal vertical itself.
 */
export const VERTICAL_EXAGGERATION = 20;
/**
 * …but never further than this share of the x-height. A few letters wander a
 * whole pixel or two (g, Y), and ×20 swung their drawn run clean across the
 * bowl it belongs to — a mark that points at the wrong ink. Such a run is
 * blown up less, and the detail names the factor actually used.
 */
export const VERTICAL_SWING_UNITS = 0.15;

/**
 * The factor one Senkrechte run is drawn at: ×20, or less where ×20 would
 * swing further than `VERTICAL_SWING_UNITS` of an x-height — a whole number,
 * at least ×1, so the label is a factor a reader can say out loud.
 */
export function verticalExaggeration(deviations: readonly number[], unitPx: number): number {
  const widest = deviations.reduce((max, d) => Math.max(max, Math.abs(d)), 0);
  if (!(widest > 0) || !(unitPx > 0)) return VERTICAL_EXAGGERATION;
  const fits = Math.floor((VERTICAL_SWING_UNITS * unitPx) / widest);
  return Math.max(1, Math.min(VERTICAL_EXAGGERATION, fits));
}

/** The mark one site gets. */
export function siteShape(category: PenaltyCategoryKey, site: PenaltySiteOut): MarkerShape {
  if (!isLocated(site)) return 'none';
  if (category === 'coverage') return COVERAGE_SHAPE[site.kind] ?? 'none';
  return CATEGORY_SHAPE[category];
}

/** Dice · Chamfer · Geo for a Deckungslücke site; null for every other category. */
export function coveragePart(category: PenaltyCategoryKey, site: PenaltySiteOut): 'dice' | 'chamfer' | 'geo' | null {
  return category === 'coverage' ? (COVERAGE_PART[site.kind] ?? null) : null;
}

/** Identity of one site across the image, the lists and the selection. */
export const siteKey = (category: PenaltyCategoryKey, index: number): string => `${category}#${index}`;

// ------------------------------------------------------------------ numbers

/** The four places every value of the lens is shown at — the precision the sites were apportioned to. */
export const fourPlaces = (value: number): string => value.toFixed(4);

/** A raw number of a site, trailing zeros dropped — `80.6`, not `80.6000`. */
export function formatNumber(value: number | string | boolean | null): string {
  if (typeof value === 'boolean') return value ? 'ja' : 'nein';
  if (typeof value === 'number') return String(Number(value.toFixed(4)));
  return String(value);
}

/** The site's part of its category as a whole percentage, from the payload's own unrounded ratio. */
export const sharePercent = (site: PenaltySiteOut): number => Math.round(site.share * 100);

// ------------------------------------------------------------------ legend

export interface CategoryChip {
  key: PenaltyCategoryKey;
  label: string;
  value: number;
  applicable: boolean;
  inSync: boolean;
  /** Sites with a place and a part of the number — what the image draws and the chip filters. */
  located: number;
  /** The summed value of the sites without one, to four places. */
  unlocatedValue: number;
  /** A chip is a FILTER only where there is something to draw; otherwise a plain label. */
  filterable: boolean;
  text: string;
}

function countText(count: number): string {
  const t = de.admin.letters.penalties;
  if (count === 0) return t.sitesNone;
  return count === 1 ? t.sitesOne : fmt(t.sitesMany, { count });
}

/**
 * The legend chips — which are also the „Abzüge (neu gemessen)" line: worst
 * first like the list's own „Abzüge:" line, then what does not apply, in the
 * metric's order. „nicht anwendbar" instead of 0, because a term that never
 * applied was not measured as perfect (Ehrliche Leerzustände).
 */
export function categoryChips(sites: Record<PenaltyCategoryKey, PenaltyCategoryOut>): CategoryChip[] {
  const t = de.admin.letters.penalties;
  const chips = PENALTY_CATEGORIES.map((key): CategoryChip => {
    const category = sites[key];
    const label = de.wizard.optimize.cat[key];
    const located = category.sites.filter((site) => isLocated(site) && isDrawn(site)).length;
    // Integer ten-thousandths, so the sum is exact at the four shown places.
    const unlocatedUnits = category.sites
      .filter((site) => !isLocated(site))
      .reduce((sum, site) => sum + Math.round(site.value * 10_000), 0);
    const unlocatedValue = unlocatedUnits / 10_000;
    let text: string;
    if (!category.applicable) text = `${label} · ${t.notApplicable}`;
    else {
      const parts = [`${label} ${fourPlaces(category.value)}`, countText(located)];
      if (unlocatedUnits > 0) parts.push(`${fourPlaces(unlocatedValue)} ${t.noPlace}`);
      text = parts.join(' · ');
    }
    return {
      key,
      label,
      value: category.value,
      applicable: category.applicable,
      inSync: category.in_sync,
      located,
      unlocatedValue,
      filterable: category.applicable && located > 0,
      text,
    };
  });
  const order = (key: PenaltyCategoryKey) => PENALTY_CATEGORIES.indexOf(key);
  return chips.sort((a, b) => {
    if (a.applicable !== b.applicable) return a.applicable ? -1 : 1;
    if (a.applicable && b.value !== a.value) return b.value - a.value;
    return order(a.key) - order(b.key);
  });
}

export interface StampDrift {
  key: PenaltyCategoryKey;
  label: string;
  stamped: number;
  measured: number;
}

/**
 * The categories whose STAMPED value (what the list shows, from the last
 * derivation) differs from today's re-score by more than the list's own
 * epsilon — the „gespeichert: …" line. Nothing when the two agree, and
 * nothing for a category the stamp predates: an absent number is not a drift.
 */
export function stampDrift(
  stamped: Record<string, number> | null,
  components: Record<string, number> | null,
): StampDrift[] {
  if (!stamped || !components) return [];
  return PENALTY_CATEGORIES.flatMap((key) => {
    const before = stamped[key];
    const now = components[key];
    if (typeof before !== 'number' || typeof now !== 'number') return [];
    // The comparison runs in integer ten-thousandths: both numbers are four-place
    // values, and `0.1767 - 0.1717` in floating point is not `0.005` exactly.
    const drift = Math.abs(Math.round(before * 10_000) - Math.round(now * 10_000));
    return drift > Math.round(PENALTY_EPS * 10_000)
      ? [{ key, label: de.wizard.optimize.cat[key], stamped: before, measured: now }]
      : [];
  });
}

// ------------------------------------------------------------------ filter

/** Flip one category's visibility on the image. A new set, never a mutation. */
export function toggleCategory(
  hidden: ReadonlySet<PenaltyCategoryKey>,
  key: PenaltyCategoryKey,
): ReadonlySet<PenaltyCategoryKey> {
  const next = new Set(hidden);
  if (next.has(key)) next.delete(key);
  else next.add(key);
  return next;
}

/**
 * Selecting a site of a hidden category shows the category again: a selection
 * the image does not draw would highlight nothing, and the list that offered
 * the site is the reader asking to see it. The same set when nothing changes,
 * so React skips the render.
 */
export function revealCategory(
  hidden: ReadonlySet<PenaltyCategoryKey>,
  key: PenaltyCategoryKey,
): ReadonlySet<PenaltyCategoryKey> {
  if (!hidden.has(key)) return hidden;
  const next = new Set(hidden);
  next.delete(key);
  return next;
}

// ------------------------------------------------------------------ magnitude

// Screen pixels of a mark's stroke at the smallest and the largest deduction.
// The floor keeps a tiny site visible (and tappable) at all; the ceiling keeps
// the costliest from burying the ink it points at.
export const MARK_WIDTH_MIN = 1.5;
export const MARK_WIDTH_MAX = 5.5;

/** The largest linearised cost among the located sites — the lens's own scale. */
export function maxPoints(sites: Record<PenaltyCategoryKey, PenaltyCategoryOut>): number {
  let max = 0;
  for (const key of PENALTY_CATEGORIES) {
    for (const site of sites[key].sites) if (isLocated(site)) max = Math.max(max, site.points_est);
  }
  return max;
}

/**
 * A site's size on ONE scale for the whole letter: its linearised points over
 * the costliest site's. Points, not values — a Deckungslücke of 0.03 costs
 * about twice what an Ecken of 0.03 does, and a mark's width has to say so,
 * which the category numbers themselves cannot (qualitaetsmetrik.md §5).
 */
export function magnitude(points: number, max: number): number {
  if (!(max > 0) || !(points > 0)) return 0;
  return Math.min(1, points / max);
}

/** Stroke width in screen pixels for a magnitude in [0, 1]. */
export const markWidth = (t: number): number => MARK_WIDTH_MIN + t * (MARK_WIDTH_MAX - MARK_WIDTH_MIN);

// ------------------------------------------------------------------ lists

/**
 * One category's sites as the list shows them: largest part first, and the
 * sites whose apportioned part is 0.0000 counted rather than listed — they
 * are real and drawn, but twelve rows of zeros would bury the ones that carry
 * the number.
 */
export function listedSites(category: PenaltyCategoryOut): { rows: PenaltySiteOut[]; zero: number } {
  const rows = category.sites.filter(isDrawn);
  rows.sort((a, b) => b.value - a.value || a.index - b.index);
  return { rows, zero: category.sites.length - rows.length };
}

/**
 * The boundary pixels of a set of cell runs `[x, y, width]`, in raster order —
 * a zone pixel with a 4-neighbour outside the zone. What the Doppelzug zone's
 * rim is drawn from: the missed ink inside the zone only reads against it.
 */
export function zoneRim(cells: ReadonlyArray<readonly [number, number, number]>): Array<[number, number]> {
  const inside = new Set<string>();
  for (const [x, y, w] of cells) for (let k = 0; k < w; k += 1) inside.add(`${x + k},${y}`);
  const out: Array<[number, number]> = [];
  for (const [x, y, w] of cells) {
    for (let k = 0; k < w; k += 1) {
      const px = x + k;
      const neighbours: Array<[number, number]> = [
        [px - 1, y],
        [px + 1, y],
        [px, y - 1],
        [px, y + 1],
      ];
      if (neighbours.some(([nx, ny]) => !inside.has(`${nx},${ny}`))) out.push([px, y]);
    }
  }
  return out;
}

/**
 * Where each ①–⑤ disc stands, in crop pixels (pixel-centre frame, like the
 * pins themselves): set off its point by a short leader so the mark it names
 * stays visible, and turned to the first of eight directions in which it does
 * not cover an earlier disc. The costliest sites cluster — on the `a` of the
 * frozen set, three of the five pins sit within 15 px of each other — and a
 * disc on a disc is a number nobody can read or tap.
 *
 * `offset` and `radius` are screen pixels; `scale` turns them into crop pixels.
 * When no direction is free, the first one wins: an overlap then is honest
 * about a crowded spot, and the list beside the image still separates them.
 */
export function placePins(
  pins: readonly PenaltyPinOut[],
  scale: number,
  offset: number,
  radius: number,
): Array<{ rank: number; x: number; y: number }> {
  const u = 1 / scale;
  const reach = offset * u;
  const diagonal = reach / Math.SQRT2;
  // Up-right first (the reading direction's free corner), then round the clock.
  const directions: Array<[number, number]> = [
    [diagonal, -diagonal],
    [-diagonal, -diagonal],
    [diagonal, diagonal],
    [-diagonal, diagonal],
    [reach, 0],
    [-reach, 0],
    [0, -reach],
    [0, reach],
  ];
  const clearance = (2 * radius + 2) * u;
  const placed: Array<{ rank: number; x: number; y: number }> = [];
  for (const pin of [...pins].sort((a, b) => a.rank - b.rank)) {
    const candidates = directions.map(([dx, dy]) => ({ x: pin.x + dx, y: pin.y + dy }));
    const free = candidates.find((c) => placed.every((p) => Math.hypot(p.x - c.x, p.y - c.y) >= clearance));
    placed.push({ rank: pin.rank, ...(free ?? candidates[0]) });
  }
  return placed;
}

/** The ①–⑤ rank of a site, or null when it is not among the pins. */
export function pinRank(pins: readonly PenaltyPinOut[], category: PenaltyCategoryKey, index: number): number | null {
  return pins.find((pin) => pin.category === category && pin.index === index)?.rank ?? null;
}

// ------------------------------------------------------------------ frame

/**
 * Screen pixels per crop pixel: as large as the column and the height cap
 * allow. The crops are small (≈ 80–230 px on a side) and a 44 px touch target
 * has to fit between neighbouring marks, so the lens scales UP — never below
 * the crop's own size where the room is there.
 */
export function lensScale(frame: PenaltyFrameOut, maxWidth: number, maxHeight: number): number {
  if (frame.width <= 0 || frame.height <= 0) return 1;
  return Math.max(0.25, Math.min(maxWidth / frame.width, maxHeight / frame.height));
}

// ------------------------------------------------------------------ Korb

/** The site as the Korb receives it — every number the note head writes. */
export function penaltyRefOf(
  category: PenaltyCategoryKey,
  site: PenaltySiteOut,
  owner: PenaltyCategoryOut,
): PenaltyRef {
  return {
    category,
    index: site.index,
    kind: site.kind,
    value: site.value,
    categoryValue: owner.value,
    exact: site.exact,
    pointsEst: site.points_est,
    x: site.x,
    y: site.y,
    numbers: site.numbers,
  };
}

/** What a site IS, in words: „Ecke", „fehlende Tinte", „Saum (Kantenquantisierung)". */
export function siteKindLabel(site: PenaltySiteOut): string {
  const kinds: Record<string, string> = de.admin.letters.penalties.kind;
  return kinds[site.kind] ?? site.kind;
}
