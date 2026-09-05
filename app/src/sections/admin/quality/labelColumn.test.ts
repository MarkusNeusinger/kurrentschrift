// The label column of the penalty breakdown is sized from the labels
// themselves. Before this it was a hard-coded 78 px — about nine characters —
// and „Deckungslücke" ran 32 px past its box straight over its own bar. Pinning
// the measurement keeps a renamed category from silently reintroducing that:
// the width has to follow the longest label, not a number somebody eyeballed.

import { describe, expect, it } from 'vitest';

import { de } from '@/locales/admin';
import { labelColumnChars } from './labelColumn';

const LONGEST = 'Deckungslücke'; // 13 characters, precomposed ü

describe('labelColumnChars', () => {
  it('measures the longest label, not the first or the last', () => {
    expect(labelColumnChars(['Ecken', LONGEST, 'Glätte'])).toBe(13);
  });

  it('counts a combining umlaut as one character', () => {
    // The monospace face advances one cell per character; counting the
    // combining mark separately would reserve a cell that is never advanced.
    const decomposed = 'Deckungslücke';
    expect(decomposed.length).toBe(14);
    expect(labelColumnChars([decomposed])).toBe(13);
  });

  it('survives an empty set rather than returning -Infinity', () => {
    expect(labelColumnChars([])).toBe(0);
  });

  it('fits every category label of the naturalness metric', () => {
    // The live check: the column is measured over exactly these strings, so a
    // new or renamed category has to stay within what the width is derived
    // from. Kurrent carries no `components`, so this set is the whole surface.
    const labels = Object.values(de.wizard.optimize.cat);
    const width = labelColumnChars(labels);
    for (const label of labels) expect(label.normalize('NFC').length).toBeLessThanOrEqual(width);
    expect(width).toBe(LONGEST.length);
  });
});
