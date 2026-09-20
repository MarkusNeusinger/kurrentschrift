// Die Nachfahr-Liste as ROWS — what one line of the work list knows about one
// written word BOX, which axes it answers to and how the list is ordered.
//
// The fourth row model beside `letters/letterRows.ts`, `pairs/pairRows.ts` and
// `words/wordRows.ts`, and the first whose subject is not a Vorlage's: the unit
// is the KASTEN, so one Fassung contributes up to five rows. That is the whole
// correction behind this surface — „der Filter ‚Nachfahren'" in the plan
// presumed a list that never existed, and a filter over Fassungen cannot say
// which WORD wants work (`admin-redesign.md` §7.2, corrected 2026-09-20).
//
// Pure and JSX-free like its three siblings: the ladder „Schwere" and the truth
// table of the axes are worth a unit test and worthless to read out of a
// component.
//
// NOTHING is derived from sensors here. The verdict per box — the Tintentreue,
// its naming sensor, its grey reason, and whether the box is still work — is
// computed on the server (`core/eigenhand/tintentreue.py`, projected by
// `GET /eigenhand/pfade/{hand}`) and only READ here. A second reading in the
// client would be a second rule with its own drift.

import type { EigenhandPfadBox, EigenhandPfadFassung } from '@/lib/api';
import { stripBoxSpecimen } from '@/sections/admin/shell/focus';
import type { ListSpec } from '@/sections/admin/shell/listState';

/** The chips, ANDed. Each names a NEXT STEP rather than a shade of the verdict:
 * a changed mask wants `pfad --apply`, a missing Tafel-Duktus wants the letter
 * view, a skipped box wants a look at why, and a hand-drawn Bahn is the
 * author's own line (§6.4 „Umgeleitet"). */
export const BOX_FILTERS = ['maske-geaendert', 'tafel-fehlt', 'uebersprungen', 'von-hand'] as const;
export type BoxFilter = (typeof BOX_FILTERS)[number];

/**
 * ONE order, and deliberately one: Q13 is a STAGED decision — Phase 2 gets „die
 * einfache Ordnung Schwere → Streifen", and the full order (Bahn-Deckung,
 * Übergangsraum-Gewicht) with the Streifenfolge as a switch beside it is Phase
 * 4. So the spec carries a single sort token and the toolbar shows no switch,
 * rather than shipping half of the Phase-4 surface early.
 */
export const BOX_SORTS = ['schwere'] as const;
export type BoxSort = (typeof BOX_SORTS)[number];

/** `status=` — the Nachfahren axis of §7.2, in German URL words. The first
 * entry is the default and therefore never appears in a link. */
export const BOX_STATUSES = ['alle', 'noetig', 'erledigt', 'ohne-bahn'] as const;
export type BoxStatus = (typeof BOX_STATUSES)[number];

/** No `tabs`: the Eigenhand page's `reiter=` belongs to the Unteransicht and is
 * written by `focus.ts`, so this spec must leave it standing (that is exactly
 * what the optional axes of `listState.ts` are for). */
export const STRIP_BOX_LIST_SPEC: ListSpec<BoxFilter, BoxSort, BoxStatus> = {
  filters: BOX_FILTERS,
  sorts: BOX_SORTS,
  defaultSort: 'schwere',
  statuses: BOX_STATUSES,
};

/**
 * The ladder „Schwere" — the first half of Q13's Phase-2 order, as RANKS rather
 * than as a score: a number that can be averaged is exactly what the Ampel
 * refuses to export (`tintentreue.py`, „keine Skalarzahl").
 *
 * The two top steps are the doctrine's own („Schwere: rot > Folger fand
 * nichts", §6.4); the three below them are decided here, as routine
 * engineering, and say what a reader can act on:
 *
 *   0 `rot`             — measured and bad: the Nachfahr-case the list is for.
 *   1 `nichts-gefunden` — the follower walked this box and came back with no
 *                         Bahn (`gave_up`, or no entry although the Fassung was
 *                         followed). Not measured, but certainly missing.
 *   2 `grau`            — a state that keeps the box open without judging it:
 *                         never followed, mask changed, format 1, unmeasured —
 *                         and the other skips, which are somebody else's step
 *                         („unautoriert" belongs to the Tafel, „keine
 *                         Bogen-Geometrie" to a Bogen nobody can re-cut).
 *   3 `gelb`            — measured and middling. Open per the server's rule,
 *                         but NOT re-traced (Q12 b), so it stands below the
 *                         states that ask for a step.
 *   4 `von-hand`        — the author's own line, unmeasured by construction:
 *                         done.
 *   5 `gruen`           — measured and good: done.
 */
export const BOX_SEVERITIES = ['rot', 'nichts-gefunden', 'grau', 'gelb', 'von-hand', 'gruen'] as const;
export type BoxSeverity = (typeof BOX_SEVERITIES)[number];

