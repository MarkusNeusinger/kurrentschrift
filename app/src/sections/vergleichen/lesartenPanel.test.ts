import { describe, expect, it } from 'vitest';

import type { LesartDictionaryOut, LesartReadingOut } from '@/lib/api';
import { de } from '@/locales';
import { lesartenState, showsDictionaryNote } from './lesartenPanel';

const t = de.vergleichen;
const DICTIONARY: LesartDictionaryOut = { source: 'igerman98', forms: 719_000, sha256: 'a1b2c3' };
const READING: LesartReadingOut = { word: 'Muhme', bank: false, cost: 1, swaps: [{ index: 1, from: 'n', to: 'u' }] };

// The copy each state puts on the page — the mapping VergleichenView renders.
const copy: Record<string, string | null> = {
  loading: t.lesartenLoading,
  error: t.lesartenError,
  noDictionary: t.noDictionary,
  staleDictionary: t.staleDictionary,
  noReadings: t.noLesarten,
  readings: null, // the grid, no sentence
};

describe('lesartenPanel', () => {
  it('says the dictionary is missing instead of calling the reading unique', () => {
    // The live answer of 2026-09-02: no dictionary loaded, so no words —
    // which is NOT the same as „nothing looks like it".
    const state = lesartenState([], null, false);
    expect(state).toBe('noDictionary');
    expect(copy[state]).toBe(t.noDictionary);
    expect(copy[state]).not.toBe(t.noLesarten);
    expect(copy[state]).not.toMatch(/eindeutig/);
    // …and the provenance line stays away, so the page says it once.
    expect(showsDictionaryNote(null)).toBe(false);
  });

  it('calls a reading unique only when a dictionary looked for it', () => {
    expect(lesartenState([], DICTIONARY, false)).toBe('noReadings');
    expect(copy.noReadings).toBe(t.noLesarten);
    expect(showsDictionaryNote(DICTIONARY)).toBe(true);
  });

  it('does not call a reading unique while the vocabulary is sorted by the old classes', () => {
    // Between the deploy of a new look-alike pair and the reload, the server
    // looks for the guess in a bucket the stored words are not in — the same
    // „empty shelf" mistake as above, one step further in.
    const stale: LesartDictionaryOut = { ...DICTIONARY, stale: true };
    const state = lesartenState([], stale, false);
    expect(state).toBe('staleDictionary');
    expect(copy[state]).not.toMatch(/eindeutig/);
    // Readings that DID come back are real words and stay on the page.
    expect(lesartenState([READING], stale, false)).toBe('readings');
  });

  it('shows the readings when there are any', () => {
    expect(lesartenState([READING], DICTIONARY, false)).toBe('readings');
    expect(copy.readings).toBeNull();
    expect(showsDictionaryNote(DICTIONARY)).toBe(true);
  });

  it('keeps loading and error ahead of every empty state', () => {
    // No answer for the current text yet — neither empty state may show.
    expect(lesartenState(null, undefined, false)).toBe('loading');
    expect(showsDictionaryNote(undefined)).toBe(false);
    // A failed request is an outage, not an answer about the words.
    expect(lesartenState(null, null, true)).toBe('error');
    expect(lesartenState([], null, true)).toBe('error');
  });
});
