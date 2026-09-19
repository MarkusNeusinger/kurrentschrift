// Unit cover for the word detail's evidence list — the inversion that makes an
// untraced Wortprobe visible where the tracing actually happens.
//
// The detail used to build its list from the stored `word_instances`, so a
// sample the hand had never drawn on could not appear at all, although the
// overview listed it with its crop and deep-linked into the detail. What has to
// hold now:
//
// * a sample without a stored row STAYS in the list — that is the whole change;
// * a sample with one is paired with it, so nothing the card draws is lost;
// * the specimen named in the URL leads, so a deep link lands on it;
// * the rest is worst measured fit first, unchanged, with an untraced sample
//   last: it has nothing measured and must not rank as a perfect fit;
// * a stored row whose sample is missing from the sidecar drops out, rather
//   than producing a card with no crop to draw on;
// * the match is on the word TEXT, case- and whitespace-insensitively, exactly
//   as the free-text field hands it over.

import { describe, expect, it } from 'vitest';

import type { WordInstanceOut, WordSampleOut } from '@/lib/api';
import { wordEvidenceOf } from './model';

const sample = (id: string, word: string): WordSampleOut =>
  ({ id, word, kind: 'word' }) as unknown as WordSampleOut;

const row = (specimenId: string, word: string, unfitted: number[] = []): WordInstanceOut =>
  ({
    kind: 'word',
    specimen_id: specimenId,
    word,
    slots: [],
    strokes: [],
    provenance: 'traced',
    hand_id: 'suetterlin-1922-norm',
    measurements: { unfitted_slots: unfitted },
  }) as unknown as WordInstanceOut;

describe('wordEvidenceOf', () => {
  it('keeps a sample that carries no stored trace', () => {
    const evidence = wordEvidenceOf([sample('unter', 'unter')], [], 'unter', null);
    expect(evidence).toEqual([{ sample: sample('unter', 'unter'), row: null }]);
  });

  it('pairs a sample with its stored trace', () => {
    const traced = row('unter', 'unter');
    const evidence = wordEvidenceOf([sample('unter', 'unter')], [traced], 'unter', null);
    expect(evidence).toHaveLength(1);
    expect(evidence[0].row).toBe(traced);
  });

  it('lists every sample of the text, traced or not', () => {
    const evidence = wordEvidenceOf(
      [sample('unter-1', 'unter'), sample('unter-2', 'unter'), sample('das', 'das')],
      [row('unter-1', 'unter')],
      'unter',
      null,
    );
    expect(evidence.map((e) => e.sample.id)).toEqual(['unter-1', 'unter-2']);
    expect(evidence.map((e) => e.row !== null)).toEqual([true, false]);
  });

  it('puts the specimen named in the URL first', () => {
    const evidence = wordEvidenceOf(
      [sample('unter-1', 'unter'), sample('unter-2', 'unter')],
      [row('unter-1', 'unter', [0, 1, 2])],
      'unter',
      'unter-2',
    );
    expect(evidence.map((e) => e.sample.id)).toEqual(['unter-2', 'unter-1']);
  });

  it('ranks the worst measured fit first and an untraced sample last', () => {
    const evidence = wordEvidenceOf(
      [sample('a', 'unter'), sample('b', 'unter'), sample('c', 'unter')],
      [row('a', 'unter'), row('b', 'unter', [0, 1])],
      'unter',
      null,
    );
    expect(evidence.map((e) => e.sample.id)).toEqual(['b', 'a', 'c']);
  });

  it('drops a stored row whose sample the sidecar does not carry', () => {
    // There would be no crop to draw it on — the card needs the sample, not the
    // other way round.
    const evidence = wordEvidenceOf([], [row('unter', 'unter')], 'unter', null);
    expect(evidence).toEqual([]);
  });

  it('matches the word text the way the free-text field hands it over', () => {
    expect(wordEvidenceOf([sample('unter', 'unter')], [], '  Unter ', null)).toHaveLength(1);
    expect(wordEvidenceOf([sample('unter', 'unter')], [], '', null)).toEqual([]);
    expect(wordEvidenceOf([sample('unter', 'unter')], [], '   ', null)).toEqual([]);
  });
});
