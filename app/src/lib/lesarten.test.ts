import { describe, expect, it } from 'vitest';

import { lesarten, LOOKALIKES, MAX_LESARTEN } from './lesarten';

const differsByOne = (a: string, b: string) => {
  const x = [...a];
  const y = [...b];
  return x.length === y.length && x.filter((c, i) => c !== y[i]).length === 1;
};

describe('lesarten', () => {
  it('swaps one documented look-alike per reading, in word order, never the guess itself', () => {
    const out = lesarten('Muhme');
    expect(out[0]).toEqual({ text: 'Nuhme', index: 0, from: 'M', to: 'N' });
    expect(out.map((l) => l.text)).toContain('Mnhme'); // u → n
    expect(out.map((l) => l.text)).toContain('Mufme'); // h → f
    for (const l of out) expect(differsByOne(l.text, 'Muhme'), l.text).toBe(true);
    expect(new Set(out.map((l) => l.text)).size).toBe(out.length);
    expect(out.map((l) => l.index)).toEqual([...out.map((l) => l.index)].sort((a, b) => a - b));
  });

  it('caps the list and honours a smaller cap', () => {
    expect(lesarten('Muhme').length).toBeLessThanOrEqual(MAX_LESARTEN);
    expect(lesarten('Muhme', 3)).toHaveLength(3);
  });

  it('offers the ſ/f trap only for a non-final s (a final s is the round s)', () => {
    expect(lesarten('lesen').map((l) => l.text)).toContain('lefen');
    expect(lesarten('das').map((l) => l.text)).not.toContain('daf');
    expect(lesarten('das').map((l) => l.text)).toEqual(['däs']);
    expect(lesarten('das Haus').map((l) => l.text)).not.toContain('daf Haus');
  });

  it('returns nothing for an empty guess or letters without a look-alike', () => {
    expect(lesarten('')).toEqual([]);
    expect(lesarten('xyz')).toEqual([]);
  });

  it('keeps every look-alike table entry symmetric enough to be a real pair', () => {
    // A look-alike is a two-way confusion: if n can read as u, u can read as n.
    for (const [from, tos] of Object.entries(LOOKALIKES)) {
      for (const to of tos) expect(LOOKALIKES[to], `${from} → ${to}`).toContain(from);
    }
  });
});
