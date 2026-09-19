// The one rule worth pinning about the hand's pen figure: a missing reading is
// missing, never zero. `core/eigenhand/befund.py` writes `nib.units = 0.0` for
// a Fassung it could not measure, so a naive median over the column would
// report a hairline hand the moment one strip failed to read — a wrong number
// that looks exactly like a right one on screen.

import { describe, expect, it } from 'vitest';

import type { EigenhandStrip } from '@/lib/api';
import { nibMedian } from './nibMedian';

function row(units: number | string | null | undefined): EigenhandStrip {
  const strip: EigenhandStrip = {
    strip: 'S0001',
    fassung: 'F01',
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
    befund:
      units === undefined
        ? null
        : {
            vorschlag: 'sauber',
            grund: 'egal',
            guete: 50,
            nib: { units },
            unstetigkeit: {},
            kringel: {},
            duktus: {},
            deckung: {},
            lesbarkeit: {},
            rang: null,
            von: null,
            abgeloest_von: null,
          },
  };
  return strip;
}

describe('nibMedian', () => {
  it('takes the middle reading of an odd count', () => {
    expect(nibMedian([row(0.03), row(0.05), row(0.04)])).toEqual({ units: 0.04, count: 3 });
  });

  it('averages the two middle readings of an even count', () => {
    expect(nibMedian([row(0.02), row(0.04)])).toEqual({ units: 0.03, count: 2 });
  });

  it('drops an unmeasured Fassung instead of counting it as a hairline', () => {
    // 0 is befund.py's „could not measure", null/absent its „nobody looked".
    expect(nibMedian([row(0.04), row(0), row(null), row(undefined)])).toEqual({ units: 0.04, count: 1 });
  });

  it('reports no figure at all rather than a zero when nothing was measured', () => {
    expect(nibMedian([row(0), row(undefined)])).toEqual({ units: null, count: 0 });
    expect(nibMedian([])).toEqual({ units: null, count: 0 });
  });

  it('ignores a non-numeric reading from the loose record', () => {
    expect(nibMedian([row('0.04'), row(0.06)])).toEqual({ units: 0.06, count: 1 });
  });
});
