// The Abzugs-Linse's decisions, pinned: which mark a site gets (the shape is
// the channel that tells categories apart, so two categories sharing one would
// be a colour-vision bug), what a legend chip says (never „0" for a term that
// did not apply), when the stamp is reported as drifted, and how the ①–⑤
// discs keep off each other. The payloads are synthetic — the real ones are
// the reserved dataset and never enter the repo.

import { describe, expect, it } from 'vitest';

import type { PenaltyCategoryKey, PenaltyCategoryOut, PenaltyPinOut, PenaltySiteOut } from '@/lib/api';

import {
  CATEGORY_SHAPE,
  categoryChips,
  coveragePart,
  edgeTicks,
  isDrawn,
  isPixelShape,
  lensScale,
  listedSites,
  magnitude,
  MARK_WIDTH_MAX,
  MARK_WIDTH_MIN,
  markWidth,
  maxPoints,
  PENALTY_CATEGORIES,
  penaltyRefOf,
  pinRank,
  placePins,
  revealCategory,
  shownPins,
  siteShape,
  spanBars,
  stampDrift,
  toggleCategory,
  VERTICAL_EXAGGERATION,
  VERTICAL_SWING_UNITS,
  verticalExaggeration,
  zoneOutline,
} from './penaltyLens';

const site = (over: Partial<PenaltySiteOut> = {}): PenaltySiteOut => ({
  index: 0,
  kind: 'corner',
  value: 0.01,
  share: 0.5,
  exact: true,
  points_est: 1,
  x: 10,
  y: 12,
  numbers: {},
  paths: [],
  cells: [],
  ...over,
});

const category = (over: Partial<PenaltyCategoryOut> = {}): PenaltyCategoryOut => ({
  value: 0,
  applicable: true,
  in_sync: true,
  exact: false,
  points_est: 0,
  sites: [],
  numbers: {},
  parts: {},
  context_paths: [],
  context_cells: [],
  ...over,
});

/** All six categories, not applicable and empty unless overridden. */
const allSites = (
  over: Partial<Record<PenaltyCategoryKey, PenaltyCategoryOut>> = {},
): Record<PenaltyCategoryKey, PenaltyCategoryOut> => {
  const out = {} as Record<PenaltyCategoryKey, PenaltyCategoryOut>;
  for (const key of PENALTY_CATEGORIES) out[key] = over[key] ?? category({ applicable: false });
  return out;
};

describe('marker shapes — the channel that is not colour', () => {
  it('gives every category a shape of its own', () => {
    const shapes = PENALTY_CATEGORIES.map((key) => CATEGORY_SHAPE[key]);
    expect(new Set(shapes).size).toBe(PENALTY_CATEGORIES.length);
  });

  it('maps a located site to its category shape', () => {
    expect(siteShape('corner', site())).toBe('square');
    expect(siteShape('collinearity', site({ kind: 'passage' }))).toBe('ring');
    expect(siteShape('verticality', site({ kind: 'run' }))).toBe('bracket');
    expect(siteShape('smoothness', site({ kind: 'segment' }))).toBe('band');
    expect(siteShape('retrace', site({ kind: 'missed_ink' }))).toBe('crosshatch');
  });

  it('splits Deckungslücke into marks no other category uses', () => {
    const kinds = ['missed_ink', 'excess_render', 'edge', 'off_skeleton'];
    const shapes = kinds.map((kind) => siteShape('coverage', site({ kind })));
    expect(shapes).toEqual(['hatch', 'stipple', 'edgeTicks', 'whiskers']);
    expect(new Set(shapes).size).toBe(4);
    // Doppelzug's missed ink is crosshatched, Deckungslücke's hatched: the same
    // pixels can carry both, and they must not read as one mark.
    expect(siteShape('retrace', site({ kind: 'missed_ink' }))).not.toBe(siteShape('coverage', site({ kind: 'missed_ink' })));
  });

  it('paints nothing for a site without a place', () => {
    expect(siteShape('coverage', site({ kind: 'rim', x: null, y: null }))).toBe('none');
    expect(siteShape('smoothness', site({ kind: 'unlocated', x: null, y: null }))).toBe('none');
  });

  it('names which coverage factor a site belongs to', () => {
    expect(coveragePart('coverage', site({ kind: 'rim' }))).toBe('dice');
    expect(coveragePart('coverage', site({ kind: 'edge' }))).toBe('chamfer');
    expect(coveragePart('coverage', site({ kind: 'off_skeleton' }))).toBe('geo');
    expect(coveragePart('corner', site())).toBeNull();
  });

  it('draws only the pixel marks in the crop grid', () => {
    expect(['hatch', 'stipple', 'crosshatch', 'edgeTicks'].every((s) => isPixelShape(s as never))).toBe(true);
    expect(['band', 'bracket', 'square', 'ring', 'whiskers'].some((s) => isPixelShape(s as never))).toBe(false);
  });
});

