// The focus ring is the one operability token that cannot be seen in a unit
// test — it is a CSS outline on a state nothing here enters. What CAN be pinned
// is that there is exactly ONE of it: that the value is the §9.1 ring, and that
// the theme's three rules carry that very object rather than a copy which could
// drift to a different colour or offset.

import { describe, expect, it } from 'vitest';

import { components } from '@/theme/components';
import { FOCUS_RING_OFFSET, FOCUS_RING_WIDTH, focusRing, focusRingSx } from './focusRing';
import { paper } from './paper';

describe('focusRing', () => {
  it('is the 2px viridian ring design-system.md §9.1 prescribes', () => {
    expect(focusRing.outline).toBe(`2px solid ${paper.viridian}`);
    expect(focusRing.outlineOffset).toBe(2);
    expect(FOCUS_RING_WIDTH).toBe(2);
    expect(FOCUS_RING_OFFSET).toBe(2);
  });

  it('is the SAME object the theme applies, so the two cannot drift apart', () => {
    // Identity, not equality: a second literal with the same numbers today is
    // exactly the drift this export exists to prevent.
    const base = components.MuiButtonBase?.styleOverrides?.root as Record<string, unknown>;
    const chip = components.MuiChip?.styleOverrides?.root as Record<string, unknown>;
    const link = (components.MuiLink?.styleOverrides?.root as Record<string, unknown>)?.[
      '&:focus-visible'
    ];
    expect(base['&.Mui-focusVisible']).toBe(focusRing);
    expect(chip['&.Mui-focusVisible']).toBe(focusRing);
    expect(link).toBe(focusRing);
  });

  it('offers the hand-rolled form under the state selector a plain element uses', () => {
    // A bare `<button>` (the Eigenhand coverage cells) never matches MUI's
    // `.Mui-focusVisible` class — it needs `:focus-visible` itself.
    expect(focusRingSx['&:focus-visible']).toBe(focusRing);
  });
});
