// „Wo kommt dieser Pfad her?" — and the case the caption used to get wrong.
//
// A Fassung's paths can come out of several runs: `tools.eigenhand.pfad` merges
// what it followed over what was stored, so one re-followed word can sit beside
// words from an older day. The caption read Verfahren and day off `pfade[0]`
// and put them under all of them (Copilot review, PR #598). Two paths from two
// runs still look like two paths on a screenshot, so the property is pinned
// here rather than inspected by eye.

import { describe, expect, it } from 'vitest';

import type { EigenhandPfad } from '@/lib/api';
import { pfadHerkunft } from './pfadHerkunft';

function pfad(word: string, verfahren: string, erzeugtAm: string | null): EigenhandPfad {
  return {
    box_index: 0,
    word,
    strokes: [],
    registration_px: { tx: 0, ty: 0, baseline_row: 0 },
    xh_px: 100,
    verfahren,
    konfiguration: {},
    meta: {},
    erzeugt_am: erzeugtAm,
    flecken_n: null,
  };
}

describe('pfadHerkunft', () => {
  it('names the one run when every path came out of it', () => {
    const herkunft = pfadHerkunft(
      [pfad('lesen', 'tintenpfad', '2026-09-12'), pfad('das', 'tintenpfad', '2026-09-12')],
      'ohne Datum',
    );
    expect(herkunft).toMatchObject({ verfahren: 'tintenpfad', datum: '2026-09-12', gemischt: false });
  });

  it('refuses to let the first path speak for a later re-follow', () => {
    // The finding itself: one word was followed again on another day, and the
    // caption must not put the first word's date under both.
    const herkunft = pfadHerkunft(
      [pfad('lesen', 'tintenpfad', '2026-09-11'), pfad('das', 'tintenpfad', '2026-09-13')],
      'ohne Datum',
    );
    expect(herkunft).toMatchObject({ verfahren: 'tintenpfad', datum: null, gemischt: true });
    expect(herkunft.laeufe).toEqual(['lesen: tintenpfad · 2026-09-11', 'das: tintenpfad · 2026-09-13']);
  });

  it('counts a differing Verfahren as mixed too', () => {
    const herkunft = pfadHerkunft(
      [pfad('lesen', 'tintenpfad', '2026-09-12'), pfad('das', 'kette', '2026-09-12')],
      'ohne Datum',
    );
    expect(herkunft).toMatchObject({ verfahren: null, datum: '2026-09-12', gemischt: true });
  });

  it('names a missing day rather than dropping it, and two of them still agree', () => {
    const herkunft = pfadHerkunft([pfad('lesen', 'tintenpfad', null), pfad('das', 'tintenpfad', null)], 'ohne Datum');
    expect(herkunft).toMatchObject({ datum: 'ohne Datum', gemischt: false });
  });

  it('does not call an empty list mixed — it has nothing to disagree about', () => {
    expect(pfadHerkunft([], 'ohne Datum')).toMatchObject({ verfahren: null, datum: null, gemischt: false });
  });
});