describe('legend chips — the „Abzüge (neu gemessen)" line', () => {
  const sites = allSites({
    corner: category({
      value: 0.1711,
      exact: true,
      sites: [site({ index: 0, value: 0.0954 }), site({ index: 1, value: 0.0757 })],
    }),
    coverage: category({
      value: 0.1981,
      sites: [
        site({ index: 0, kind: 'edge', value: 0.1323 }),
        site({ index: 1, kind: 'edge', value: 0 }),
        site({ index: 2, kind: 'rim', value: 0.0658, x: null, y: null }),
      ],
    }),
    smoothness: category({ value: 0, sites: [] }),
  });
  const chips = categoryChips(sites);

  it('orders worst first, then what does not apply in the metric order', () => {
    expect(chips.map((c) => c.key)).toEqual([
      'coverage',
      'corner',
      'smoothness',
      'verticality',
      'collinearity',
      'retrace',
    ]);
  });

  it('carries the number to four places and the drawn site count', () => {
    expect(chips[1].text).toBe('Ecken 0.1711 · 2 Stellen');
  });

  it('says what has no place, and counts only what is drawn', () => {
    // One edge site carries 0.0000 — it adds nothing to the four places shown.
    expect(chips[0].text).toBe('Deckungslücke 0.1981 · 1 Stelle · 0.0658 ohne Ort');
    expect(chips[0].unlocatedValue).toBe(0.0658);
  });

  it('reads „nicht anwendbar" instead of 0 for a term that never applied', () => {
    const cross = chips.find((c) => c.key === 'collinearity');
    expect(cross?.text).toBe('Kreuzungsflucht · nicht anwendbar');
    expect(cross?.text).not.toContain('0.0000');
    expect(cross?.filterable).toBe(false);
  });

  it('keeps an applicable zero honest: measured, no site, no switch', () => {
    const smooth = chips.find((c) => c.key === 'smoothness');
    expect(smooth?.text).toBe('Glätte 0.0000 · keine Stelle');
    expect(smooth?.filterable).toBe(false);
  });

  it('names the collinearity deduction „Kreuzungsflucht", never the landmark word', () => {
    expect(chips.some((c) => c.label === 'Kreuzung')).toBe(false);
  });

  it('tells a dropped map apart from an ordinary part without a place', () => {
    // The core's drift group: the whole number as ONE unlocated site.
    const drifted = categoryChips(
      allSites({
        smoothness: category({
          value: 0.0123,
          in_sync: false,
          sites: [site({ kind: 'unlocated', value: 0.0123, x: null, y: null, numbers: { reason: 'recomputation_drift' } })],
        }),
      }),
    ).find((c) => c.key === 'smoothness');
    expect(drifted?.inSync).toBe(false);
    expect(drifted?.text).toBe('Glätte 0.0123 · Karte verworfen (Nachrechnung weicht ab)');
    expect(drifted?.text).not.toContain('ohne Ort');
    expect(drifted?.filterable).toBe(false);
  });
});

describe('the „gespeichert" line', () => {
  it('reports only a category that moved by more than 0.005', () => {
    const drift = stampDrift(
      { coverage: 0.1767, corner: 0.171, smoothness: 0.1168 },
      { coverage: 0.1981, corner: 0.1711, smoothness: 0.1158, naturalness: 0.1 },
    );
    expect(drift).toEqual([{ key: 'coverage', label: 'Deckungslücke', stamped: 0.1767, measured: 0.1981 }]);
  });

  it('does not report a step of exactly 0.005, which floating point would', () => {
    // 0.1767 − 0.1717 is 0.005000000000000004 in doubles.
    expect(stampDrift({ coverage: 0.1767 }, { coverage: 0.1717 })).toEqual([]);
  });

  it('takes an absent stamp for what it is, not for a drift', () => {
    expect(stampDrift(null, { coverage: 0.2 })).toEqual([]);
    expect(stampDrift({ coverage: 0.2 }, { coverage: 0.2, retrace: 0.3 })).toEqual([]);
  });
});

describe('filter state', () => {
  it('flips one category without mutating the old set', () => {
    const before: ReadonlySet<PenaltyCategoryKey> = new Set(['corner']);
    const after = toggleCategory(before, 'corner');
    expect(after.has('corner')).toBe(false);
    expect(before.has('corner')).toBe(true);
    expect(toggleCategory(after, 'retrace').has('retrace')).toBe(true);
  });

  it('shows a hidden category again when one of its sites is selected', () => {
    const hidden: ReadonlySet<PenaltyCategoryKey> = new Set(['corner', 'retrace']);
    const next = revealCategory(hidden, 'corner');
    expect([...next]).toEqual(['retrace']);
    // Nothing to change: the same set, so React skips the render.
    expect(revealCategory(next, 'coverage')).toBe(next);
  });
});

