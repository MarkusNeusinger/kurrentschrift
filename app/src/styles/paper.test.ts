// The overlay layer and role tokens, checked as what they claim to be: hues a
// reader can tell from their ground AND from each other, with every collision
// that remains named out loud rather than left to be discovered on a crop.
//
// The helpers live here rather than in a `styles/contrast.ts`, because nothing
// in production computes contrast — a module with no caller is dead code, and
// these fifteen lines are the assertion, not a utility.
//
// Two measurements, and they are deliberately NOT the same instrument:
//
//   * against a GROUND the question is visibility, so it is WCAG relative
//     luminance (1.4.11 asks 3:1 for a non-text graphical object);
//   * between two LAYERS the question is "can a deuteranope tell these apart",
//     and luminance cannot answer it. The 3:1-on-both-grounds rule already pins
//     every layer into one narrow luminance band (Y ∈ [0.14, 0.30], i.e. at
//     most 1.84:1 from end to end), so a luminance-based separation of 2:1
//     between two layers is arithmetically impossible, not merely unmet. What
//     survives deuteranopia is lightness PLUS the blue↔yellow axis, and a
//     CIE76 ΔE over the simulated pair measures exactly that.

import { describe, expect, it } from 'vitest';

import { mixHex } from '@/sections/admin/shell/pathOverlay';

import { absetzer, layer, layerDash, mono, paper, role, roleDash } from './paper';

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
const NAMED_EXCEPTIONS: ReadonlyArray<readonly [string, string]> = [['path', 'engine']];

const pairsOf = <T extends Record<string, string>>(group: T): [string, string][] => {
  const keys = Object.keys(group);
  return keys.flatMap((a, i) => keys.slice(i + 1).map((b): [string, string] => [a, b]));
};

const isException = (a: string, b: string): boolean =>
  NAMED_EXCEPTIONS.some(([x, y]) => (x === a && y === b) || (x === b && y === a));

describe('overlay layer tokens', () => {
  // The two grounds an overlay is ever drawn on: a white work surface
  // (design-system §5) and the plate ink it follows.
  it.each(Object.entries(layer))('%s clears 3:1 on white and on the ink', (_key, hex) => {
    expect(contrast(hex, '#ffffff')).toBeGreaterThanOrEqual(GROUND_FLOOR);
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

describe('the Absetzer mark', () => {
  // It is drawn on the same two grounds, so the ground rule holds …
  it('clears 3:1 on white and on the ink', () => {
    expect(contrast(absetzer.color, '#ffffff')).toBeGreaterThanOrEqual(GROUND_FLOOR);
    expect(contrast(absetzer.color, paper.ink)).toBeGreaterThanOrEqual(GROUND_FLOOR);
  });

  // … but the pairwise rule does not: a lift carries no reading of its own, and
  // half width + a dotted stroke + joining two stretch ends already say what it
  // is. What it must not be is a colour the Spur→Pfad ramp passes through, or a
  // three-part path would show one stretch in the lift's own colour.
  it('is not a colour the writing-order ramp passes through', () => {
    // The ramp's own blend function, so this cannot drift from what is drawn.
    for (const t of [0.25, 0.5, 0.75]) {
      expect(distance(absetzer.color, mixHex(layer.trace, layer.path, t))).toBeGreaterThanOrEqual(SEPARATION_FLOOR);
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

describe('the accent stays the accent', () => {
  // Viridian is CTA, `success` and focus ring at once; a layer or a role
  // wearing it would make an active state and a fact look alike.
  it.each([...Object.entries(layer), ...Object.entries(role)])('%s is not viridian', (_key, hex) => {
    expect(hex).not.toBe(paper.viridian);
    expect(hex).not.toBe(paper.viridianText);
  });
});

describe('mono', () => {
  it('is a system stack, so no new webfont is shipped', () => {
    expect(mono).toContain('monospace');
    expect(mono).not.toMatch(/url\(|@font-face/);
  });
});
