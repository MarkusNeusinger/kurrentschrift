// „Welche Fassung schreibe ich neu?" — the order that answers it.
//
// A comparator sorting the wrong way is invisible in a screenshot: three rows
// in the wrong order still look like three rows. So the property is pinned
// here rather than inspected by eye — including the case a screenshot cannot
// show at all, a Fassung with no Befund, which must sink rather than lead a
// rewrite list.

import { describe, expect, it } from 'vitest';

import type { EigenhandBefund, EigenhandStrip, EigenhandVorschlag } from '@/lib/api';
import { VORSCHLAG_COLOR, VORSCHLAG_SEVERITY, byBefund } from './befundOrder';

function row(fassung: string, vorschlag: EigenhandVorschlag | null, guete = 50): EigenhandStrip {
  const befund: EigenhandBefund | null =
    vorschlag === null
      ? null
      : {
          vorschlag,
          grund: 'egal',
          guete,
          nib: {},
          unstetigkeit: {},
          kringel: {},
          duktus: {},
          deckung: {},
          lesbarkeit: {},
          rang: null,
          von: null,
          abgeloest_von: null,
        };
  return {
    strip: 'S0001',
    fassung,
    sheet: 'B0001',
    row_index: 0,
    width_px: 10,
    height_px: 10,
    dpi: 300,
    crop_origin_mm: [0, 0],
    sha256: 'x',
    bytes: 1,
    words: [],
    boxes: [],
    befund,
  };
}

const order = (rows: EigenhandStrip[]) => [...rows].sort(byBefund).map((r) => r.fassung);

describe('byBefund — weakest first', () => {
  it('puts the severest suggestion at the top', () => {
    expect(order([row('F01', 'sauber', 90), row('F02', 'brauchbar', 70), row('F03', 'neu schreiben', 30)])).toEqual([
      'F03',
      'F02',
      'F01',
    ]);
  });

  it('breaks a tie on the suggestion by the lower composite', () => {
    expect(order([row('F01', 'brauchbar', 80), row('F02', 'brauchbar', 40)])).toEqual(['F02', 'F01']);
  });

  it('sinks a Fassung with no Befund — a missing reading is not a bad one', () => {
    expect(order([row('F01', null), row('F02', 'sauber', 99)])).toEqual(['F02', 'F01']);
  });

  it('is stable on rows that are equal in every graded way', () => {
    expect(order([row('F02', 'sauber', 90), row('F01', 'sauber', 90)])).toEqual(['F01', 'F02']);
  });
});

describe('the chip colour and the sort read the same ladder', () => {
  it('has one entry per suggestion in both tables', () => {
    expect(Object.keys(VORSCHLAG_COLOR).sort()).toEqual(Object.keys(VORSCHLAG_SEVERITY).sort());
  });

  it('colours the severest red and the clean one green', () => {
    const worst = (Object.keys(VORSCHLAG_SEVERITY) as EigenhandVorschlag[]).reduce((a, b) =>
      VORSCHLAG_SEVERITY[a] > VORSCHLAG_SEVERITY[b] ? a : b,
    );
    expect(VORSCHLAG_COLOR[worst]).toBe('error');
    expect(VORSCHLAG_COLOR.sauber).toBe('success');
  });
});