describe('magnitude', () => {
  it('puts every site on the letter’s one scale, the costliest at full width', () => {
    const sites = allSites({
      corner: category({ sites: [site({ points_est: 2 }), site({ index: 1, points_est: 0.5 })] }),
      coverage: category({ sites: [site({ kind: 'rim', points_est: 9, x: null, y: null })] }),
    });
    // The unlocated rim is not drawn, so it does not set the scale.
    expect(maxPoints(sites)).toBe(2);
    expect(magnitude(2, 2)).toBe(1);
    expect(magnitude(0.5, 2)).toBe(0.25);
    expect(magnitude(1, 0)).toBe(0);
    expect(markWidth(0)).toBe(MARK_WIDTH_MIN);
    expect(markWidth(1)).toBe(MARK_WIDTH_MAX);
  });
});

describe('the Senkrechte exaggeration', () => {
  it('blows a sub-pixel wander up twenty times', () => {
    // 0.1 px on a 64 px x-height: ×20 swings 2 px, well inside 0.15 · 64.
    expect(verticalExaggeration([0.05, -0.1, 0.02], 64)).toBe(VERTICAL_EXAGGERATION);
  });

  it('blows a wide wander up less, so the drawn run stays by its own ink', () => {
    // 1.5 px on 64 px: ×20 would swing 30 px, a half x-height across the bowl.
    const factor = verticalExaggeration([1.5, -0.4], 64);
    expect(factor).toBe(6); // floor(0.15 · 64 / 1.5)
    expect(factor * 1.5).toBeLessThanOrEqual(VERTICAL_SWING_UNITS * 64);
  });

  it('never draws below the truth or divides by nothing', () => {
    expect(verticalExaggeration([40], 64)).toBe(1);
    expect(verticalExaggeration([], 64)).toBe(VERTICAL_EXAGGERATION);
    expect(verticalExaggeration([0, 0], 64)).toBe(VERTICAL_EXAGGERATION);
  });
});

describe('site lists', () => {
  it('lists the largest part first and counts the zeros instead of listing them', () => {
    const { rows, zero } = listedSites(
      category({
        sites: [
          site({ index: 0, value: 0.0021 }),
          site({ index: 1, value: 0 }),
          site({ index: 2, value: 0.0954 }),
          site({ index: 3, kind: 'rim', value: 0.0658, x: null, y: null }),
        ],
      }),
    );
    expect(rows.map((s) => s.index)).toEqual([2, 3, 0]);
    expect(zero).toBe(1);
    expect(isDrawn(site({ value: 0 }))).toBe(false);
  });

  it('knows which sites are pins', () => {
    const pins: PenaltyPinOut[] = [{ rank: 1, category: 'corner', index: 1, points_est: 2.28, x: 72.6, y: 24.86 }];
    expect(pinRank(pins, 'corner', 1)).toBe(1);
    expect(pinRank(pins, 'corner', 0)).toBeNull();
  });

  it('never pins a site the image does not draw, and ranks the rest again from 1', () => {
    // The core pins by the unrounded part; a category whose number rounds to
    // 0.0000 apportions 0.0000 to each of its sites, which the image leaves out.
    const sites = allSites({
      retrace: category({ value: 0, sites: [site({ index: 0, kind: 'missed_ink', value: 0, points_est: 0.02 })] }),
      corner: category({ value: 0.0003, sites: [site({ index: 0, value: 0.0003, points_est: 0.01 })] }),
    });
    const pins: PenaltyPinOut[] = [
      { rank: 1, category: 'retrace', index: 0, points_est: 0.02, x: 10, y: 12 },
      { rank: 2, category: 'corner', index: 0, points_est: 0.01, x: 10, y: 12 },
    ];
    expect(shownPins(pins, sites)).toEqual([{ ...pins[1], rank: 1 }]);
    // Nothing to drop: the payload's own pins, untouched.
    expect(shownPins([pins[1]].map((p) => ({ ...p, rank: 1 })), sites)[0]).toEqual({ ...pins[1], rank: 1 });
  });
});

