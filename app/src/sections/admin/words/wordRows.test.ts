import { describe, expect, it } from 'vitest';

import type { WordInstanceOut, WordSampleOut, WordSampleScoreOut } from '@/lib/api';
import { writeListState } from '@/sections/admin/shell/listState';

import {
  WORD_LIST_SPEC,
  WORD_SORTS,
  buildWordRows,
  matchesWordFilters,
  rankingIsStale,
  settledScores,
  sortWordRows,
  traceFilterOf,
  wordTabOf,
  wordTally,
  wordsRankable,
  type WordRow,
} from './wordRows';

const sample = (id: string, word: string, over: Partial<WordSampleOut> = {}): WordSampleOut => ({
  id,
  word,
  kind: 'word',
  sample_set: null,
  width: 400,
  height: 120,
  baseline_y: 90,
  midband_y: 50,
  ...over,
});

const trace = (specimenId: string, provenance: string): WordInstanceOut =>
  ({ specimen_id: specimenId, word: 'x', kind: 'word', provenance }) as unknown as WordInstanceOut;

const score = (id: string, loss: number, failed = false): WordSampleScoreOut =>
  ({ id, word: 'x', loss, failed, missing: [], segments: [] }) as WordSampleScoreOut;

const input = (over: Partial<Parameters<typeof buildWordRows>[0]> = {}) => ({
  samples: [sample('s1', 'lesen'), sample('s2', 'das'), sample('s3', 'denen')],
  tracesBySpecimen: new Map<string, WordInstanceOut[]>([['s1', [trace('s1', 'authored')]]]),
  tab: 'woerter' as const,
  korbByWord: new Map<string, number>([['das', 1]]),
  scores: {} as Record<string, WordSampleScoreOut | undefined>,
  ...over,
});

const row = (rows: WordRow[], id: string): WordRow => {
  const found = rows.find((r) => r.sampleId === id);
  expect(found, id).toBeDefined();
  return found as WordRow;
};

describe('which tab a Wortprobe stands in', () => {
  it('sorts the plate words, the foreign hand and the pair drills apart', () => {
    expect(wordTabOf(sample('a', 'lesen'))).toBe('woerter');
    expect(wordTabOf(sample('b', 'lesen', { sample_set: 'abb22' }))).toBe('andere');
    // The Abb.-20 drills belong to neither tab: they are pure joins and have
    // their home under Übergänge.
    expect(wordTabOf(sample('c', 'ab', { kind: 'pair' }))).toBeNull();
    // Truthiness, not `!= null`: an empty tag is not another hand.
    expect(wordTabOf(sample('d', 'lesen', { sample_set: '' }))).toBe('woerter');
  });

  it('lists only the rows of the chosen tab', () => {
    const samples = [sample('s1', 'lesen'), sample('s2', 'du', { sample_set: 'abb22' }), sample('s3', 'ab', { kind: 'pair' })];
    expect(buildWordRows(input({ samples })).map((r) => r.sampleId)).toEqual(['s1']);
    expect(buildWordRows(input({ samples, tab: 'andere' })).map((r) => r.sampleId)).toEqual(['s2']);
  });
});

