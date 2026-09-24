// Die Tintentreue-Verteilung — the per-box Ampel COUNTED over one hand, for the
// statistik Unteransicht (`admin-redesign.md` §6.3, Stufe 1 of §15.1).
//
// Pure and JSX-free, like `stripBoxRows.ts`, whose row model it reuses: the
// numbers here and the Nachfahr-Liste one view over are taken from the same
// rows, so „4 folgen nicht" on this page and the four red rows of the list
// cannot drift apart.
//
// NOTHING is judged here. The step and its reason are the server's
// (`core/eigenhand/tintentreue.py`, projected by `GET /eigenhand/pfade/{hand}`)
// and are only counted. In particular no share of the steps is folded into one
// number: the Ampel refuses a scalar on purpose („keine Skalarzahl"), and a
// „Treue-Quote" printed here would be that scalar by the back door.
//
// And the count stays ONE hand's. The thresholds are calibrated per hand and
// never comparable across hands (`tintentreue.py`, rule 3), so nothing here
// takes more than one hand's read.

import type { EigenhandPfadFassung, EigenhandTintentreueStufe } from '@/lib/api';
import {
  BOX_FILTERS,
  BOX_STATUSES,
  buildStripBoxRows,
  matchesStripBoxFilters,
  STRIP_BOX_LIST_SPEC,
  type BoxFilter,
  type BoxStatus,
  type StripBoxRow,
} from '@/sections/admin/eigenhand/stripBoxRows';
import { eigenhandUrl } from '@/sections/admin/shell/focus';
import { writeListState } from '@/sections/admin/shell/listState';

/** The four states in the order the view lists them: the three measured steps
 * best first, then the grey state — which is the ABSENCE of a measurement and
 * therefore last rather than „below red". */
export const VERTEILUNG_STUFEN: readonly EigenhandTintentreueStufe[] = [
  'folgt',
  'folgt teils',
  'folgt nicht',
  'nicht beurteilt',
];

/** A way into the Nachfahr-Liste that selects EXACTLY the counted boxes. */
export type ListenLink = { filter: BoxFilter } | { status: BoxStatus };

/** One counted group — a step, or one reason inside a step. */
export type Gruppe = {
  /** The server's own words: the step, the grey reason or the naming sensor. */
  name: string;
  count: number;
  /** The box addresses behind the count, in the read's order. */
  keys: string[];
  /** Set only where an existing list axis selects this very set of boxes. */
  link: ListenLink | null;
};

export type StufenZeile = Gruppe & {
  stufe: EigenhandTintentreueStufe;
  /** For a measured step, the sensors that named it; for the grey state, its
   * reasons. Most frequent first, ties in the order they were first met. */
  gruende: Gruppe[];
};

export type FassungsZeile = {
  strip: string;
  fassung: string;
  kaesten: number;
  stufen: Record<EigenhandTintentreueStufe, number>;
};

export type TintentreueVerteilung = {
  kaesten: number;
  fassungen: number;
  /** Boxes a sensor verdict stands on — the three steps together. */
  gemessen: number;
  stufen: StufenZeile[];
  proFassung: FassungsZeile[];
  /** Whether ANY counted box was graded under borrowed thresholds; `null` with
   * no box at all, because an empty hand has no thresholds to speak of. */
  vorlaeufig: boolean | null;
  /** Every threshold date the counted boxes carry. One per hand today (the
   * bounds live in code per hand); more than one would mean the read spans a
   * calibration, and the view says so rather than printing one of them. */
  schwellenStaende: string[];
};

const emptyStufen = (): Record<EigenhandTintentreueStufe, number> => ({
  folgt: 0,
  'folgt teils': 0,
  'folgt nicht': 0,
  'nicht beurteilt': 0,
});

// The candidate axes a link may use, specific before general: a chip names one
// next step, a status only a broad half of the list.
const CANDIDATES: readonly ListenLink[] = [
  ...BOX_FILTERS.map((filter) => ({ filter })),
  ...BOX_STATUSES.slice(1).map((status) => ({ status })),
];

