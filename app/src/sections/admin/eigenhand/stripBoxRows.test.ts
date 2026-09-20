import { describe, expect, it } from 'vitest';

import type { EigenhandPfadBox, EigenhandPfadFassung, EigenhandTintentreue } from '@/lib/api';

import {
  BOX_STATUSES,
  boxFilterCounts,
  buildStripBoxRows,
  matchesBoxFilter,
  matchesStripBoxFilters,
  missingKeysOf,
  severityOf,
  sortStripBoxRows,
  stripBoxTally,
  stripBoxesRankable,
  type StripBoxRow,
} from './stripBoxRows';

const urteil = (over: Partial<EigenhandTintentreue> = {}): EigenhandTintentreue => ({
  stufe: 'nicht beurteilt',
  grund: 'kein Eintrag',
  gemessen: false,
  sensor: null,
  sensoren: [],
  format: 1,
  schwellen_stand: '2026-09-20',
  vorlaeufig: true,
  ...over,
});

const box = (index: number, over: Partial<EigenhandPfadBox> = {}): EigenhandPfadBox => ({
  box_index: index,
  word: `wort${index}`,
  absetzer_soll: 2,
  status: null,
  grund: null,
  detail: null,
  verfahren: null,
  erzeugt_am: null,
  flecken_n: null,
  stale: false,
  offen: true,
  tintentreue: urteil(),
  ...over,
});

const fassung = (strip: string, kaesten: EigenhandPfadBox[], over: Partial<EigenhandPfadFassung> = {}): EigenhandPfadFassung => ({
  strip,
  fassung: 'F02',
  sheet: 'B0001',
  row_index: 0,
  format: 2,
  gefolgt: true,
  zaehler: { kaesten: kaesten.length, gemessen: 0, folgt: 0, von_hand: 0 },
  kaesten,
  ...over,
});

/** A followed box on one of the three measured steps. */
const followed = (index: number, stufe: EigenhandTintentreue['stufe'], over: Partial<EigenhandPfadBox> = {}) =>
  box(index, {
    verfahren: 'tintenpfad',
    erzeugt_am: '2026-09-20',
    offen: stufe !== 'folgt',
    tintentreue: urteil({ stufe, grund: 'Absetzer (Bahn)', gemessen: true, sensor: 'Absetzer (Bahn)', format: 2 }),
    ...over,
  });

const rowsOf = (fassungen: EigenhandPfadFassung[], korbByBox: Map<string, number> | null = null): StripBoxRow[] =>
  buildStripBoxRows({ fassungen, korbByBox });

describe('one row per word box', () => {
  it('keys a row by its box address and keeps the read’s plan order', () => {
    const rows = rowsOf([
      fassung('S0041', [box(0), box(1)]),
      fassung('S0042', [box(0)], { fassung: 'F01' }),
    ]);
    expect(rows.map((row) => row.key)).toEqual(['S0041/F02#0', 'S0041/F02#1', 'S0042/F01#0']);
    // The key is exactly what `work_items.specimen_id` carries for a box (V7),
    // so the Korb count and the row cannot disagree about which box is meant.
    expect(rows[1].strip).toBe('S0041');
    expect(rows[1].boxIndex).toBe(1);
  });

  it('carries the FASSUNG’s stored format and its gefolgt state onto every row', () => {
    const rows = rowsOf([fassung('S0041', [box(0)], { format: 1, gefolgt: false })]);
    expect(rows[0].format).toBe(1);
    expect(rows[0].gefolgt).toBe(false);
  });

  it('leaves the basket count null while the admin-gated read has not answered', () => {
    expect(rowsOf([fassung('S0041', [box(0)])])[0].korbOpen).toBeNull();
    const counted = rowsOf([fassung('S0041', [box(0)])], new Map([['S0041/F02#0', 2]]));
    expect(counted[0].korbOpen).toBe(2);
    // The read answered and this box is clean — 0, not „unbekannt".
    expect(rowsOf([fassung('S0041', [box(1)])], new Map())[0].korbOpen).toBe(0);
  });
});

