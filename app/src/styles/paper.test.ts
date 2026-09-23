// The overlay layer and role tokens, checked as what they claim to be: hues a
// reader can tell from their ground AND from each other, with every collision
// that remains named out loud rather than left to be discovered on a crop.
//
// The helpers live here rather than in a `styles/contrast.ts`, because nothing
// in production computes contrast — a module with no caller is dead code, and
// these fifteen lines are the assertion, not a utility.
//
// Three measurements, and they are deliberately NOT the same instrument:
//
//   * against a GROUND the question is visibility, so it is WCAG relative
//     luminance (1.4.11 asks 3:1 for a non-text graphical object). The floor is
//     asserted on the token AS DRAWN OPAQUE — a legend swatch, a solo face, a
//     chip, an opaque stroke;
//   * where a layer is drawn TRANSLUCENT over a scan, the floor is not met and
//     is not meant to be: the ink underneath has to stay readable through the
//     overlay, which is the whole point of the comparison. Those uses are
//     measured composited and asserted BY NAME with their numbers below, so the
//     claim is honest and any tune of an opacity or a hue moves an assertion;
//   * between two LAYERS the question is "can a deuteranope tell these apart",
//     and luminance cannot answer it. The 3:1-on-both-grounds rule already pins
//     every layer into one narrow luminance band (Y ∈ [0.14, 0.30], i.e. at
//     most 1.84:1 from end to end), so a luminance-based separation of 2:1
//     between two layers is arithmetically impossible, not merely unmet. What
//     survives deuteranopia is lightness PLUS the blue↔yellow axis, and a
//     CIE76 ΔE over the simulated pair measures exactly that.

import { describe, expect, it } from 'vitest';

import { mixHex } from '@/sections/admin/shell/pathOverlay';

import {
  layer,
  layerAlpha,
  layerDash,
  liftConnector,
  mono,
  paper,
  penalty,
  penaltyCropAlpha,
  role,
  roleDash,
  strokeStyle,
} from './paper';

type Rgb = [number, number, number];

const rgbOf = (hex: string): Rgb => {
  const h = hex.replace('#', '');
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)) as Rgb;
};

const linear = (channel: number): number => {
  const c = channel / 255;
  return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
};

const luminance = (hex: string): number => {
  const [r, g, b] = rgbOf(hex).map(linear);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};

/** WCAG 2.x contrast ratio, 1–21. */
const contrast = (a: string, b: string): number => {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
};

/**
 * `fg` at `alpha` over `bg`, the way the browser composites an SVG `fill-` or
 * `stroke-opacity`: straight over, in sRGB, NOT in linear light. What comes out
 * is the colour a screen-reading eye and a contrast checker actually see.
 */
const composite = (fg: string, alpha: number, bg: string): string => {
  const [f, b] = [rgbOf(fg), rgbOf(bg)];
  return `#${f
    .map((_, i) => Math.round(alpha * f[i] + (1 - alpha) * b[i]))
    .map((v) => v.toString(16).padStart(2, '0'))
    .join('')}`;
};

const round2 = (n: number): number => Math.round(n * 100) / 100;

/**
 * Deuteranope simulation, Viénot/Brettel/Mollon (1999): drop the M cone onto
 * the plane the remaining two span, in LMS on gamma-2.2 linear RGB. Chosen over
 * a severity-scaled model because the question here is the worst case, not a
 * degree of it.
 */
const deuteranope = (hex: string): string => {
  const [r, g, b] = rgbOf(hex).map((c) => (c / 255) ** 2.2);
  const l = 17.8824 * r + 43.5161 * g + 4.11935 * b;
  const s = 0.0299566 * r + 0.184309 * g + 1.46709 * b;
  const m = 0.494207 * l + 1.24827 * s;
  const out = [
    0.080944 * l - 0.130504 * m + 0.116721 * s,
    -0.0102485 * l + 0.0540194 * m - 0.113615 * s,
    -0.000365294 * l - 0.00412163 * m + 0.693513 * s,
  ];
  return `#${out
    .map((v) => Math.round(Math.min(1, Math.max(0, v)) ** (1 / 2.2) * 255))
    .map((v) => v.toString(16).padStart(2, '0'))
    .join('')}`;
};

const lab = (hex: string): [number, number, number] => {
  const [r, g, b] = rgbOf(hex).map(linear);
  const white = [0.95047, 1, 1.08883];
  const xyz = [
    0.4124 * r + 0.3576 * g + 0.1805 * b,
    0.2126 * r + 0.7152 * g + 0.0722 * b,
    0.0193 * r + 0.1192 * g + 0.9505 * b,
  ].map((v, i) => v / white[i]);
  const f = (t: number) => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116);
  const [fx, fy, fz] = xyz.map(f);
  return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)];
};