describe('the ①–⑤ discs', () => {
  it('turns a disc away from one it would cover', () => {
    // Three pins within a few pixels of each other, as on the frozen `a`.
    const pins: PenaltyPinOut[] = [
      { rank: 1, category: 'corner', index: 1, points_est: 2.3, x: 72.6, y: 24.9 },
      { rank: 2, category: 'smoothness', index: 1, points_est: 2.3, x: 74, y: 26 },
      { rank: 3, category: 'coverage', index: 7, points_est: 1.4, x: 73, y: 30 },
    ];
    const scale = 3;
    const placed = placePins(pins, scale, 20, 11);
    const clearance = (2 * 11 + 2) / scale;
    for (let i = 0; i < placed.length; i += 1) {
      for (let j = i + 1; j < placed.length; j += 1) {
        expect(Math.hypot(placed[i].x - placed[j].x, placed[i].y - placed[j].y)).toBeGreaterThanOrEqual(clearance);
      }
    }
    // The first pin keeps the preferred corner: up and to the right.
    expect(placed[0].x).toBeGreaterThan(72.6);
    expect(placed[0].y).toBeLessThan(24.9);
  });

  it('sets every disc the same distance off its point', () => {
    const pins: PenaltyPinOut[] = [{ rank: 1, category: 'corner', index: 0, points_est: 1, x: 10, y: 10 }];
    const [disc] = placePins(pins, 2, 20, 11);
    expect(Math.hypot(disc.x - 10, disc.y - 10)).toBeCloseTo(10);
  });
});

describe('frame', () => {
  it('scales the crop up to the column or the height cap, whichever binds', () => {
    expect(lensScale({ width: 154, height: 98, unit_px: 64 }, 560, 540)).toBeCloseTo(560 / 154);
    expect(lensScale({ width: 87, height: 205, unit_px: 62 }, 560, 540)).toBeCloseTo(540 / 205);
  });

});

describe('context and edge forms', () => {
  it('outlines a zone as one closed loop on the pixel edges', () => {
    // A 3×3 block: one loop, its four corners — no dot per boundary pixel.
    const loops = zoneOutline([
      [2, 1, 3],
      [2, 2, 3],
      [2, 3, 3],
    ]);
    expect(loops).toHaveLength(1);
    expect([...loops[0]].sort()).toEqual(
      [
        [2, 1],
        [5, 1],
        [5, 4],
        [2, 4],
      ].sort(),
    );
  });

  it('gives a ring its inner outline too, and keeps diagonal neighbours apart', () => {
    const ring = zoneOutline([
      [0, 0, 3],
      [0, 1, 1],
      [2, 1, 1],
      [0, 2, 3],
    ]);
    expect(ring).toHaveLength(2);
    expect(ring.map((loop) => loop.length).sort()).toEqual([4, 4]);
    // Two pixels touching only at a corner are two regions, not a figure eight.
    expect(
      zoneOutline([
        [0, 0, 1],
        [1, 1, 1],
      ]),
    ).toHaveLength(2);
    expect(zoneOutline([])).toEqual([]);
  });

  it('ticks a Chamfer edge across it, spaced, on the pixel centres', () => {
    // A horizontal edge: the ticks stand upright, at least the gap apart.
    const flat = edgeTicks([[10, 5, 12]], 3);
    expect(flat.length).toBe(4);
    for (const tick of flat) {
      expect(tick.y).toBe(5.5);
      expect(Math.abs(tick.ny)).toBeCloseTo(1);
      expect(tick.nx).toBeCloseTo(0);
    }
    for (let i = 1; i < flat.length; i += 1) expect(flat[i].x - flat[i - 1].x).toBeGreaterThanOrEqual(3);
    // A vertical edge: the ticks lie flat.
    const column = edgeTicks(
      Array.from({ length: 8 }, (_, i) => [4, i, 1] as [number, number, number]),
      2,
    );
    for (const tick of column) expect(Math.abs(tick.nx)).toBeCloseTo(1);
    // A lone pixel has no direction: an upright tick, never NaN.
    expect(edgeTicks([[0, 0, 1]], 3)).toEqual([{ x: 0.5, y: 0.5, nx: 0, ny: 1 }]);
  });

  it('bars a corner window square to its ends', () => {
    const bars = spanBars(
      [
        [0, 0],
        [4, 0],
        [4, 4],
      ],
      2,
    );
    expect(bars).toEqual([
      [
        [0, 2],
        [0, -2],
      ],
      [
        [6, 4],
        [2, 4],
      ],
    ]);
    expect(spanBars([[1, 1]], 2)).toEqual([]);
  });
});

describe('the Korb reference', () => {
  it('carries every number the note head writes', () => {
    const owner = category({ value: 0.1711 });
    const ref = penaltyRefOf('corner', site({ index: 1, value: 0.0954, points_est: 2.28, numbers: { anchor: 71 } }), owner);
    expect(ref).toEqual({
      category: 'corner',
      index: 1,
      kind: 'corner',
      value: 0.0954,
      categoryValue: 0.1711,
      exact: true,
      pointsEst: 2.28,
      x: 10,
      y: 12,
      numbers: { anchor: 71 },
    });
  });
});
