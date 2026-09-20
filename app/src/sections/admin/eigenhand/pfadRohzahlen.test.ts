// „0 % Tinte ohne Bahn" and „nicht gemessen" look the same to a `||` reader —
// and the first is the best reading a Bahn can get.
//
// `tools/eigenhand/pfad.py` projects the follower's sensors with `.get(key)`,
// so every key is present and any of them may be `null`; `meta` itself is
// stored unvalidated. Both facts are invisible on a screenshot: a chip reading
// „Absetzer 0" says nothing about whether it was counted. Pinned here instead.

import { readFileSync } from 'node:fs';

import { describe, expect, it } from 'vitest';

import type { EigenhandPfad } from '@/lib/api';
import { pfadRohzahlen } from './pfadRohzahlen';

function pfad(meta: Record<string, unknown>): EigenhandPfad {
  return {
    box_index: 0,
    word: 'lesen',
    strokes: [],
    registration_px: { tx: 0, ty: 0, baseline_row: 0 },
    xh_px: 100,
    verfahren: 'tintenpfad',
    konfiguration: {},
    meta,
    erzeugt_am: '2026-09-19',
    flecken_n: null,
  };
}

describe('pfadRohzahlen', () => {
  it('reads the four numbers off meta.tintenpfad', () => {
    const rohzahlen = pfadRohzahlen(
      pfad({
        letter_spans: null,
        tintenpfad: { runs: 4, strands: 2, jumps: 1, hairpins: 2, paper_lifts: 3, ink_unvisited_share: 0.21 },
      }),
    );
    expect(rohzahlen).toEqual({
      inkUnvisitedShare: 0.21,
      paperLifts: 3,
      jumps: 1,
      hairpins: 2,
      measured: true,
    });
  });

  it('keeps a measured zero a zero — the best reading, not a missing one', () => {
    const rohzahlen = pfadRohzahlen(
      pfad({ tintenpfad: { jumps: 0, hairpins: 0, paper_lifts: 0, ink_unvisited_share: 0.0 } }),
    );
    expect(rohzahlen).toEqual({
      inkUnvisitedShare: 0,
      paperLifts: 0,
      jumps: 0,
      hairpins: 0,
      measured: true,
    });
  });

  it('lets one null value stay null while its siblings read', () => {
    // What the writer's `.get(key)` produces: every key present, a sensor the
    // follower did not emit stored as `null`.
    const rohzahlen = pfadRohzahlen(
      pfad({ tintenpfad: { jumps: 1, hairpins: null, paper_lifts: 4, ink_unvisited_share: 0.07 } }),
    );
    expect(rohzahlen).toMatchObject({ hairpins: null, jumps: 1, paperLifts: 4, measured: true });
  });

  it('calls a path without the sensor block unmeasured rather than perfect', () => {
    // A hand-traced box (`verfahren: authored`) carries no sensors at all.
    expect(pfadRohzahlen(pfad({}))).toEqual({
      inkUnvisitedShare: null,
      paperLifts: null,
      jumps: null,
      hairpins: null,
      measured: false,
    });
    expect(pfadRohzahlen(pfad({ tintenpfad: { runs: null, jumps: null, hairpins: null, paper_lifts: null } }))).toMatchObject(
      { measured: false },
    );
  });

  it('refuses what is not a finite number instead of rendering it', () => {
    const rohzahlen = pfadRohzahlen(
      pfad({ tintenpfad: { jumps: '3', hairpins: true, paper_lifts: Number.NaN, ink_unvisited_share: Infinity } }),
    );
    expect(rohzahlen).toEqual({
      inkUnvisitedShare: null,
      paperLifts: null,
      jumps: null,
      hairpins: null,
      measured: false,
    });
  });

  it('refuses a sensor block that is not an object', () => {
    expect(pfadRohzahlen(pfad({ tintenpfad: [1, 2, 3] }))).toMatchObject({ measured: false });
    expect(pfadRohzahlen(pfad({ tintenpfad: 'keine' }))).toMatchObject({ measured: false });
  });

  it('survives a meta that is not an object either', () => {
    // The optional chain carries these; Python's `isinstance(…, Mapping)` is a
    // differently written guard for the same rule, so the shared fixture below
    // pins all four shapes on both sides.
    for (const meta of [null, undefined, 'keine', [1, 2, 3], 7]) {
      expect(pfadRohzahlen({ ...pfad({}), meta } as unknown as EigenhandPfad)).toMatchObject({ measured: false });
    }
  });

  it('refuses an integer wider than a float64, which JSON.parse hands over as Infinity', () => {
    // Valid JSON on both sides: Python builds an arbitrary-precision int and
    // has to catch the OverflowError, JavaScript gets Infinity. Both answer
    // „no reading"; the shared fixture pins the pair.
    const huge = JSON.parse('{"tintenpfad":{"paper_lifts":1e400,"jumps":0,"hairpins":0}}');
    expect(pfadRohzahlen(pfad(huge))).toMatchObject({ paperLifts: null, jumps: 0 });
  });
});

// Twin-sync guard: this reader and `core/eigenhand/tintentreue.py::rohzahlen`
// read the SAME unvalidated blob in two languages with two null rules, and the
// traffic light derived over there has to call „gemessen" what this panel calls
// `measured` — otherwise the numbers show for a box the light calls grey. Both
// sides assert the shared fixture, as shaping.ts/shaping.py do
// (tests/fixtures/shaping_cases.json); the Python half lives in
// tests/test_eigenhand_tintentreue.py.
//
// The fixture carries no NaN/Infinity by construction: `json.loads` takes them
// and `JSON.parse` does not, so those two stay in each language's own cases
// above.
interface TintentreueCase {
  name: string;
  pfad: EigenhandPfad | null;
  rohzahlen: {
    ink_unvisited_share: number | null;
    paper_lifts: number | null;
    jumps: number | null;
    hairpins: number | null;
    gemessen: boolean;
  } | null;
}

// Read via node fs rather than an import so the fixture can live at the repo
// root, shared with the Python test.
const CASES: TintentreueCase[] = JSON.parse(
  readFileSync(new URL('../../../../../tests/fixtures/tintentreue_cases.json', import.meta.url), 'utf-8'),
);

describe('pfadRohzahlen twin parity', () => {
  it('has a non-empty shared fixture', () => {
    expect(CASES.length).toBeGreaterThan(0);
  });

  it.each(CASES.filter((c): c is TintentreueCase & { pfad: EigenhandPfad } => c.pfad !== null))(
    'reads $name like core/eigenhand/tintentreue.py',
    ({ pfad: entry, rohzahlen }) => {
      expect(pfadRohzahlen(entry)).toEqual({
        inkUnvisitedShare: rohzahlen?.ink_unvisited_share ?? null,
        paperLifts: rohzahlen?.paper_lifts ?? null,
        jumps: rohzahlen?.jumps ?? null,
        hairpins: rohzahlen?.hairpins ?? null,
        measured: rohzahlen?.gemessen ?? false,
      });
    },
  );
});