/** CIE76 colour difference. */
const distance = (a: string, b: string): number => {
  const [la, lb] = [lab(a), lab(b)];
  return Math.hypot(la[0] - lb[0], la[1] - lb[1], la[2] - lb[2]);
};

/** The same difference AS A DEUTERANOPE SEES IT. */
const separation = (a: string, b: string): number => distance(deuteranope(a), deuteranope(b));

// 3:1 is WCAG 1.4.11 for a non-text graphical object.
const GROUND_FLOOR = 3;
// A ΔE of 35 is far past "noticeably different" and still leaves room for a
// palette tune; the pairs that pass here sit at 41 and above, the one that does
// not sits at 11, so nothing is riding on the exact number.
const SEPARATION_FLOOR = 35;

// The one collision the period set cannot resolve: Ocker and Zinnober are the
// same colour for a deuteranope. Both hues are kept because they are the
// warning family the rest of the app already uses, and the pair is carried by
// two other channels — the engine is dashed where the Pfad is solid, and the
// legend names both. Asserted as BELOW the floor, so fixing it is a test
// failure too: the exception has to be removed, never widened. Wanting a fourth
// hue instead is understandable and does not work: a layer must clear 3:1 on
// white AND on the ink, which pins it to one narrow lightness band, and the
// only hues left in that band are a red and an orange.
// The lift connector's clearance from the ramp is a SIGHTED reader's question, not a
// colour-vision one: the failure it guards against is "the lift and the middle
// stretch of a three-part path came out the same colour", which happens on a
// full-colour screen. So it is plain CIE76 on the hexes as drawn, and it gets
// its own number rather than borrowing the floor above — under a deuteranope
// simulation the nearest ramp sample sits at ΔE 33.7, which is fine for a mark
// that also carries half width, a dotted stroke and its position under the
// strokes, but would read as a promise this test does not make.
const RAMP_CLEARANCE = 35;

const NAMED_EXCEPTIONS: ReadonlyArray<readonly [string, string]> = [['path', 'engine']];

const pairsOf = <T extends Record<string, string>>(group: T): [string, string][] => {
  const keys = Object.keys(group);
  return keys.flatMap((a, i) => keys.slice(i + 1).map((b): [string, string] => [a, b]));
};

const isException = (a: string, b: string): boolean =>
  NAMED_EXCEPTIONS.some(([x, y]) => (x === a && y === b) || (x === b && y === a));

const WHITE = '#ffffff';

// Every place a layer or a non-layer mark is drawn at less than full opacity,
// with the composited contrast MEASURED on 2026-09-19 by the helpers above.
//
// This is the review's finding of PR #620 written down rather than argued away:
// the engine silhouette sits at 0.42 and composites to 1.81:1 on white, well
// under the 3:1 the opaque token clears. It is not a bug and it is not new —
// the same opacities stood on `main` with the old `#e02030` — it is what a
// comparison overlay IS: a translucent film over the scanned ink so the ink
// stays the thing being judged. What the distinction rides on there is the
// stroke style and the legend, not the contrast ratio.
//
// `grounds` lists only the grounds a use is really drawn on: a sketch has a
// white background and never plate ink, so claiming a number over ink for it
// would be the same kind of untrue as the claim this table replaces. The
// numbers are exact to two decimals ON PURPOSE — a tripwire, not a floor.
const TRANSLUCENT_USES = [
  { use: 'engineOverlay', color: layer.engine, grounds: { white: 1.81, ink: 1.71 } },
  { use: 'engineFit', color: layer.engine, grounds: { white: 1.76, ink: 1.66 } },
  { use: 'engineWizard', color: layer.engine, grounds: { white: 1.9, ink: 1.8 } },
  { use: 'engineFace', color: layer.engine, grounds: { white: 3.43 } },
  { use: 'trace', color: layer.trace, grounds: { white: 4.23, ink: 3.44 } },
  { use: 'traceSpread', color: layer.trace, grounds: { white: 2.37 } },
  { use: 'lift', color: liftConnector.color, grounds: { white: 2.99, ink: 2.64 } },
  { use: 'current', color: layer.path, grounds: { white: 2.43 } },
] as const satisfies ReadonlyArray<{
  use: keyof typeof layerAlpha;
  color: string;
  grounds: { white: number; ink?: number };
}>;

// Which of them clear the floor once composited and which do not — named, so
// that a use crossing the line in either direction has to be looked at.
const CLEARS_COMPOSITED: readonly string[] = ['engineFace', 'trace'];

