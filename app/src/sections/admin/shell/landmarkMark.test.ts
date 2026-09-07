// The Landmarken-Linse's half of the Auftragskorb contract
// (optimierungs-werkbank.md §8): a landmark complaint carries WHICH marker on
// WHICH row with WHICH numbers, because the row is all a working session gets.
// The note's first line is that contract — pinned here so a rename or a
// reordering cannot quietly turn it into prose.

import { describe, expect, it } from 'vitest';

import {
  landmarkLabel,
  landmarkNoteHead,
  markKey,
  targetLabel,
  workItemBodyOf,
  type LandmarkRef,
  type Mark,
} from './model';

const kringel: LandmarkRef = {
  kind: 'loop',
  index: 1,
  x: 0.4211,
  y: 0.6134,
  numbers: { d0: 0.3122, size_class: 'klein', state: 'punkt', anchor_range: null },
};

const markOf = (landmark: LandmarkRef, variant = 0): Mark => ({
  target: { kind: 'landmark', glyphKey: 'd', variant, landmark },
});

describe('landmark marks', () => {
  it('labels a marker by its kind and index', () => {
    expect(landmarkLabel(kringel)).toBe('Kringel #1');
    expect(targetLabel(markOf(kringel).target)).toBe('Landmarke Kringel #1 · d');
  });

  it('names the empty-area report without an index', () => {
    const spot: LandmarkRef = { kind: 'spot', index: null, x: 0.1, y: 0.2, numbers: {} };
    expect(landmarkLabel(spot)).toBe('Stelle ohne Marke');
    expect(targetLabel(markOf(spot).target)).toBe('Landmarke Stelle ohne Marke · d');
  });

  it('files a position-less report as the identity alone, never as the origin', () => {
    // The keyboard path and an unmatched catalogue Kringel have no detected
    // place. Inventing (0, 0) would file a measurement that never happened.
    const spot: LandmarkRef = { kind: 'spot', index: null, numbers: {} };
    expect(landmarkNoteHead(markOf(spot).target)).toBe(
      'Landmarke: Stelle ohne Marke (spot) · d · Tafel-Duktus (Variante 0)',
    );
    const unmatched: LandmarkRef = { kind: 'loop', index: 1, numbers: { state: 'punkt' } };
    const head = landmarkNoteHead(markOf(unmatched).target);
    expect(head).toContain('state punkt');
    expect(head).not.toContain('x 0.0000');
  });

  it('writes identity on the first line and the measured numbers on the second', () => {
    const [identity, numbers, ...rest] = landmarkNoteHead(markOf(kringel).target).split('\n');
    expect(identity).toBe('Landmarke: Kringel #1 (loop#1) · d · Tafel-Duktus (Variante 0)');
    // The machine token, the position and every non-null number travel — a
    // session reproduces the complaint from this line alone.
    expect(numbers).toBe('x 0.4211 · y 0.6134 · d0 0.3122 · size_class klein · state punkt');
    expect(rest).toEqual([]);
  });

  it('says which stored row the marker was read on', () => {
    expect(landmarkNoteHead(markOf(kringel, 100).target)).toContain('Laufform (Variante 100)');
  });

  it('drops a null number rather than filing "anchor_range null"', () => {
    expect(landmarkNoteHead(markOf(kringel).target)).not.toContain('anchor_range');
  });

  it('files as kind landmark on the letter, head first and the note under it', () => {
    const body = workItemBodyOf(markOf(kringel), 'Der Kringel ist hier offen, nicht zu.');
    expect(body.kind).toBe('landmark');
    expect(body.glyph_key).toBe('d');
    expect(body.note?.startsWith('Landmarke: Kringel #1 (loop#1)')).toBe(true);
    expect(body.note?.endsWith('Der Kringel ist hier offen, nicht zu.')).toBe(true);
  });

  it('still files something workable when the author adds no words', () => {
    // The API refuses a landmark item with an empty note, and it should never
    // have to: the lens always writes the head.
    expect(workItemBodyOf(markOf(kringel), '').note?.trim()).not.toBe('');
  });

  it('keeps two empty-area reports on one letter apart', () => {
    const here: LandmarkRef = { kind: 'spot', index: null, x: 0.1, y: 0.2, numbers: {} };
    const there: LandmarkRef = { kind: 'spot', index: null, x: 0.9, y: 0.4, numbers: {} };
    expect(markKey(markOf(here))).not.toBe(markKey(markOf(there)));
    // A position-less one carries no coordinate in its key either.
    expect(markKey(markOf({ kind: 'spot', index: null, numbers: {} }))).not.toContain('@');
  });
});