describe('what one row knows', () => {
  it('counts the stored Bahnen and reports the Nachfahr-Status beside them', () => {
    const rows = buildWordRows(input());
    // Two statements, not one: a stored line exists, AND the author drew it.
    expect(row(rows, 's1')).toMatchObject({ traces: 1, status: 'authored' });
    expect(row(rows, 's2')).toMatchObject({ traces: 0, status: 'open' });
  });

  it('counts a harvested fit as a Bahn without calling it nachgefahren', () => {
    const rows = buildWordRows(
      input({ tracesBySpecimen: new Map([['s1', [trace('s1', 'traced')]]]) }),
    );
    expect(row(rows, 's1')).toMatchObject({ traces: 1, status: 'open' });
  });

  it('registers the overlay on the AUTHORED line where one exists', () => {
    const rows = buildWordRows(
      input({ tracesBySpecimen: new Map([['s1', [trace('s1', 'traced'), trace('s1', 'authored')]]]) }),
    );
    expect(row(rows, 's1').traced?.provenance).toBe('authored');
    expect(row(rows, 's1').traces).toBe(2);
  });

  it('calls a clipped specimen unvollständig, and lets an authored line overrule the flag', () => {
    const samples = [sample('s1', 'lesen', { incomplete: true }), sample('s2', 'das', { incomplete: true })];
    const rows = buildWordRows(input({ samples }));
    expect(row(rows, 's2').status).toBe('incomplete');
    // Where a flagged specimen was traced anyway, the stored line is the truth
    // about it, not the flag.
    expect(row(rows, 's1').status).toBe('authored');
  });

  it('names the foreign writer', () => {
    const rows = buildWordRows(
      input({ samples: [sample('s9', 'du', { sample_set: 'abb22' })], tab: 'andere' }),
    );
    expect(row(rows, 's9')).toMatchObject({ foreign: true, foreignSet: 'abb22' });
    expect(buildWordRows(input()).every((r) => r.foreign === false)).toBe(true);
  });

  it('carries no score at all until one was computed — never a zero', () => {
    const rows = buildWordRows(input());
    expect(row(rows, 's1')).toMatchObject({ loss: null, scoreFailed: false, score: null });
    const scored = buildWordRows(input({ scores: { s1: score('s1', 0.31) } }));
    expect(row(scored, 's1').loss).toBe(0.31);
  });

  it('gives a failed score no loss, but says that it failed', () => {
    // „nicht bewertbar" is an answer about the Wortprobe; borrowing its number
    // would rank it beside the measured ones.
    const rows = buildWordRows(input({ scores: { s1: score('s1', 9.9, true) } }));
    expect(row(rows, 's1')).toMatchObject({ loss: null, scoreFailed: true });
  });

  it('keeps an unanswered basket read out of the row', () => {
    expect(row(buildWordRows(input()), 's2').korbOpen).toBe(1);
    expect(row(buildWordRows(input()), 's1').korbOpen).toBe(0);
    expect(row(buildWordRows(input({ korbByWord: null })), 's2').korbOpen).toBeNull();
  });
});

describe('the two selecting axes', () => {
  const rows = buildWordRows(input());

  it('translates the URL word into the filter the evidence model speaks', () => {
    expect(traceFilterOf('alle')).toBe('all');
    expect(traceFilterOf('offen')).toBe('open');
    expect(traceFilterOf('nachgefahren')).toBe('authored');
    expect(traceFilterOf('unvollstaendig')).toBe('incomplete');
    expect(traceFilterOf(null)).toBe('all');
  });

  it('selects by status', () => {
    expect(rows.filter((r) => matchesWordFilters(r, 'nachgefahren', '')).map((r) => r.sampleId)).toEqual(['s1']);
    expect(rows.filter((r) => matchesWordFilters(r, 'offen', '')).map((r) => r.sampleId)).toEqual(['s2', 's3']);
    expect(rows.filter((r) => matchesWordFilters(r, 'alle', ''))).toHaveLength(3);
  });

  it('searches the WORD, case- and space-insensitively — never the specimen id', () => {
    expect(rows.filter((r) => matchesWordFilters(r, 'alle', 'EN')).map((r) => r.word)).toEqual(['lesen', 'denen']);
    expect(rows.filter((r) => matchesWordFilters(r, 'alle', '  das  ')).map((r) => r.word)).toEqual(['das']);
    // „s1" is a specimen id, not a word — otherwise every plate whose id
    // spells a common fragment would answer a search for that fragment.
    expect(rows.filter((r) => matchesWordFilters(r, 'alle', 's1'))).toEqual([]);
  });

  it('ANDs the status and the needle', () => {
    expect(rows.filter((r) => matchesWordFilters(r, 'offen', 'en')).map((r) => r.word)).toEqual(['denen']);
  });
});