const selects = (row: StripBoxRow, link: ListenLink): boolean =>
  'filter' in link
    ? matchesStripBoxFilters(row, [link.filter], null, '')
    : matchesStripBoxFilters(row, [], link.status, '');

/**
 * The list axis that shows exactly these boxes, or `null`.
 *
 * Tested against the ROWS rather than mapped by name, and for two reasons. The
 * list has no axis per Ampel step on purpose — its chips each name a next step,
 * not a shade of the verdict (`stripBoxRows.ts`) — so most counts have no
 * honest link, and a link that opened a SUPERSET under „3" would show a list of
 * eleven and be wrong on its face. And `grund` is free text on the wire: a
 * mapping keyed on its sentences would be a rename in `core` away from pointing
 * somewhere else. Equality of the two sets is the only promise a link here can
 * keep, so it is the one it makes.
 */
export function exactLink(rows: readonly StripBoxRow[], keys: readonly string[]): ListenLink | null {
  if (keys.length === 0) return null;
  const wanted = new Set(keys);
  for (const link of CANDIDATES) {
    const hit = rows.filter((row) => selects(row, link));
    if (hit.length === wanted.size && hit.every((row) => wanted.has(row.key))) return link;
  }
  return null;
}

/**
 * The address of the Nachfahr-Liste narrowed to one link — `?reiter=streifen`
 * in its default list mode, with the axis written by the list's own
 * `writeListState`, so the link carries exactly the words the list reads back
 * and no parameter of its own.
 */
export function listenLinkUrl(link: ListenLink): string {
  const base = eigenhandUrl('streifen');
  const [path, query = ''] = base.split('?');
  const next = writeListState(
    new URLSearchParams(query),
    'filter' in link ? { filters: [link.filter] } : { status: link.status },
    STRIP_BOX_LIST_SPEC,
  );
  return `${path}?${next.toString()}`;
}

function groupBy(rows: readonly StripBoxRow[], nameOf: (row: StripBoxRow) => string): Map<string, string[]> {
  // A Map keeps insertion order, which is the tiebreak the sort below relies on.
  const groups = new Map<string, string[]>();
  for (const row of rows) {
    const name = nameOf(row);
    const keys = groups.get(name);
    if (keys) keys.push(row.key);
    else groups.set(name, [row.key]);
  }
  return groups;
}

/** The hand-wide distribution of the Ampel, counted over every word box the
 * read carries — the same set the Nachfahr-Liste's counter is taken over. */
export function tintentreueVerteilung(fassungen: readonly EigenhandPfadFassung[]): TintentreueVerteilung {
  const rows = buildStripBoxRows({ fassungen, korbByBox: null });

  const stufen: StufenZeile[] = VERTEILUNG_STUFEN.map((stufe) => {
    const inStufe = rows.filter((row) => row.tintentreue.stufe === stufe);
    const keys = inStufe.map((row) => row.key);
    const gruende = [...groupBy(inStufe, (row) => row.tintentreue.grund).entries()]
      .map(([name, groupKeys], order) => ({ name, keys: groupKeys, order }))
      .sort((a, b) => b.keys.length - a.keys.length || a.order - b.order)
      .map(({ name, keys: groupKeys }) => ({
        name,
        count: groupKeys.length,
        keys: groupKeys,
        link: exactLink(rows, groupKeys),
      }));
    return { stufe, name: stufe, count: keys.length, keys, link: exactLink(rows, keys), gruende };
  });

  const proFassung = fassungen.map((fassung) => {
    const counts = emptyStufen();
    for (const box of fassung.kaesten) counts[box.tintentreue.stufe] += 1;
    return { strip: fassung.strip, fassung: fassung.fassung, kaesten: fassung.kaesten.length, stufen: counts };
  });

  return {
    kaesten: rows.length,
    fassungen: fassungen.length,
    gemessen: rows.filter((row) => row.tintentreue.stufe !== 'nicht beurteilt').length,
    stufen,
    proFassung,
    vorlaeufig: rows.length === 0 ? null : rows.some((row) => row.tintentreue.vorlaeufig),
    schwellenStaende: [...new Set(rows.map((row) => row.tintentreue.schwellen_stand))],
  };
}