/**
 * Two of the grey reasons `core/eigenhand/tintentreue.py` sends, as its own
 * words. Compared as strings the way `pfadHerkunft.ts` compares `verfahren`:
 * the STEP vocabulary is a closed `Literal` on the wire, the reasons are
 * sentences, and a reader that needs one of them says which.
 *
 * `maske` is needed by the row rather than by the model: the mask state is
 * shown beside the verdict, and where the verdict ALREADY says it (because
 * nothing greyer stands in front of it) a chip repeating it would be the very
 * doubling this PR removes from the strip caption.
 */
export const TINTENTREUE_GRUND = { vonHand: 'von Hand gezeichnet', maske: 'Maske geändert' } as const;
const GRUND_VON_HAND = TINTENTREUE_GRUND.vonHand;

export type StripBoxRow = {
  /** `S0041/F02#2` — the box address, the list's key AND `specimen_id` (V7). */
  key: string;
  strip: string;
  fassung: string;
  sheet: string;
  rowIndex: number;
  boxIndex: number;
  word: string;
  /** The FASSUNG's stored Streifen-Pfad format, not the constant this bundle
   * knows: under format 1 the box cannot carry a Skip-Eintrag, and the Ampel
   * greys for that reason rather than because nothing was measured. */
  format: number;
  /** False says nobody has followed this Fassung — a different silence from
   * „followed and this box got nothing". */
  gefolgt: boolean;
  /** Joined body runs the script writes this word in — no Markenzüge (the
   * server's `absetzer_soll`, `core.eigenhand.befund.body_runs_expected`). */
  absetzerSoll: number;
  /** The Skip-Eintrag, where the row carries one; `null` under format 1. */
  skipGrund: EigenhandPfadBox['grund'];
  skipDetail: string | null;
  /** Who made the entry, `null` where the box carries none at all. */
  verfahren: string | null;
  erzeugtAm: string | null;
  /** Followed under a Fleckenmaske of another size than the Fassung carries
   * today — „erst `pfad --apply`", and stated beside the verdict because the
   * verdict shows one grey state at a time. */
  stale: boolean;
  /** Still Nachfahr-work? The server's rule (`api/routers/eigenhand.py`). */
  offen: boolean;
  /** The verdict itself, passed through untouched for the row's chips. */
  tintentreue: EigenhandPfadBox['tintentreue'];
  severity: BoxSeverity;
  /** The glyph keys the Tafel still owes, for a skip that named them —
   * `unauthored` writes them into `detail` as a space-separated list. */
  missingKeys: string[];
  /** null = the basket read has not answered; 0 = it did and this box is clean. */
  korbOpen: number | null;
};

export type StripBoxRowInput = {
  /** The meta-only read's Fassungen, in its own order (strip, then Fassung). */
  fassungen: readonly EigenhandPfadFassung[];
  /** Open basket rows per box address; null while the read is unknown. */
  korbByBox: Map<string, number> | null;
};

/** Which of the six steps this box stands on. */
export function severityOf(box: EigenhandPfadBox, gefolgt: boolean): BoxSeverity {
  if (box.tintentreue.grund === GRUND_VON_HAND) return 'von-hand';
  if (box.status === 'skipped') return box.grund === 'gave_up' ? 'nichts-gefunden' : 'grau';
  // No entry at all in a Fassung the follower HAS walked: it produced nothing
  // for this box and, under format 1, could not say so.
  if (box.verfahren === null) return gefolgt ? 'nichts-gefunden' : 'grau';
  if (box.tintentreue.stufe === 'folgt nicht') return 'rot';
  if (box.tintentreue.stufe === 'folgt teils') return 'gelb';
  if (box.tintentreue.stufe === 'folgt') return 'gruen';
  return 'grau';
}

/** The keys a skip named as missing from the Tafel, or `[]` for every other
 * kind of entry. Guarded against a `detail` that is anything else: the column
 * is a short free line, and only `unauthored` promises this shape. */
export function missingKeysOf(box: EigenhandPfadBox): string[] {
  if (box.grund !== 'unauthored' || !box.detail) return [];
  return box.detail.split(/\s+/).filter(Boolean);
}

