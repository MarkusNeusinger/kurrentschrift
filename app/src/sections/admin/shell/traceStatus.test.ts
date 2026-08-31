// Unit cover for the word overview's tracing status — the value both the
// „Offen"/„Nachgefahren"/„Unvollständig" filter and the toolbar tally read.
//
// What has to hold, because the to-do list is only trustworthy if it does:
//
// * a stored HAND trace means done — an automatic `traced`/`harvested` row does
//   not, it is exactly what the pass is there to replace;
// * a specimen the sidecar flags as clipped is never „offen": no one can trace
//   a cut-off i-dot, so leaving it in the open list would keep the pass
//   permanently unfinishable;
// * but a flagged specimen that WAS traced anyway reads as done — the stored
//   line is the truth about it, not the flag;
// * a payload without the flag (the cached pre-`incomplete` schema still
//   served by a CDN after a deploy) reads as unflagged rather than crashing.

import { describe, expect, it } from 'vitest';

import type { WordInstanceOut, WordSampleOut } from '@/lib/api';
import { matchesTraceFilter, traceStatusOf } from './model';

const sample = (incomplete?: boolean): WordSampleOut =>
  ({ id: 'unter', word: 'unter', kind: 'word', incomplete }) as unknown as WordSampleOut;

const row = (provenance: string): WordInstanceOut => ({ provenance }) as unknown as WordInstanceOut;

describe('traceStatusOf', () => {
  it('reads an authored trace as done', () => {
    expect(traceStatusOf(sample(), row('authored'))).toBe('authored');
  });

  it('leaves an automatic fit open — that is the work, not its result', () => {
    expect(traceStatusOf(sample(), row('traced'))).toBe('open');
    expect(traceStatusOf(sample(), row('harvested'))).toBe('open');
    expect(traceStatusOf(sample(), null)).toBe('open');
    expect(traceStatusOf(sample(), undefined)).toBe('open');
  });

  it('takes a clipped specimen out of the open list', () => {
    expect(traceStatusOf(sample(true), null)).toBe('incomplete');
    expect(traceStatusOf(sample(true), row('traced'))).toBe('incomplete');
  });

  it('still reads a clipped specimen as done once it carries a hand trace', () => {
    expect(traceStatusOf(sample(true), row('authored'))).toBe('authored');
  });

  it('treats a payload without the flag as unflagged', () => {
    expect(traceStatusOf({ id: 'x', word: 'x' } as unknown as WordSampleOut, null)).toBe('open');
  });
});

describe('matchesTraceFilter', () => {
  it('lets everything through under „Alle"', () => {
    for (const status of ['authored', 'open', 'incomplete'] as const) {
      expect(matchesTraceFilter('all', status)).toBe(true);
    }
  });

  it('keeps the three states apart', () => {
    expect(matchesTraceFilter('open', 'open')).toBe(true);
    expect(matchesTraceFilter('open', 'incomplete')).toBe(false);
    expect(matchesTraceFilter('open', 'authored')).toBe(false);
    expect(matchesTraceFilter('incomplete', 'incomplete')).toBe(true);
    expect(matchesTraceFilter('authored', 'authored')).toBe(true);
  });
});