describe('the order of the rows', () => {
  it('keeps the sidecar order by default', () => {
    expect(sortWordRows(buildWordRows(input()), 'reihenfolge').map((r) => r.sampleId)).toEqual(['s1', 's2', 's3']);
  });

  it('puts the worst Loss first and the unscored rows last', () => {
    const rows = buildWordRows(input({ scores: { s1: score('s1', 0.2), s3: score('s3', 0.5) } }));
    expect(sortWordRows(rows, 'schlechteste').map((r) => r.sampleId)).toEqual(['s3', 's1', 's2']);
  });

  it('reports whether there is anything to rank by', () => {
    expect(wordsRankable(buildWordRows(input()))).toBe(false);
    expect(wordsRankable(buildWordRows(input({ scores: { s1: score('s1', 0.2) } })))).toBe(true);
    // A failed score is not a rank.
    expect(wordsRankable(buildWordRows(input({ scores: { s1: score('s1', 0.2, true) } })))).toBe(false);
  });
});

describe('a ranking that no longer describes the list', () => {
  const unscored = buildWordRows(input());
  const scored = buildWordRows(input({ scores: { s1: score('s1', 0.2) } }));

  it('is stale once the rows carry no Loss — and only then', () => {
    // „Neu laden" cleared the measurements, or the link was pasted into a
    // fresh session: the URL says „Schlechteste zuerst" over the plate's
    // order, and the toolbar shows that option disabled AND selected.
    expect(rankingIsStale(unscored, 'schlechteste', true)).toBe(true);
    expect(rankingIsStale(scored, 'schlechteste', true)).toBe(false);
    expect(rankingIsStale(unscored, 'reihenfolge', true)).toBe(false);
  });

  it('says nothing while the read is out or the tab is empty', () => {
    // Neither silence is an answer about the rows — dropping the axis there
    // would eat a deep link's ranking before its data arrived.
    expect(rankingIsStale(unscored, 'schlechteste', false)).toBe(false);
    expect(rankingIsStale([], 'schlechteste', true)).toBe(false);
  });

  it('leaves the rest of the list state alone when the view drops it', () => {
    const out = writeListState(
      new URLSearchParams('sort=schlechteste&seite=3&filter=en&reiter=andere&w=lesen'),
      { sort: WORD_SORTS[0], page: 3 },
      WORD_LIST_SPEC,
    );
    // The default sort is absent from a clean URL — which is how it is dropped.
    expect(out.get('sort')).toBeNull();
    // The axis never changed the order, so the reader does not move either.
    expect(out.get('seite')).toBe('3');
    expect(out.get('filter')).toBe('en');
    expect(out.get('reiter')).toBe('andere');
    expect(out.get('w')).toBe('lesen');
  });
});

describe('the score record the view holds', () => {
  it('hands the rows the answers and keeps the sentinels of a running request', () => {
    const measured = score('s1', 0.4);
    expect(settledScores({ s1: measured, s2: 'busy', s3: 'error', s4: undefined })).toEqual({ s1: measured });
  });

  it('never lets a running request read as a Loss', () => {
    const rows = buildWordRows(input({ scores: settledScores({ s1: 'busy' }) }));
    expect(row(rows, 's1')).toMatchObject({ loss: null, scoreFailed: false });
    expect(wordsRankable(rows)).toBe(false);
  });
});

describe('the progress tally', () => {
  it('counts the authored rows and leaves the clipped ones out of the total', () => {
    const samples = [
      sample('s1', 'lesen'),
      sample('s2', 'das'),
      sample('s3', 'denen', { incomplete: true }),
    ];
    expect(wordTally(buildWordRows(input({ samples })))).toEqual({ done: 1, total: 2, incomplete: 1 });
  });
});