describe('overlay layer tokens', () => {
  // The two grounds an overlay is ever drawn on: a white work surface
  // (design-system §5) and the plate ink it follows. This is the OPAQUE mark —
  // the swatch in the legend, the solo face, an opaque stroke.
  it.each(Object.entries(layer))('%s clears 3:1 on white and on the ink', (_key, hex) => {
    expect(contrast(hex, WHITE)).toBeGreaterThanOrEqual(GROUND_FLOOR);
    expect(contrast(hex, paper.ink)).toBeGreaterThanOrEqual(GROUND_FLOOR);
  });

  it.each(pairsOf(layer))('%s and %s stay apart for a deuteranope', (a, b) => {
    const seen = separation(layer[a as keyof typeof layer], layer[b as keyof typeof layer]);
    if (isException(a, b)) expect(seen).toBeLessThan(SEPARATION_FLOOR);
    else expect(seen).toBeGreaterThanOrEqual(SEPARATION_FLOOR);
  });

  it('gives every layer exactly one stroke style', () => {
    expect(Object.keys(layerDash)).toEqual(Object.keys(layer));
  });

  it('keeps the exception carried by a stroke style rather than by colour', () => {
    for (const [a, b] of NAMED_EXCEPTIONS) {
      expect(layerDash[a as keyof typeof layerDash]).not.toEqual(layerDash[b as keyof typeof layerDash]);
    }
  });
});

describe('what a translucent use really composites to', () => {
  it.each(TRANSLUCENT_USES)('$use is the recorded colour over its own grounds', ({ use, color, grounds }) => {
    for (const [ground, ratio] of Object.entries(grounds)) {
      const bg = ground === 'white' ? WHITE : paper.ink;
      expect(round2(contrast(composite(color, layerAlpha[use], bg), bg))).toBe(ratio);
    }
  });

  it('measures every named opacity, so a new one cannot arrive unmeasured', () => {
    expect(TRANSLUCENT_USES.map((u) => u.use).sort()).toEqual(Object.keys(layerAlpha).sort());
  });

  it('names which uses clear the floor composited and which are the exception', () => {
    for (const { use, color, grounds } of TRANSLUCENT_USES) {
      const worst = Math.min(
        ...Object.entries(grounds).map(([ground]) => {
          const bg = ground === 'white' ? WHITE : paper.ink;
          return contrast(composite(color, layerAlpha[use], bg), bg);
        }),
      );
      if (CLEARS_COMPOSITED.includes(use)) expect(worst).toBeGreaterThanOrEqual(GROUND_FLOOR);
      else expect(worst).toBeLessThan(GROUND_FLOOR);
    }
  });
});

describe('stroke styles', () => {
  // The finding this pins: `[2, 2]` under SVG's default `butt` cap draws square
  // dashes, so a "dotted" token that carried only a dash silently became a
  // second dashed one. A dot is a zero-length dash under a ROUND cap.
  it('draws the dotted style as real dots, not as short dashes', () => {
    expect(strokeStyle.dotted.cap).toBe('round');
    expect(strokeStyle.dotted.dash[0]).toBe(0);
    expect(strokeStyle.dotted.dash[1]).toBeGreaterThan(0);
  });

  it('keeps the dashed style a dash, with its own cap', () => {
    expect(strokeStyle.dashed.cap).toBe('butt');
    expect(strokeStyle.dashed.dash.every((d) => d > 0)).toBe(true);
  });

  it('gives every taught style a cap, so no consumer has to invent one', () => {
    for (const style of [...Object.values(layerDash), ...Object.values(roleDash), liftConnector.stroke]) {
      expect(['butt', 'round']).toContain(style.cap);
    }
  });
});

describe('the lift connector (Absetzer)', () => {
  // It is drawn on the same two grounds, so the ground rule holds for the hue …
  it('clears 3:1 on white and on the ink', () => {
    expect(contrast(liftConnector.color, WHITE)).toBeGreaterThanOrEqual(GROUND_FLOOR);
    expect(contrast(liftConnector.color, paper.ink)).toBeGreaterThanOrEqual(GROUND_FLOOR);
  });

  // … but the pairwise rule does not: a lift carries no reading of its own, and
  // half width + a dotted stroke + joining two stretch ends already say what it
  // is. What it must not be is a colour the Spur→Pfad ramp passes through, or a
  // three-part path would show one stretch in the lift's own colour.
  it('is not a colour the writing-order ramp passes through', () => {
    // The ramp's own blend function, so this cannot drift from what is drawn.
    for (const t of [0.25, 0.5, 0.75]) {
      expect(distance(liftConnector.color, mixHex(layer.trace, layer.path, t))).toBeGreaterThanOrEqual(
        RAMP_CLEARANCE,
      );
    }
  });
});

