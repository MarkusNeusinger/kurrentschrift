import { describe, expect, it } from 'vitest';

import type { EigenhandPfadBox, EigenhandPfadFassung, EigenhandTintentreue } from '@/lib/api';

import { exactLink, listenLinkUrl, tintentreueVerteilung, VERTEILUNG_STUFEN } from './tintentreueVerteilung';
import { buildStripBoxRows } from './stripBoxRows';

const urteil = (over: Partial<EigenhandTintentreue> = {}): EigenhandTintentreue => ({
  stufe: 'nicht beurteilt',
  grund: 'kein Eintrag',
  gemessen: false,
  sensor: null,
  sensoren: [],
  format: 2,
  schwellen_stand: '2026-09-20',
  vorlaeufig: true,
  ...over,
});

const box = (index: number, over: Partial<EigenhandPfadBox> = {}): EigenhandPfadBox => ({
  box_index: index,
  word: `wort${index}`,
  absetzer_soll: 1,
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

const measured = (index: number, stufe: EigenhandTintentreue['stufe'], sensor: string) =>
  box(index, {
    verfahren: 'tintenpfad',
    offen: stufe !== 'folgt',
    tintentreue: urteil({ stufe, grund: sensor, gemessen: true, sensor }),
  });

const skipped = (index: number, grund: EigenhandPfadBox['grund'], wort: string) =>
  box(index, {
    status: 'skipped',
    grund,
    verfahren: 'tintenpfad',
    tintentreue: urteil({ grund: `übersprungen: ${wort}` }),
  });

const fassung = (strip: string, kaesten: EigenhandPfadBox[], over: Partial<EigenhandPfadFassung> = {}): EigenhandPfadFassung => ({
  strip,
  fassung: 'F01',
  sheet: 'B0001',
  row_index: 0,
  format: 2,
  gefolgt: true,
  zaehler: { kaesten: kaesten.length, gemessen: 0, folgt: 0, von_hand: 0 },
  kaesten,
  ...over,
});

const HAND = [
  fassung('S0001', [
    measured(0, 'folgt', 'nichts fällt auf'),
    measured(1, 'folgt nicht', 'Absetzer (Bahn)'),
    measured(2, 'folgt teils', 'AIoU'),
    skipped(3, 'unauthored', 'unautoriert'),
  ]),
  fassung('S0002', [
    measured(0, 'folgt nicht', 'AIoU'),
    measured(1, 'folgt nicht', 'Absetzer (Bahn)'),
    box(2),
    box(3, { tintentreue: urteil({ grund: 'Format 1 — unvollständig gemessen', format: 1 }) }),
    box(4, { tintentreue: urteil({ grund: 'Format 1 — unvollständig gemessen', format: 1 }) }),
  ]),
];

const zeile = (verteilung: ReturnType<typeof tintentreueVerteilung>, stufe: string) =>
  verteilung.stufen.find((entry) => entry.stufe === stufe)!;

describe('the hand-wide Tintentreue distribution', () => {
  it('counts every box once, in the four states and their fixed order', () => {
    const verteilung = tintentreueVerteilung(HAND);
    expect(verteilung.kaesten).toBe(9);
    expect(verteilung.fassungen).toBe(2);
    expect(verteilung.stufen.map((entry) => entry.stufe)).toEqual(VERTEILUNG_STUFEN);
    expect(verteilung.stufen.map((entry) => entry.count)).toEqual([1, 1, 3, 4]);
    // „beurteilt" is the three measured steps and never the grey state.
    expect(verteilung.gemessen).toBe(5);
    // The counts add up to the box total: nothing is dropped or counted twice.
    expect(verteilung.stufen.reduce((sum, entry) => sum + entry.count, 0)).toBe(verteilung.kaesten);
  });

  it('groups the grey state by its reason, most frequent first, ties in the order met', () => {
    const grau = zeile(tintentreueVerteilung(HAND), 'nicht beurteilt');
    expect(grau.gruende.map((g) => [g.name, g.count])).toEqual([
      ['Format 1 — unvollständig gemessen', 2],
      ['übersprungen: unautoriert', 1],
      ['kein Eintrag', 1],
    ]);
  });

  it('groups a measured step by the sensor that named it', () => {
    const rot = zeile(tintentreueVerteilung(HAND), 'folgt nicht');
    expect(rot.gruende.map((g) => [g.name, g.count])).toEqual([
      ['Absetzer (Bahn)', 2],
      ['AIoU', 1],
    ]);
    expect(rot.keys).toEqual(['S0001/F01#1', 'S0002/F01#0', 'S0002/F01#1']);
  });

  it('counts per Fassung without giving a Fassung a verdict of its own', () => {
    const { proFassung } = tintentreueVerteilung(HAND);
    expect(proFassung).toEqual([
      {
        strip: 'S0001',
        fassung: 'F01',
        kaesten: 4,
        stufen: { folgt: 1, 'folgt teils': 1, 'folgt nicht': 1, 'nicht beurteilt': 1 },
      },
      {
        strip: 'S0002',
        fassung: 'F01',
        kaesten: 5,
        stufen: { folgt: 0, 'folgt teils': 0, 'folgt nicht': 2, 'nicht beurteilt': 3 },
      },
    ]);
  });

  it('says „vorläufig" while any box was graded under borrowed bounds, and keeps every date', () => {
    expect(tintentreueVerteilung(HAND).vorlaeufig).toBe(true);
    expect(tintentreueVerteilung(HAND).schwellenStaende).toEqual(['2026-09-20']);
    const calibrated = [
      fassung('S0001', [
        box(0, { tintentreue: urteil({ vorlaeufig: false, schwellen_stand: '2026-10-01' }) }),
        box(1, { tintentreue: urteil({ vorlaeufig: false, schwellen_stand: '2026-10-02' }) }),
      ]),
    ];
    expect(tintentreueVerteilung(calibrated).vorlaeufig).toBe(false);
    expect(tintentreueVerteilung(calibrated).schwellenStaende).toEqual(['2026-10-01', '2026-10-02']);
  });

  it('has nothing to say about thresholds for a hand without boxes', () => {
    const empty = tintentreueVerteilung([]);
    expect(empty.kaesten).toBe(0);
    expect(empty.vorlaeufig).toBeNull();
    expect(empty.stufen.every((entry) => entry.count === 0 && entry.link === null)).toBe(true);
  });
});

describe('links into the Nachfahr-Liste', () => {
  it('links a count only where a list axis selects exactly its boxes', () => {
    const verteilung = tintentreueVerteilung(HAND);
    const grau = zeile(verteilung, 'nicht beurteilt');
    // `unauthored` is exactly the „Tafel fehlt" chip — and here also exactly
    // „übersprungen"; the chip, as the more specific axis, wins.
    expect(grau.gruende.find((g) => g.name === 'übersprungen: unautoriert')?.link).toEqual({ filter: 'tafel-fehlt' });
    // The list has no axis per step, so a red count gets no link rather than
    // a superset behind its number.
    expect(zeile(verteilung, 'folgt nicht').link).toBeNull();
    expect(zeile(verteilung, 'folgt teils').link).toBeNull();
    // „folgt" is exactly „Erledigt" while no hand-drawn Bahn waits unmeasured.
    expect(zeile(verteilung, 'folgt').link).toEqual({ status: 'erledigt' });
  });

  it('drops the link the moment the axis selects one box more', () => {
    const withHandDrawn = [
      ...HAND,
      fassung('S0003', [
        box(0, { verfahren: 'authored', offen: false, tintentreue: urteil({ grund: 'von Hand gezeichnet' }) }),
      ]),
    ];
    const verteilung = tintentreueVerteilung(withHandDrawn);
    expect(zeile(verteilung, 'folgt').link).toBeNull();
    // The unmeasured hand-drawn box is itself exactly the „von Hand" chip.
    expect(zeile(verteilung, 'nicht beurteilt').gruende.find((g) => g.name === 'von Hand gezeichnet')?.link).toEqual({
      filter: 'von-hand',
    });
  });

  it('never links an empty count, although an empty axis selects the same empty set', () => {
    const rows = buildStripBoxRows({ fassungen: HAND, korbByBox: null });
    expect(exactLink(rows, [])).toBeNull();
  });

  it('builds the address the list reads back, in its default list mode', () => {
    expect(listenLinkUrl({ filter: 'tafel-fehlt' })).toBe('/admin/eigenhand?reiter=streifen&filter=tafel-fehlt');
    expect(listenLinkUrl({ status: 'erledigt' })).toBe('/admin/eigenhand?reiter=streifen&status=erledigt');
  });
});
