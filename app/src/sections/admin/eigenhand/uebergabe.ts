// A due local step, ready to be shown — server rule → German card.
//
// The split this module lives on: the RULE and the COMMAND are decided once,
// server-side (`core/eigenhand/faellig.py`), because the terminal twin
// `tools.eigenhand.report --faellig` has to print the same list; the German
// copy lives in the locale, keyed by the rule id. So an id the server emits
// and this bundle does not know yields `null` — no card at all, never an empty
// one under a headline (the defensive posture of `pfadRohzahlen.ts`).
//
// Pure on purpose: everything here is testable without rendering a panel.

import type { EigenhandFaellig } from '@/lib/api';
import { de, fmt } from '@/locales/admin';

export type Uebergabe = {
  id: string;
  titel: string;
  warum: string;
  /** The command as it has to be typed — built server-side, or here for `bahn_folgen`. */
  befehl: string;
  /** „Danach hier: …" — what changes on this page once the step has run. */
  danach: string;
  /** The order hint, where one step must not be taken before another. */
  reihenfolge: string;
  /** What the command alone would not say — today: the further open Bögen. */
  hinweis?: string;
};

type Copy = { titel: string; warum: string; danach: string; reihenfolge: string };

// `Partial` rather than the literal's own shape: an unknown id has to come back
// `undefined` here, which is the whole point of the lookup.
const KARTEN: Partial<Record<string, Copy>> = de.admin.eigenhand.uebergabe.karten;

/**
 * The rule ids the SERVER can emit, in chain order — hand-synced with
 * `RULE_IDS` in `core/eigenhand/faellig.py`, the way the wire types are
 * hand-synced with `api/schemas.py`. `bahn_folgen` is deliberately not in here:
 * it is built in the browser (see `bahnKarte`), because Phase 1 has no read
 * that says hand-wide which Fassung carries a Bahn.
 */
export const FAELLIG_IDS = ['setup_pull', 'universe_push', 'bogen_pull', 'sync_streifen'] as const;

/** The card for one due step the server reported, or `null` for an id we have no copy for. */
export function uebergabeKarte(row: EigenhandFaellig): Uebergabe | null {
  const copy = KARTEN[row.id];
  if (!copy) return null;
  const params = row.params ?? {};
  // Every field goes through `fmt`, not just the title: which one carries a
  // `{{…}}` is the locale's business, and a placeholder added to `warum` later
  // would otherwise ship literally with nothing failing.
  return {
    id: row.id,
    titel: fmt(copy.titel, params),
    warum: fmt(copy.warum, params),
    befehl: row.befehl,
    danach: fmt(copy.danach, params),
    reihenfolge: fmt(copy.reihenfolge, params),
    // Only the server can know there is more than one open Bogen; the command
    // on the card holds exactly one.
    hinweis: Number(params.weitere) > 0 ? fmt(de.admin.eigenhand.uebergabe.weitereBoegen, params) : undefined,
  };
}

/** Every due step the server reported that this bundle can spell out, in its order. */
export function uebergabeKarten(rows: readonly EigenhandFaellig[]): Uebergabe[] {
  return rows.map(uebergabeKarte).filter((karte): karte is Uebergabe => karte !== null);
}

/**
 * „Follow this Fassung's Bahn" — the one card the browser builds itself.
 *
 * The command is the DRY RUN. Pushing what was written up is the point of the
 * chain, so a card may hand over a write — what it never hands over is one that
 * REPLACES what is there, and `pfad --apply` overwrites followed geometry.
 * `--apply` is named in the order hint instead, behind the snapshot that
 * belongs in front of it (Q9). The other command of that kind,
 * `universe --push`, carries the snapshot in its own order hint.
 */
export function bahnKarte(hand: string, strip: string, fassung: string): Uebergabe {
  const t = de.admin.eigenhand.uebergabe;
  const copy = t.karten.bahn_folgen;
  return {
    id: 'bahn_folgen',
    titel: copy.titel,
    warum: copy.warum,
    befehl: fmt(t.bahnBefehl, { hand, strip, fassung }),
    danach: copy.danach,
    reihenfolge: copy.reihenfolge,
  };
}

/** The terminal twin, for the line under the block: the same list, printed at the machine. */
export function rechnerBefehl(hand: string): string {
  return fmt(de.admin.eigenhand.uebergabe.rechnerBefehl, { hand });
}
