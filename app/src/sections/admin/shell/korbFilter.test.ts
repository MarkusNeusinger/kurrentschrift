// Unit cover for the Auftragskorb drawer's filter and grouping.
//
// What has to hold, because the basket is the workbench's to-do list and a
// filter that lies about it is worse than no filter:
//
// * the drawer opens showing everything — nothing may be hidden before the
//   author touched a control;
// * the handed-back rows stay on top whatever the filter does, because those
//   are the ones waiting on a human;
// * a chosen Stufe never matches a row without one. The API asks for a `stage`
//   only when a row CLOSES, so the live queue has none — a filter that swept it
//   into a stage bucket would invent a diagnosis;
// * choosing „Erledigt" reveals the archive even while „erledigte anzeigen" is
//   off, and only then.

import { describe, expect, it } from 'vitest';

import type { WorkItemKind, WorkItemOut, WorkItemStage, WorkItemStatus } from '@/lib/api';
import { groupKorb, isKorbFilterAll, korbArchiveVisible, KORB_FILTER_ALL, matchesKorbFilter } from './korbFilter';

let nextId = 1;
const row = (status: WorkItemStatus, kind: WorkItemKind = 'letter', stage: WorkItemStage | null = null): WorkItemOut =>
  ({ id: nextId++, status, kind, stage }) as unknown as WorkItemOut;

const keys = (groups: { key: WorkItemStatus }[]) => groups.map((g) => g.key);

describe('matchesKorbFilter', () => {
  it('lets every row through under „alle"', () => {
    for (const status of ['open', 'ack', 'done', 'returned'] as const) {
      expect(matchesKorbFilter(row(status, 'note'), KORB_FILTER_ALL)).toBe(true);
    }
    expect(isKorbFilterAll(KORB_FILTER_ALL)).toBe(true);
  });

  it('selects exactly one status', () => {
    const filter = { ...KORB_FILTER_ALL, status: 'returned' as const };
    expect(matchesKorbFilter(row('returned'), filter)).toBe(true);
    expect(matchesKorbFilter(row('open'), filter)).toBe(false);
    expect(isKorbFilterAll(filter)).toBe(false);
  });

  it('keeps the levels apart — a Landmarke is not a Buchstabe', () => {
    // Both carry `glyph_key`, so only `kind` tells them apart.
    const filter = { ...KORB_FILTER_ALL, kind: 'landmark' as const };
    expect(matchesKorbFilter(row('open', 'landmark'), filter)).toBe(true);
    expect(matchesKorbFilter(row('open', 'letter'), filter)).toBe(false);
  });

  it('never matches a row without a Stufe', () => {
    const filter = { ...KORB_FILTER_ALL, stage: 'laufform' as const };
    expect(matchesKorbFilter(row('done', 'letter', 'laufform'), filter)).toBe(true);
    // The whole live queue looks like this: filed, not yet closed, no stage.
    expect(matchesKorbFilter(row('open'), filter)).toBe(false);
    expect(matchesKorbFilter(row('ack'), filter)).toBe(false);
  });

  it('ANDs the three selects', () => {
    const filter = { status: 'done' as const, kind: 'word' as const, stage: 'word_trace' as const };
    expect(matchesKorbFilter(row('done', 'word', 'word_trace'), filter)).toBe(true);
    expect(matchesKorbFilter(row('done', 'word', 'composition'), filter)).toBe(false);
    expect(matchesKorbFilter(row('done', 'letter', 'word_trace'), filter)).toBe(false);
    expect(matchesKorbFilter(row('returned', 'word', 'word_trace'), filter)).toBe(false);
  });
});

describe('groupKorb', () => {
  it('opens on every row, handed-back ones on top', () => {
    const rows = [row('done'), row('open'), row('ack'), row('returned')];
    expect(keys(groupKorb(rows, KORB_FILTER_ALL, true))).toEqual(['returned', 'open', 'ack', 'done']);
  });

  it('keeps the order when a filter empties the leading groups', () => {
    const rows = [row('open', 'letter'), row('returned', 'letter'), row('ack', 'note'), row('done', 'note')];
    expect(keys(groupKorb(rows, { ...KORB_FILTER_ALL, kind: 'note' }, true))).toEqual(['ack', 'done']);
  });

  it('hides the archive behind „erledigte anzeigen"', () => {
    const rows = [row('open'), row('done')];
    expect(keys(groupKorb(rows, KORB_FILTER_ALL, false))).toEqual(['open']);
    expect(korbArchiveVisible(KORB_FILTER_ALL, false)).toBe(false);
  });

  it('lets the status filter „Erledigt" win over that switch', () => {
    const rows = [row('open'), row('done')];
    const filter = { ...KORB_FILTER_ALL, status: 'done' as const };
    expect(keys(groupKorb(rows, filter, false))).toEqual(['done']);
    expect(korbArchiveVisible(filter, false)).toBe(true);
  });

  it('reports nothing rather than an empty group', () => {
    expect(groupKorb([row('open')], { ...KORB_FILTER_ALL, stage: 'join_rule' }, true)).toEqual([]);
  });

  it('leaves the server order inside a group alone', () => {
    const first = row('open');
    const second = row('open');
    expect(groupKorb([first, second], KORB_FILTER_ALL, false)[0].rows.map((r) => r.id)).toEqual([first.id, second.id]);
  });
});
