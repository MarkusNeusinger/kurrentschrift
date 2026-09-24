// The Abzugs-Linse's half of the Auftragskorb contract (optimierungs-werkbank.md
// §9): a deduction files as a PLAIN LETTER item — no kind or stage of its own
// (author decision 2026-09-23) — and the note's head is what tells a working
// session which site of which category, with which numbers. Pinned here so a
// rename or a reordering cannot quietly turn it into prose.

import { describe, expect, it } from 'vitest';

import { markKey, penaltyLabel, penaltyNoteHead, targetLabel, workItemBodyOf, type Mark, type PenaltyRef } from './model';

const corner: PenaltyRef = {
  category: 'corner',
  index: 1,
  kind: 'corner',
  value: 0.0954,
  categoryValue: 0.1711,
  exact: true,
  pointsEst: 2.28,
  x: 72.6,
  y: 24.86,
  numbers: { anchor: 71, sample: 142, s_in: 0.1187, s_out: 0.1218, q: 0.6182 },
};

const markOf = (penalty: PenaltyRef, glyphKey = 'a'): Mark => ({ target: { kind: 'penalty', glyphKey, penalty } });

describe('penalty marks', () => {
  it('names a site by its category label and its payload index', () => {
    expect(penaltyLabel(corner)).toBe('Ecken #1');
    expect(penaltyLabel({ category: 'collinearity', index: 0 })).toBe('Kreuzungsflucht #0');
  });

  it('tells the filing dialog it is a LETTER item about a deduction', () => {
    expect(targetLabel(markOf(corner).target)).toBe('Buchstabe a · Abzug Ecken #1');
  });

  it('writes the identity and the site’s part of its number on the first line', () => {
    const [identity] = penaltyNoteHead(markOf(corner).target as Extract<Mark['target'], { kind: 'penalty' }>).split('\n');
    expect(identity).toBe('Abzug: Ecken #1 (corner#1) · a · Tafel-Duktus (Variante 0) · 0.0954 von 0.1711');
  });

  it('puts the kind of part, the points, the position and every number on the second', () => {
    const [, details, ...rest] = penaltyNoteHead(
      markOf(corner).target as Extract<Mark['target'], { kind: 'penalty' }>,
    ).split('\n');
    expect(details).toBe(
      'Term · ≈ 2.28 Punkte · kind corner · x 72.6 px · y 24.86 px · anchor 71 · sample 142 · s_in 0.1187 · s_out 0.1218 · q 0.6182',
    );
    expect(rest).toEqual([]);
  });

  it('says „ohne Ort" for a part without a place instead of inventing one', () => {
    const rim: PenaltyRef = {
      ...corner,
      category: 'coverage',
      index: 47,
      kind: 'rim',
      exact: false,
      x: null,
      y: null,
      numbers: { missed_px: 310, excess_px: 41, rim_px: 1.5, note: null },
    };
    const head = penaltyNoteHead(markOf(rim).target as Extract<Mark['target'], { kind: 'penalty' }>);
    expect(head).toContain('Anteil · ≈ 2.28 Punkte · kind rim · ohne Ort · missed_px 310');
    expect(head).not.toContain('x null');
    // A null number is dropped, never filed as „note null".
    expect(head).not.toContain('note');
  });

  it('files as a plain letter item, head first and the author’s words under it', () => {
    const body = workItemBodyOf(markOf(corner), 'Die Ecke ist gewollt rund.');
    expect(body.kind).toBe('letter');
    expect(body.glyph_key).toBe('a');
    expect(body.note?.startsWith('Abzug: Ecken #1 (corner#1)')).toBe(true);
    expect(body.note?.endsWith('\n\nDie Ecke ist gewollt rund.')).toBe(true);
  });

  it('still files the head when the author adds no words', () => {
    expect(workItemBodyOf(markOf(corner), '').note).toBe(
      penaltyNoteHead(markOf(corner).target as Extract<Mark['target'], { kind: 'penalty' }>),
    );
  });

  it('keeps two sites of one letter apart', () => {
    expect(markKey(markOf(corner))).not.toBe(markKey(markOf({ ...corner, index: 3 })));
  });
});