/** One row per word box of every Fassung, in the read's own (plan) order. */
export function buildStripBoxRows(input: StripBoxRowInput): StripBoxRow[] {
  const rows: StripBoxRow[] = [];
  for (const fassung of input.fassungen) {
    for (const box of fassung.kaesten) {
      const key = stripBoxSpecimen(fassung.strip, fassung.fassung, box.box_index);
      rows.push({
        key,
        strip: fassung.strip,
        fassung: fassung.fassung,
        sheet: fassung.sheet,
        rowIndex: fassung.row_index,
        boxIndex: box.box_index,
        word: box.word,
        format: fassung.format,
        gefolgt: fassung.gefolgt,
        absetzerSoll: box.absetzer_soll,
        skipGrund: box.status === 'skipped' ? box.grund : null,
        skipDetail: box.detail,
        verfahren: box.verfahren,
        erzeugtAm: box.erzeugt_am,
        stale: box.stale,
        offen: box.offen,
        tintentreue: box.tintentreue,
        severity: severityOf(box, fassung.gefolgt),
        missingKeys: missingKeysOf(box),
        korbOpen: input.korbByBox === null ? null : (input.korbByBox.get(key) ?? 0),
      });
    }
  }
  return rows;
}

/** Whether one row answers one chip. */
export function matchesBoxFilter(row: StripBoxRow, filter: BoxFilter): boolean {
  if (filter === 'maske-geaendert') return row.stale;
  if (filter === 'tafel-fehlt') return row.skipGrund === 'unauthored';
  if (filter === 'uebersprungen') return row.skipGrund !== null;
  return row.verfahren === 'authored';
}

/** Whether one row answers the single-choice Nachfahren axis. „Ohne Bahn" is
 * the two ways a box can carry none: no entry at all, or an entry that says
 * outright there is no path (author decision C). */
export function matchesBoxStatus(row: StripBoxRow, status: BoxStatus | null): boolean {
  if (status === 'noetig') return row.offen;
  if (status === 'erledigt') return !row.offen;
  if (status === 'ohne-bahn') return row.verfahren === null || row.skipGrund !== null;
  return true;
}

/**
 * The three selecting axes ANDed — the chips, the status and the word search
 * the strip surface already carried. The needle matches the WORD and nothing
 * else: the strip and Fassung ids are shown so a row can be named at the
 * terminal, but „S00" would otherwise select a third of the plan.
 */
export function matchesStripBoxFilters(
  row: StripBoxRow,
  filters: readonly BoxFilter[],
  status: BoxStatus | null,
  wort: string,
): boolean {
  if (!matchesBoxStatus(row, status)) return false;
  const needle = wort.trim().toLowerCase();
  if (needle && !row.word.toLowerCase().includes(needle)) return false;
  return filters.every((filter) => matchesBoxFilter(row, filter));
}

/**
 * How many rows EACH chip would select on its own — the number on the chip,
 * deliberately not „how many would remain beside the other ticked chips"
 * (`letterRows.ts` states the rule). No `null` here, unlike the letters: every
 * fact a chip rests on comes from the ONE read the list is built from, so a
 * chip either has its rows or the list has none at all.
 */
export function boxFilterCounts(rows: readonly StripBoxRow[]): Record<BoxFilter, number> {
  const counts = {} as Record<BoxFilter, number>;
  for (const filter of BOX_FILTERS) {
    counts[filter] = rows.filter((row) => matchesBoxFilter(row, filter)).length;
  }
  return counts;
}

const SEVERITY_RANK: Record<BoxSeverity, number> = BOX_SEVERITIES.reduce(
  (out, name, index) => ({ ...out, [name]: index }),
  {} as Record<BoxSeverity, number>,
);

/**
 * „Schwere → Streifen" (Q13, Phase 2 = b): the worst step first, and inside one
 * step the plan's own order — strip, Fassung, box. The tiebreak is the READ's
 * order rather than a second comparison, so two boxes that say the same thing
 * never swap places between two renders.
 */
export function sortStripBoxRows(rows: readonly StripBoxRow[]): StripBoxRow[] {
  return rows
    .map((row, index) => ({ row, index }))
    .sort((a, b) => SEVERITY_RANK[a.row.severity] - SEVERITY_RANK[b.row.severity] || a.index - b.index)
    .map((entry) => entry.row);
}

/**
 * Is there anything the Schwere actually ranks? Without a single MEASURED box
 * every row sits on „grau" and the order is silently the plan order again —
 * which is the state of the whole Bestand until a Fassung is followed under
 * Streifen-Pfad format 2. The toolbar says so instead of implying a ranking.
 */
export const stripBoxesRankable = (rows: readonly StripBoxRow[]): boolean =>
  rows.some((row) => row.tintentreue.gemessen);

/** „3 von 4 Kästen folgen" over the WHOLE list — a Fassung gets a counter and
 * never a colour (author decision E), and the list answers the same way: the
 * counter is taken over every row, never over the ones a filter left standing.
 */
export function stripBoxTally(rows: readonly StripBoxRow[]): {
  kaesten: number;
  folgt: number;
  vonHand: number;
  offen: number;
} {
  return {
    kaesten: rows.length,
    folgt: rows.filter((row) => row.severity === 'gruen').length,
    vonHand: rows.filter((row) => row.severity === 'von-hand').length,
    offen: rows.filter((row) => row.offen).length,
  };
}
