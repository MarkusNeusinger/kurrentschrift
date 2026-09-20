// The score colours are a CONTRAST decision, and the source guard next door
// cannot see it: `paletteProp.guard.test.ts` only rejects a dotted path on a
// `color` prop, so a tier quietly returning to ochre — or a positive delta
// going back to raw `success.main` — would keep that guard green while the
// number on screen drops below AA again.
//
// So this file pins the two things that must not drift: WHICH token each tier
// and each delta sign resolves to, and that the resolved tone actually clears
// 4,5:1 as TEXT on the two grounds these numbers sit on (the white work
// surface and the card ground `paper.hi`). The contrast helper is local for
// the same reason `paper.test.ts` gives for its own copy: nothing in
// production computes contrast, so a shared module would have no caller.
//
// The bar beside the number is deliberately NOT pinned here — it is a
// graphical mark under WCAG 1.4.11 and needs 3:1, which is the whole point of
// the split documented in `scoreColors.ts`.

import { describe, expect, it } from 'vitest';

import { ink, imprint } from '@/theme/palette';
import { paper, pigment } from '@/styles/paper';
import { PENALTY_TEXT_COLOR, type PenaltyTier, scoreDeltaColor } from './scoreColors';

const WHITE = '#ffffff';

/** WCAG 2.x contrast ratio, 1–21. */
function contrast(a: string, b: string): number {
  const luminance = (hex: string): number => {
    const channels = [1, 3, 5].map((i) => {
      const c = parseInt(hex.slice(i, i + 2), 16) / 255;
      return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
  };
  const [x, y] = [luminance(a), luminance(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
}

/**
 * What each `sx` token resolves to at render time — read from the palette
 * itself, so a retuned ink is measured rather than a hex copied in here.
 */
const RESOLVED: Record<string, string> = {
  'text.primary': ink.primary,
  'text.secondary': ink.soft,
  'text.disabled': ink.muted,
  'error.main': pigment.oxblood,
  'warning.main': pigment.ochre,
  'success.main': imprint.viridian,
};

const resolve = (token: string): string => RESOLVED[token] ?? token;

const AA_TEXT = 4.5;

describe('PENALTY_TEXT_COLOR', () => {
  it('keeps the warning tier in ink — ochre is a mark colour', () => {
    expect(PENALTY_TEXT_COLOR.warning).toBe('text.primary');
    // The tone it must never return to, and the number that rules it out.
    const ochre = resolve('warning.main');
    expect(contrast(ochre, WHITE)).toBeLessThan(AA_TEXT);
    expect(contrast(ochre, paper.hi)).toBeLessThan(AA_TEXT);
  });

  it('rises soft ink → ink → oxblood, so the ladder reads without colour', () => {
    expect(PENALTY_TEXT_COLOR.primary).toBe('text.secondary');
    expect(PENALTY_TEXT_COLOR.error).toBe('error.main');
  });

  it('clears AA for text on both grounds, in every tier', () => {
    const tiers: PenaltyTier[] = ['primary', 'warning', 'error'];
    for (const tier of tiers) {
      const hex = resolve(PENALTY_TEXT_COLOR[tier]);
      expect(contrast(hex, WHITE), `${tier} on white`).toBeGreaterThanOrEqual(AA_TEXT);
      expect(contrast(hex, paper.hi), `${tier} on the card ground`).toBeGreaterThanOrEqual(AA_TEXT);
    }
  });
});

describe('scoreDeltaColor', () => {
  it('takes the viridian TEXT shade for an improvement, never raw viridian', () => {
    expect(scoreDeltaColor(3.4)).toBe(paper.viridianText);
    expect(scoreDeltaColor(0)).toBe(paper.viridianText);
    // Raw viridian — what `success.main` resolves to — is exactly what this
    // avoids: fine on white, short on the card ground these deltas sit on.
    expect(contrast(resolve('success.main'), paper.hi)).toBeLessThan(AA_TEXT);
  });

  it('takes oxblood for a regression', () => {
    expect(scoreDeltaColor(-0.1)).toBe('error.main');
  });

  it('clears AA for text on both grounds, in both directions', () => {
    for (const delta of [1, -1]) {
      const hex = resolve(scoreDeltaColor(delta));
      expect(contrast(hex, WHITE), `${delta} on white`).toBeGreaterThanOrEqual(AA_TEXT);
      expect(contrast(hex, paper.hi), `${delta} on the card ground`).toBeGreaterThanOrEqual(AA_TEXT);
    }
  });
});