describe('die Schwere', () => {
  it('ranks a red box first and the follower’s empty hand right behind it', () => {
    const rows = rowsOf([
      fassung('S0041', [
        followed(0, 'folgt'),
        box(1, { status: 'skipped', grund: 'gave_up', verfahren: 'tintenpfad' }),
        followed(2, 'folgt nicht'),
        followed(3, 'folgt teils'),
      ]),
    ]);
    expect(sortStripBoxRows(rows).map((row) => row.severity)).toEqual([
      'rot',
      'nichts-gefunden',
      'gelb',
      'gruen',
    ]);
  });

  it('greys a skip that is somebody else’s step, and finds nothing only where the follower gave up', () => {
    // „unautoriert" is a Tafel gap and „keine Bogen-Geometrie" is a Bogen
    // nobody can re-cut — neither is the follower coming back empty-handed.
    expect(severityOf(box(0, { status: 'skipped', grund: 'unauthored', detail: 'sz ch' }))).toBe('grau');
    expect(severityOf(box(0, { status: 'skipped', grund: 'no_geometry' }))).toBe('grau');
    expect(severityOf(box(0, { status: 'skipped', grund: 'gave_up' }))).toBe('nichts-gefunden');
  });

  it('never reads a box with no entry as a finding, whatever the Fassung did', () => {
    // `--box` narrows a RUN and says nothing about the boxes it left alone
    // (`follow_row` writes no „not selected" on purpose), so the untouched
    // siblings of the first per-box run must not climb over real findings.
    const rows = rowsOf([fassung('S0041', [box(0), followed(1, 'folgt nicht')], { gefolgt: true })]);
    expect(rows.map((row) => row.severity)).toEqual(['grau', 'rot']);
    // It stays BELOW the measured findings — the step it was promoted over.
    expect(sortStripBoxRows(rows).map((row) => row.word)).toEqual(['wort1', 'wort0']);
    // The same box in a Fassung nobody has followed says exactly the same.
    expect(severityOf(box(0))).toBe('grau');
  });

  it('puts the author’s own line under „erledigt", never under a measured step', () => {
    // Read off `offen`, which the server computes — not off the German reason
    // sentence: „not open and not green" IS the hand-drawn, unmeasured box.
    const own = box(0, { verfahren: 'authored', offen: false, tintentreue: urteil({ grund: 'von Hand gezeichnet' }) });
    expect(severityOf(own)).toBe('von-hand');
    // And a hand-drawn Bahn the tool HAS measured and found wanting is a
    // finding like any other (V21) — it stays open and red.
    const measured = box(0, {
      verfahren: 'authored',
      offen: true,
      tintentreue: urteil({ stufe: 'folgt nicht', grund: 'AIoU', gemessen: true, format: 2 }),
    });
    expect(severityOf(measured)).toBe('rot');
  });

  it('keeps the plan order inside one step, so equal rows never swap places', () => {
    const rows = rowsOf([
      fassung('S0041', [followed(0, 'folgt nicht'), followed(1, 'folgt nicht')]),
      fassung('S0040', [followed(0, 'folgt nicht')], { fassung: 'F01' }),
    ]);
    expect(sortStripBoxRows(rows).map((row) => row.key)).toEqual(['S0041/F02#0', 'S0041/F02#1', 'S0040/F01#0']);
  });

  it('says so instead of ranking when not one box has been measured', () => {
    const grey = rowsOf([fassung('S0041', [box(0), box(1)])]);
    expect(stripBoxesRankable(grey)).toBe(false);
    expect(stripBoxesRankable(rowsOf([fassung('S0041', [followed(0, 'folgt')])]))).toBe(true);
  });
});

