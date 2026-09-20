import { describe, expect, it } from 'vitest';

import type { WorkItemKind, WorkItemOut, WorkItemStatus } from '@/lib/api';

import { korbCountsOf, pairCountKey } from './korbTargets';

let nextId = 1;
function item(kind: WorkItemKind, status: WorkItemStatus, fields: Partial<WorkItemOut> = {}): WorkItemOut {
  return {
    id: nextId++,
    source_id: 'suetterlin-1922',
    kind,
    glyph_key: null,
    left_key: null,
    right_key: null,
    word: null,
    specimen_kind: null,
    specimen_id: null,
    note: 'n',
    status,
    understanding: null,
    reproduced: null,
    stage: null,
    resolution: null,
    acked_at: null,
    closed_at: null,
    created_at: null,
    updated_at: null,
    ...fields,
  };
}

describe('korb counts per subject', () => {
  it('counts open and handed-back rows, and neither the acknowledged nor the archived ones', () => {
    const counts = korbCountsOf([
      item('letter', 'open', { glyph_key: 'a' }),
      item('letter', 'returned', { glyph_key: 'a' }),
      item('letter', 'ack', { glyph_key: 'a' }),
      item('letter', 'done', { glyph_key: 'a' }),
    ]);
    expect(counts?.byGlyph.get('a')).toBe(2);
  });

  it('counts a landmark on its letter — the lens lives in that view', () => {
    const counts = korbCountsOf([item('landmark', 'open', { glyph_key: 'n' })]);
    expect(counts?.byGlyph.get('n')).toBe(1);
  });

  it('ignores a general note: it points at no subject a list could key on', () => {
    const counts = korbCountsOf([item('note', 'open'), item('note', 'returned')]);
    expect(counts?.byGlyph.size).toBe(0);
    expect(counts?.byPair.size).toBe(0);
    expect(counts?.byWord.size).toBe(0);
  });

  it('keys a join by its ordered pair and a word by its text', () => {
    const counts = korbCountsOf([
      item('pair', 'open', { left_key: 'a', right_key: 'b' }),
      item('word', 'open', { word: 'lesen' }),
    ]);
    expect(counts?.byPair.get(pairCountKey('a', 'b'))).toBe(1);
    expect(counts?.byWord.get('lesen')).toBe(1);
  });

  it('counts a written word box on the BOX, never on the plate’s word of the same text', () => {
    // A box row is an Eigenhand task (V7); counting it on `byWord` would put it
    // on the Vorlage's Wortprobe „kann" in the Wörter overview.
    const counts = korbCountsOf([
      item('word', 'open', { word: 'kann', specimen_kind: 'strip', specimen_id: 'S0041/F02#2' }),
      item('word', 'returned', { word: 'kann', specimen_kind: 'strip', specimen_id: 'S0041/F02#2' }),
      item('word', 'open', { word: 'kann', specimen_kind: 'word', specimen_id: 'kann' }),
    ]);
    expect(counts?.byStripBox.get('S0041/F02#2')).toBe(2);
    expect(counts?.byWord.get('kann')).toBe(1);
  });

  it('skips a row whose target is only half given', () => {
    const counts = korbCountsOf([
      item('pair', 'open', { left_key: 'a' }),
      item('letter', 'open'),
      // Filed by specimen id alone — there is no word text to count it on.
      item('word', 'open', { specimen_id: 'abb19-3' }),
    ]);
    expect(counts?.byPair.size).toBe(0);
    expect(counts?.byGlyph.size).toBe(0);
    expect(counts?.byWord.size).toBe(0);
  });

  it('stays null while the basket read has not answered', () => {
    // An admin-gated read that 401'd is „unbekannt", never „keine Aufträge" —
    // the chip must be able to say nothing at all.
    expect(korbCountsOf(null)).toBeNull();
  });
});
