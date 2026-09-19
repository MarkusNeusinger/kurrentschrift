// The seam between a server rule and a German card.
//
// Two halves that can rot independently: the server may learn a rule this
// bundle has no copy for (a deploy ahead of the SPA), and the copy may outlive
// the rule that reached it. The first must produce NO card — never a headline
// over an empty box —, and the second is caught by the totality case below,
// which walks the ids `core/eigenhand/faellig.py` actually emits.

import { describe, expect, it } from 'vitest';

import type { EigenhandFaellig } from '@/lib/api';
import { FAELLIG_IDS, bahnKarte, rechnerBefehl, uebergabeKarte, uebergabeKarten } from './uebergabe';

const HAND = 'mn-suetterlin';

/** A row in the shape the bestand read delivers it. */
function row(id: string, params: Record<string, string | number> = {}): EigenhandFaellig {
  return { id, befehl: `uv run python -m tools.eigenhand.${id} --hand ${HAND}`, params: { hand: HAND, ...params } };
}

const PARAMS: Record<string, Record<string, string | number>> = {
  bogen_pull: { sheet: 'B0007', offen: 2 },
  sync_streifen: { ohne_bild: 4 },
};

describe('uebergabeKarte', () => {
  it('spells out every id the server can emit', () => {
    // The totality case: a rule without copy would render nothing at all, and
    // the author would be waiting for a card that silently never comes.
    for (const id of FAELLIG_IDS) {
      const karte = uebergabeKarte(row(id, PARAMS[id]));
      expect(karte, id).not.toBeNull();
      expect(karte?.titel, id).toBeTruthy();
      expect(karte?.warum, id).toBeTruthy();
      expect(karte?.danach, id).toBeTruthy();
      // No placeholder survives into the copy — an unfilled {{…}} on screen is
      // the failure this interpolation exists to avoid.
      expect(karte?.titel, id).not.toMatch(/\{\{/);
    }
  });

  it('interpolates the server parameters into the title', () => {
    expect(uebergabeKarte(row('bogen_pull', PARAMS.bogen_pull))?.titel).toContain('B0007');
    expect(uebergabeKarte(row('sync_streifen', PARAMS.sync_streifen))?.titel).toContain('4');
  });

  it('takes the command from the server rather than building one', () => {
    const served = row('universe_push');
    expect(uebergabeKarte(served)?.befehl).toBe(served.befehl);
  });

  it('yields null for an id it has no copy for — never a blank card', () => {
    expect(uebergabeKarte(row('schnappschuss_holen'))).toBeNull();
    expect(uebergabeKarte(row(''))).toBeNull();
  });

  it('keeps the servers order and drops only what it cannot spell out', () => {
    const karten = uebergabeKarten([row('universe_push'), row('was_auch_immer'), row('sync_streifen', PARAMS.sync_streifen)]);
    expect(karten.map((k) => k.id)).toEqual(['universe_push', 'sync_streifen']);
  });
});

describe('bahnKarte', () => {
  it('names the real strip and Fassung instead of „…"', () => {
    const karte = bahnKarte(HAND, 'S0042', 'F02');
    expect(karte.befehl).toContain('--strip S0042');
    expect(karte.befehl).toContain('--fassung F02');
    expect(karte.befehl).toContain(`--hand ${HAND}`);
  });

  it('copies the dry run — never the command that writes to the shared DB', () => {
    // P1-Q9: `--apply` is named in the order hint, behind the snapshot that
    // belongs in front of it, and never handed over by the copy button.
    const karte = bahnKarte(HAND, 'S0042', 'F02');
    expect(karte.befehl).not.toContain('--apply');
    expect(karte.reihenfolge).toContain('--apply');
  });

  it('is not one of the ids the server can emit', () => {
    expect(FAELLIG_IDS).not.toContain(bahnKarte(HAND, 'S0042', 'F02').id);
  });
});

describe('rechnerBefehl', () => {
  it('names the hand, so the twin prints this hands list', () => {
    expect(rechnerBefehl(HAND)).toBe(`uv run python -m tools.eigenhand.report --hand ${HAND} --faellig`);
  });
});