describe('role tokens', () => {
  // A role is read on paper, never over ink: chips, list rows, legend dots.
  it.each(Object.entries(role))('%s clears 3:1 on both paper grounds', (_key, hex) => {
    expect(contrast(hex, paper.hi)).toBeGreaterThanOrEqual(GROUND_FLOOR);
    expect(contrast(hex, paper.bg)).toBeGreaterThanOrEqual(GROUND_FLOOR);
  });

  it.each(pairsOf(role))('%s and %s stay apart for a deuteranope', (a, b) => {
    expect(separation(role[a as keyof typeof role], role[b as keyof typeof role])).toBeGreaterThanOrEqual(
      SEPARATION_FLOOR,
    );
  });

  it('gives every role exactly one stroke style', () => {
    expect(Object.keys(roleDash)).toEqual(Object.keys(role));
  });
});

describe('the Abzugs-Linse tokens', () => {
  // The lens draws over the Tafel-Ausschnitt DIMMED to `penaltyCropAlpha`, so
  // its two grounds are white and the plate ink composited at that opacity —
  // the ground the marks really sit on, measured rather than assumed.
  const dimmedInk = composite(paper.ink, penaltyCropAlpha, WHITE);

  it('dims the plate ink to the recorded grey', () => {
    // A tripwire, like the translucent uses above: a changed opacity moves this.
    expect(dimmedInk).toBe('#b2afab');
    expect(round2(contrast(dimmedInk, WHITE))).toBe(2.18);
  });

  it.each(Object.entries(penalty))('%s clears 3:1 on white and on the dimmed ink', (_key, hex) => {
    expect(contrast(hex, WHITE)).toBeGreaterThanOrEqual(GROUND_FLOOR);
    expect(contrast(hex, dimmedInk)).toBeGreaterThanOrEqual(GROUND_FLOOR);
  });

  it('keeps the marks apart from the centreline they sit on, for a deuteranope too', () => {
    // The one pair that shares every stretch of the drawing: a mark lies ON the
    // centreline. Width and shape also separate them, but the hues must not
    // collapse either.
    expect(separation(penalty.mark, penalty.centerline)).toBeGreaterThanOrEqual(SEPARATION_FLOOR);
    expect(separation(penalty.mark, penalty.selected)).toBeGreaterThanOrEqual(SEPARATION_FLOOR);
  });

  it('names the one close pair, carried by the selection ring and width', () => {
    // Selected vs centreline sits just under the floor for a deuteranope (34.5).
    // The selection is never read by hue alone: it doubles the mark's width and
    // draws a ring round the site — so this is asserted BELOW the floor, and
    // the day a tune separates them the exception has to be removed here.
    expect(separation(penalty.selected, penalty.centerline)).toBeLessThan(SEPARATION_FLOOR);
  });

  it('marks an active state with viridian and nothing else with it', () => {
    expect(penalty.selected).toBe(paper.viridianText);
    for (const [key, hex] of Object.entries(penalty)) {
      if (key !== 'selected') {
        expect(hex).not.toBe(paper.viridian);
        expect(hex).not.toBe(paper.viridianText);
      }
    }
  });
});

describe('the accent stays the accent', () => {
  // Viridian is CTA, `success` and focus ring at once; a layer or a role
  // wearing it would make an active state and a fact look alike.
  it.each([...Object.entries(layer), ...Object.entries(role)])('%s is not viridian', (_key, hex) => {
    expect(hex).not.toBe(paper.viridian);
    expect(hex).not.toBe(paper.viridianText);
  });
});

describe('mono', () => {
  // Every face the platforms already have, plus the generic fallback. A stack
  // that reaches past this list needs a file under app/public/fonts/, an
  // @font-face rule, a preload and an OFL notice — which is exactly the cost
  // §2 says the token exists to avoid. Checking the NAMES is the only way to
  // see that from here: a font-family value never carries the `url()` that
  // ships a face, so a "no @font-face" pattern match tests nothing.
  const SYSTEM_FACES = [
    'ui-monospace',
    'sfmono-regular',
    'sf mono',
    'menlo',
    'monaco',
    'consolas',
    'dejavu sans mono',
    'liberation mono',
    'courier new',
    'monospace',
  ];

  it('is a system stack, so no new webfont is shipped', () => {
    const families = mono.split(',').map((f) => f.trim().replace(/^['"]|['"]$/g, '').toLowerCase());
    expect(families.length).toBeGreaterThan(1);
    for (const family of families) expect(SYSTEM_FACES).toContain(family);
  });

  it('ends in the generic family, so an unknown platform still gets a mono', () => {
    expect(mono.trim().endsWith('monospace')).toBe(true);
  });
});
