// „Wo kommt diese Bahn her?" — and the case the caption used to get wrong.
//
// A Fassung's paths can come out of several runs: `tools.eigenhand.pfad` merges
// what it followed over what was stored, so one re-followed word can sit beside
// words from an older day. The caption read Verfahren and day off `pfade[0]`
// and put them under all of them (Copilot review, PR #598). Two paths from two
// runs still look like two paths on a screenshot, so the property is pinned
// here rather than inspected by eye.

import { describe, expect, it } from 'vitest';

import type { EigenhandPfad } from '@/lib/api';
import { herkunftChipLabel, pfadHerkunft, verfahrenLabel } from './pfadHerkunft';

// Stand-ins for the two locale strings, so a wording change never turns this
// suite red and the assertions stay about the MAPPING.
const LABELS = { tintenpfad: 'automatisch (Tintenpfad)', authored: 'von Hand' };

function pfad(word: string, verfahren: string, erzeugtAm: string | null): EigenhandPfad {
  return {
    box_index: 0,
    word,
    status: null,
    grund: null,
    detail: null,
    strokes: [],
    letter_spans: null,
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
      LABELS,
    );
    expect(herkunft).toMatchObject({ verfahren: 'tintenpfad', datum: '2026-09-12', gemischt: false });
  });

  it('refuses to let the first path speak for a later re-follow', () => {
    // The finding itself: one word was followed again on another day, and the
    // caption must not put the first word's date under both.
    const herkunft = pfadHerkunft(
      [pfad('lesen', 'tintenpfad', '2026-09-11'), pfad('das', 'tintenpfad', '2026-09-13')],
      'ohne Datum',
      LABELS,
    );
    expect(herkunft).toMatchObject({ verfahren: 'tintenpfad', datum: null, gemischt: true });
    expect(herkunft.laeufe).toEqual([
      'lesen: automatisch (Tintenpfad) · 2026-09-11',
      'das: automatisch (Tintenpfad) · 2026-09-13',
    ]);
  });

  it('counts a differing Verfahren as mixed too', () => {
    const herkunft = pfadHerkunft(
      [pfad('lesen', 'tintenpfad', '2026-09-12'), pfad('das', 'kette', '2026-09-12')],
      'ohne Datum',
      LABELS,
    );
    expect(herkunft).toMatchObject({ verfahren: null, datum: '2026-09-12', gemischt: true });
  });

  it('names a missing day rather than dropping it, and two of them still agree', () => {
    const herkunft = pfadHerkunft(
      [pfad('lesen', 'tintenpfad', null), pfad('das', 'tintenpfad', null)],
      'ohne Datum',
      LABELS,
    );
    expect(herkunft).toMatchObject({ datum: 'ohne Datum', gemischt: false });
  });

  it('does not call an empty list mixed — it has nothing to disagree about', () => {
    expect(pfadHerkunft([], 'ohne Datum', LABELS)).toMatchObject({
      verfahren: null,
      datum: null,
      gemischt: false,
    });
  });

  it('keeps a mixed run from naming one method, even when both labels agree', () => {
    // Two followers can legitimately share a chip label. The agreement is read
    // off the RAW column, so the caption still falls to „verschiedene Läufe"
    // rather than inventing one run out of two.
    const sameWording = { tintenpfad: 'automatisch', authored: 'automatisch' };
    const herkunft = pfadHerkunft(
      [pfad('lesen', 'tintenpfad', '2026-09-12'), pfad('das', 'authored', '2026-09-12')],
      'ohne Datum',
      sameWording,
    );
    expect(herkunft).toMatchObject({ verfahren: null, gemischt: true });
  });
});

describe('herkunftChipLabel', () => {
  it('keeps naming the one Verfahren when only the days differ', () => {
    // The Copilot finding of PR #621: a word followed again on another day
    // makes the Fassung mixed, but says nothing about HOW any of them were
    // followed — so the chip must not vanish with the date.
    const herkunft = pfadHerkunft(
      [pfad('lesen', 'tintenpfad', '2026-09-11'), pfad('das', 'tintenpfad', '2026-09-13')],
      'ohne Datum',
      LABELS,
    );
    expect(herkunft.gemischt).toBe(true);
    expect(herkunftChipLabel(herkunft, LABELS)).toBe('automatisch (Tintenpfad)');
  });

  it('names nothing when the Verfahren themselves differ', () => {
    const herkunft = pfadHerkunft(
      [pfad('lesen', 'tintenpfad', '2026-09-12'), pfad('das', 'authored', '2026-09-12')],
      'ohne Datum',
      LABELS,
    );
    expect(herkunftChipLabel(herkunft, LABELS)).toBeNull();
  });

  it('names nothing for a Fassung without a single stored path', () => {
    expect(herkunftChipLabel(pfadHerkunft([], 'ohne Datum', LABELS), LABELS)).toBeNull();
  });

  it('hands an unknown Verfahren to the chip raw', () => {
    const herkunft = pfadHerkunft([pfad('lesen', 'lotse-2027', '2026-09-12')], 'ohne Datum', LABELS);
    expect(herkunftChipLabel(herkunft, LABELS)).toBe('lotse-2027');
  });
});

describe('verfahrenLabel', () => {
  it('names the two Verfahren the strip store writes', () => {
    expect(verfahrenLabel('tintenpfad', LABELS)).toBe('automatisch (Tintenpfad)');
    expect(verfahrenLabel('authored', LABELS)).toBe('von Hand');
  });

  it('hands an unknown Verfahren back unchanged', () => {
    // `verfahren` is a free 64-character column. A run from another follower
    // must stay readable under ITS name — relabelling it „automatisch
    // (Tintenpfad)" would be a claim about how the line was made.
    expect(verfahrenLabel('kette', LABELS)).toBe('kette');
    expect(verfahrenLabel('lotse-2027', LABELS)).toBe('lotse-2027');
    expect(verfahrenLabel('', LABELS)).toBe('');
  });
});
