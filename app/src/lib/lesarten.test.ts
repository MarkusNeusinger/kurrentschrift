import { describe, expect, it } from 'vitest';

import { LOOKALIKES } from './lesarten';

describe('LOOKALIKES', () => {
  it('is symmetric — a look-alike is a two-way confusion', () => {
    for (const [from, tos] of Object.entries(LOOKALIKES)) {
      for (const to of tos) expect(LOOKALIKES[to], `${from} → ${to}`).toContain(from);
    }
  });

  it('keys single typed letters only (the long ſ is typed as s)', () => {
    for (const from of Object.keys(LOOKALIKES)) expect([...from]).toHaveLength(1);
    expect(LOOKALIKES.s).toContain('f');
    expect(LOOKALIKES).not.toHaveProperty('ſ');
  });
});