describe('the three selecting axes', () => {
  const rows = rowsOf([
    fassung('S0041', [
      followed(0, 'folgt nicht', { word: 'kann' }),
      followed(1, 'folgt', { word: 'lesen', offen: false, stale: true }),
      box(2, {
        word: 'sechs',
        status: 'skipped',
        grund: 'unauthored',
        detail: 'sz ch',
        verfahren: 'tintenpfad',
      }),
      box(3, {
        word: 'kannte',
        verfahren: 'authored',
        offen: false,
        tintentreue: urteil({ grund: 'von Hand gezeichnet' }),
      }),
    ]),
  ]);

  it('answers the Nachfahren status', () => {
    const words = (status: (typeof BOX_STATUSES)[number]) =>
      rows.filter((row) => matchesStripBoxFilters(row, [], status, '')).map((row) => row.word);
    expect(words('alle')).toEqual(['kann', 'lesen', 'sechs', 'kannte']);
    expect(words('noetig')).toEqual(['kann', 'sechs']);
    expect(words('erledigt')).toEqual(['lesen', 'kannte']);
    // „Ohne Bahn" is the two ways a box can carry none — no entry, or an entry
    // that says outright there is none.
    expect(words('ohne-bahn')).toEqual(['sechs']);
  });

  it('ANDs the chips and counts each of them on its own', () => {
    expect(rows.filter((row) => matchesBoxFilter(row, 'maske-geaendert')).map((r) => r.word)).toEqual(['lesen']);
    expect(rows.filter((row) => matchesBoxFilter(row, 'tafel-fehlt')).map((r) => r.word)).toEqual(['sechs']);
    expect(rows.filter((row) => matchesBoxFilter(row, 'von-hand')).map((r) => r.word)).toEqual(['kannte']);
    expect(boxFilterCounts(rows)).toEqual({
      'maske-geaendert': 1,
      'tafel-fehlt': 1,
      uebersprungen: 1,
      'von-hand': 1,
    });
    // Two chips ticked select what holds BOTH — here nothing.
    expect(rows.filter((row) => matchesStripBoxFilters(row, ['von-hand', 'tafel-fehlt'], 'alle', ''))).toEqual([]);
  });

  it('matches the word and nothing else with the search needle', () => {
    expect(rows.filter((row) => matchesStripBoxFilters(row, [], 'alle', 'kann')).map((r) => r.word)).toEqual([
      'kann',
      'kannte',
    ]);
    // The strip id is shown so a row can be named at the terminal — it is not
    // searchable, or „S00" would select a third of the plan.
    expect(rows.filter((row) => matchesStripBoxFilters(row, [], 'alle', 'S0041'))).toEqual([]);
  });
});

describe('the Tafel gap a skip names', () => {
  it('reads the missing glyph keys out of an unauthored skip only', () => {
    expect(missingKeysOf(box(0, { status: 'skipped', grund: 'unauthored', detail: 'sz  ch' }))).toEqual(['sz', 'ch']);
    // Every other `detail` is a free line from the follower, not a key list.
    expect(missingKeysOf(box(0, { status: 'skipped', grund: 'gave_up', detail: 'no_ink: nothing found' }))).toEqual([]);
    expect(missingKeysOf(box(0, { status: 'skipped', grund: 'unauthored', detail: null }))).toEqual([]);
  });
});

describe('the counter of the whole list', () => {
  it('counts over every row, never over the ones a filter left standing', () => {
    const rows = rowsOf([
      fassung('S0041', [
        followed(0, 'folgt'),
        followed(1, 'folgt nicht'),
        box(2, { verfahren: 'authored', offen: false, tintentreue: urteil({ grund: 'von Hand gezeichnet' }) }),
      ]),
    ]);
    expect(stripBoxTally(rows)).toEqual({ kaesten: 3, folgt: 1, vonHand: 1, offen: 1 });
  });

  it('counts „von Hand" in the tally as UNMEASURED, where the chip counts provenance', () => {
    // An authored Bahn the tool has since measured keeps its Herkunft — so the
    // chip holds it and the tally does not. The label says „(ungemessen)"
    // rather than letting the two numbers look like a contradiction (V21).
    const rows = rowsOf([
      fassung('S0041', [
        box(0, { verfahren: 'authored', offen: false, tintentreue: urteil({ grund: 'von Hand gezeichnet' }) }),
        followed(1, 'folgt', { verfahren: 'authored' }),
      ]),
    ]);
    expect(boxFilterCounts(rows)['von-hand']).toBe(2);
    expect(stripBoxTally(rows).vonHand).toBe(1);
  });
});
