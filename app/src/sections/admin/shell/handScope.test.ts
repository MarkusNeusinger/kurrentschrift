import { describe, expect, it } from 'vitest';

import { handCandidates, handStyle, handsOfStyle, resolveHand, styleOfHand } from './handScope';

// The style list as `GET /eigenhand/hands` ships it (core/eigenhand/ids.py
// STYLE_IDS) — read from the server on purpose, so this module never becomes a
// second place where the three scripts are written down.
const STYLES = ['kurrent', 'suetterlin', 'offenbacher'];

describe('style of a hand', () => {
  it('reads the script out of the id suffix', () => {
    expect(styleOfHand('mn-suetterlin', STYLES)).toBe('suetterlin');
    expect(styleOfHand('zweithand-kurrent', STYLES)).toBe('kurrent');
    expect(styleOfHand('mn-zweite-suetterlin', STYLES)).toBe('suetterlin');
  });

  it('names no script for an id that spells none', () => {
    expect(styleOfHand('mn', STYLES)).toBeNull();
    expect(styleOfHand('mn-fraktur', STYLES)).toBeNull();
    // „suetterlin" without the separator is a different hand, not this script.
    expect(styleOfHand('mnsuetterlin', STYLES)).toBeNull();
    // And the PLATE hands are none of this: `suetterlin-1922-norm` is a row of
    // the writer registry, whose ids put the script in FRONT. They reach the
    // admin through the per-panel statistics, never through this field — which
    // is exactly the distinction P1-Q3 a draws.
    expect(styleOfHand('suetterlin-1922-norm', STYLES)).toBeNull();
  });
});

describe('the candidate hands', () => {
  it('unions the two reads, and lets a setup state the script', () => {
    // /eigenhand/hands is built from sheets ∪ Fassungen, so `neu-suetterlin`
    // — a hand whose setup was typed before its first sheet — appears only in
    // the setups. A candidate set from one read alone would hide it.
    const candidates = handCandidates(
      ['mn-suetterlin'],
      [
        { hand: 'neu-suetterlin', style: 'suetterlin' },
        // The setup wins over the suffix: it STATES the script, the suffix
        // only guesses it — and here the suffix would guess nothing at all.
        { hand: 'gastschreiber', style: 'kurrent' },
      ],
      STYLES,
    );
    expect(candidates).toEqual([
      { id: 'gastschreiber', style: 'kurrent' },
      { id: 'mn-suetterlin', style: 'suetterlin' },
      { id: 'neu-suetterlin', style: 'suetterlin' },
    ]);
  });

  it('keeps one entry per hand when both reads know it', () => {
    const candidates = handCandidates(['mn-suetterlin'], [{ hand: 'mn-suetterlin', style: 'suetterlin' }], STYLES);
    expect(candidates).toEqual([{ id: 'mn-suetterlin', style: 'suetterlin' }]);
  });

  it('never offers a hand of another script', () => {
    const candidates = handCandidates(['mn-suetterlin', 'zweithand-kurrent', 'namenlos'], [], STYLES);
    expect(handsOfStyle(candidates, 'suetterlin')).toEqual(['mn-suetterlin']);
    expect(handsOfStyle(candidates, 'kurrent')).toEqual(['zweithand-kurrent']);
    // A hand whose id names no script belongs to none — it is never a pick.
    expect(handsOfStyle(candidates, 'offenbacher')).toEqual([]);
    expect(handsOfStyle(candidates, null)).toEqual([]);
    expect(handStyle(candidates, 'namenlos')).toBeNull();
    expect(handStyle(candidates, 'gibtsnicht')).toBeNull();
  });
});

describe('the active hand (V19)', () => {
  const candidates = handCandidates(
    ['mn-suetterlin', 'zweit-suetterlin', 'mn-kurrent'],
    [],
    STYLES,
  );

  it('keeps the chosen hand while it belongs to the Vorlage', () => {
    expect(resolveHand('zweit-suetterlin', 'suetterlin', candidates, {})).toBe('zweit-suetterlin');
  });

  it('drops a foreign-script hand on a style change and takes the last one of that script', () => {
    expect(resolveHand('mn-kurrent', 'suetterlin', candidates, { suetterlin: 'zweit-suetterlin' })).toBe(
      'zweit-suetterlin',
    );
  });

  it('falls back to the first candidate, then to nothing', () => {
    expect(resolveHand(null, 'suetterlin', candidates, {})).toBe('mn-suetterlin');
    // A remembered hand that no read knows any more is not a pick either.
    expect(resolveHand(null, 'kurrent', candidates, { kurrent: 'geloescht-kurrent' })).toBe('mn-kurrent');
    // „oder leer": a script with no written hand keeps the field empty rather
    // than borrowing another script's.
    expect(resolveHand('mn-suetterlin', 'offenbacher', candidates, { offenbacher: 'mn-suetterlin' })).toBeNull();
    expect(resolveHand('mn-suetterlin', null, candidates, {})).toBeNull();
    expect(resolveHand(null, 'suetterlin', [], {})).toBeNull();
  });

  it('gives two Vorlagen of ONE script the same hand', () => {
    // Q25 a: the hand belongs to the script, not to the chart. Both Kurrent
    // Vorlagen therefore resolve to the same hand — which is why the choice
    // may not live under the per-source remount.
    const chosen = 'mn-kurrent';
    const loth = resolveHand(chosen, 'kurrent', candidates, { kurrent: chosen });
    const petzendorfer = resolveHand(chosen, 'kurrent', candidates, { kurrent: chosen });
    expect(loth).toBe('mn-kurrent');
    expect(petzendorfer).toBe(loth);
  });
});
