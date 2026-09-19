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
// * an untraced Abb.-20 PAIR drill of the same two letters stays out — it is
//   the Übergänge view's subject, not a Wortprobe of that text — while one that
//   already carries a trace stays reachable, because the drill card deep-links
//   into exactly this detail;
// * a foreign writer's sample (Abb. 22) is evidence but not THIS hand's, which
//   `ownHandEvidence` is what the head counts run over;
// * the match is on the word TEXT, case- and whitespace-insensitively, exactly
//   as the free-text field hands it over.

import { describe, expect, it } from 'vitest';

import type { WordInstanceOut, WordSampleOut } from '@/lib/api';
import { ownHandEvidence, wordEvidenceOf } from './model';

const sample = (id: string, word: string, extra: Partial<WordSampleOut> = {}): WordSampleOut =>
  ({ id, word, kind: 'word', sample_set: null, ...extra }) as unknown as WordSampleOut;

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

  it('leaves an untraced pair drill out of the word detail', () => {
    // `du` is written on the Abb.-20 pair plate as well; that crop belongs to
    // the Übergänge view, and offering it here as a Wortprobe would also offer
    // it the word editor.
    const drill = sample('pairs-du', 'du', { kind: 'pair' });
    expect(wordEvidenceOf([drill], [], 'du', null)).toEqual([]);
    expect(wordEvidenceOf([drill, sample('du-1', 'du')], [], 'du', null).map((e) => e.sample.id)).toEqual(['du-1']);
  });

  it('keeps a pair drill that already carries a stored trace', () => {
    // The drill card's „im Wort ansehen" deep-links here, and the trace-only
    // list this replaces showed such a row.
    const drill = sample('pairs-du', 'du', { kind: 'pair' });
    const traced = { ...row('pairs-du', 'du'), kind: 'pair' } as WordInstanceOut;
    expect(wordEvidenceOf([drill], [traced], 'du', null)).toEqual([{ sample: drill, row: traced }]);
  });

  it('carries a foreign writer’s sample as evidence, but not as this hand’s', () => {
    const foreign = sample('abb22-und-3', 'und', { sample_set: 'abb22' });
    const mine = sample('und-1', 'und');
    const evidence = wordEvidenceOf([mine, foreign], [], 'und', null);
    expect(evidence).toHaveLength(2);
    expect(ownHandEvidence(evidence).map((e) => e.sample.id)).toEqual(['und-1']);
  });

  it('does not treat an empty set tag as another hand', () => {
    const evidence = wordEvidenceOf([sample('und-1', 'und', { sample_set: '' })], [], 'und', null);
    expect(ownHandEvidence(evidence)).toHaveLength(1);
  });
});
