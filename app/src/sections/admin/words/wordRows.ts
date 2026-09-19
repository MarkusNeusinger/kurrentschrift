// The Wörter overview as ROWS — what one line of the work list knows about a
// Wortprobe, which of the six URL axes it answers to and how the list is
// ordered.
//
// Pure and JSX-free, the third of the row models beside `letters/letterRows.ts`
// and `pairs/pairRows.ts`. What is special here is the number of axes: this
// overview searches by free text, selects a Nachfahr-Status AND stands in one
// of three tabs, on top of view, sort and page. The author's decision Q5 (a) of
// 2026-09-19 gives each of them its own German parameter rather than packing
// three into one token, and the vocabularies below are that decision as data.
//
// Two facts per row are ANSWERS that may be missing, and both stay `null`
// rather than 0: the basket read is admin-gated and may 401, and a score is
// only there once somebody paid for it — „Loss 0.00" would be an excellent
// mark invented for a Wortprobe nobody measured.

import type { WordInstanceOut, WordSampleOut, WordSampleScoreOut } from '@/lib/api';
import type { ListSpec } from '@/sections/admin/shell/listState';
import { matchesTraceFilter, traceStatusOf, type TraceFilter, type TraceStatus } from '@/sections/admin/shell/model';

/** The plate's own order, and „worst first" — which costs a sweep, so it stays
 * an explicit act rather than a default that quietly fires 169 requests. */
export const WORD_SORTS = ['reihenfolge', 'schlechteste'] as const;
export type WordSort = (typeof WORD_SORTS)[number];

/** `status=` — the existing Nachfahren selection, in German URL words. The
 * first entry is the default and therefore never appears in a link. */
export const WORD_STATUSES = ['alle', 'offen', 'nachgefahren', 'unvollstaendig'] as const;
export type WordStatus = (typeof WORD_STATUSES)[number];

/** `reiter=` — which tab of this page. „Andere Hand" is the Abb.-22 set, and
 * the third tab is the Nachfahr-Übersicht, which is not a list of Wortproben
 * but a stack of the author's own lines (`AuthoredTraceReview`). */
export const WORD_TABS = ['woerter', 'andere', 'nachgefahren'] as const;
export type WordTab = (typeof WORD_TABS)[number];

export const WORD_LIST_SPEC: ListSpec<never, WordSort, WordStatus, WordTab> = {
  // No chips here: this overview's `filter=` is the free-text „Proben filtern"
  // field that was always on the surface, now in the URL where a link can
  // carry it.
  filters: [],
  freeText: true,
  sorts: WORD_SORTS,
  defaultSort: 'reihenfolge',
  statuses: WORD_STATUSES,
  tabs: WORD_TABS,
};

/**
 * What the view holds per Wortprobe: a measurement, or the state of the request
 * that is fetching one. The two sentinels are progress of the SURFACE — they
 * belong to the button that was pressed, never to the row.
 */
export type ScoreEntry = WordSampleScoreOut | 'busy' | 'error';

/**
 * What one entry of that record may be SHOWN as. Two different failures end in
 * the same word: the request did not answer (`'error'`), or it answered „nicht
 * bewertbar" (`failed`) for a Wortprobe whose templates are missing. The second
 * carries a `loss` field all the same, so a surface that only checks for an
 * object prints an excellent mark for a word the engine could not even write.
 * Stated here once, for the list's chip and the detail's alike.
 */
export function scoreOutcome(entry: ScoreEntry | undefined): 'none' | 'busy' | 'failed' | 'measured' {
  if (entry === undefined) return 'none';
  if (entry === 'busy') return 'busy';
  if (entry === 'error' || entry.failed) return 'failed';
  return 'measured';
}

/** The measurements out of such a record, so a running or failed request can
 * never be mistaken for a Loss by the rows. */
export function settledScores(
  entries: Readonly<Record<string, ScoreEntry | undefined>>,
): Record<string, WordSampleScoreOut> {
  const out: Record<string, WordSampleScoreOut> = {};
  for (const [id, entry] of Object.entries(entries)) {
    if (entry && entry !== 'busy' && entry !== 'error') out[id] = entry;
  }
  return out;
}

/** The URL word for a status ↔ the filter the evidence model already speaks
 * (`shell/model.ts`), so the rule itself is stated once and only translated. */
export function traceFilterOf(status: WordStatus | null): TraceFilter {
  if (status === 'offen') return 'open';
  if (status === 'nachgefahren') return 'authored';
  if (status === 'unvollstaendig') return 'incomplete';
  return 'all';
}

export type WordRow = {
  sampleId: string;
  word: string;
  /** Another writer's plate (Abb. 22): context in the list, never a reference
   * of THIS hand — which is why it has a tab and a chip of its own (V4). */
  foreign: boolean;
  /** The set tag as the sidecar spells it, for the chip's own words. */
  foreignSet: string | null;
  status: TraceStatus;
  /** How many stored Bahnen this Wortprobe carries. Today's schema caps it at
   * one per (kind, specimen), but a Bahn is not the same statement as
   * „nachgefahren": a harvested fit is a stored line too, and only an authored
   * one is the author's own pen work. */
  traces: number;
  /** null = the basket read has not answered; 0 = it did and this word is clean. */
  korbOpen: number | null;
  /** null = no score was computed for this Wortprobe — never a zero. */
  loss: number | null;
  /** The sweep answered for this row but could not judge it. */
  scoreFailed: boolean;
  /** Carried along so the expanded row and the gallery mount the existing card
   * without a second lookup. */
  sample: WordSampleOut;
  score: WordSampleScoreOut | null;
  /** This Wortprobe's stored trace, for the card overlay's registration. */
  traced: WordInstanceOut | null;
};

/**
 * Which tab a Wortprobe belongs to — the rule `WordComparison` carried inline
 * as `matchesMode`. Truthiness, not `!= null`: an empty set tag must not count
 * as another hand. The Abb.-20 pair drills belong to neither tab; they have
 * their home under Übergänge.
 */
export function wordTabOf(sample: WordSampleOut): WordTab | null {
  if (sample.sample_set) return 'andere';
  return sample.kind === 'word' ? 'woerter' : null;
}

export type WordRowInput = {
  samples: readonly WordSampleOut[];
  /** Every stored word instance of the source, grouped by specimen id. */
  tracesBySpecimen: Map<string, WordInstanceOut[]>;
  tab: WordTab;
  /** Open basket items per word TEXT; null while the read is unknown. */
  korbByWord: Map<string, number> | null;
  scores: Readonly<Record<string, WordSampleScoreOut | undefined>>;
};

/** One row per Wortprobe of the chosen tab, in the sidecar's own order. */
export function buildWordRows(input: WordRowInput): WordRow[] {
  const rows: WordRow[] = [];
  for (const sample of input.samples) {
    if (wordTabOf(sample) !== input.tab) continue;
    const stored = input.tracesBySpecimen.get(sample.id) ?? [];
    // The one the card's overlay registers on: an authored line wins, because
    // it is the measured registration the author set by hand.
    const traced = stored.find((row) => row.provenance === 'authored') ?? stored[0] ?? null;
    const score = input.scores[sample.id];
    rows.push({
      sampleId: sample.id,
      word: sample.word,
      foreign: Boolean(sample.sample_set),
      foreignSet: sample.sample_set || null,
      status: traceStatusOf(sample, traced),
      traces: stored.length,
      korbOpen: input.korbByWord === null ? null : (input.korbByWord.get(sample.word) ?? 0),
      loss: score && !score.failed ? score.loss : null,
      scoreFailed: score?.failed === true,
      sample,
      score: score ?? null,
      traced,
    });
  }
  return rows;
}

/**
 * Whether one row survives the two selecting axes — the status and the search
 * needle, ANDed. The needle matches the WORD, not the specimen id: the id is
 * shown so a row can be named in a report, but „ab" would otherwise select
 * every sample of a plate called `abb19-…`.
 */
export function matchesWordFilters(row: WordRow, status: WordStatus | null, text: string): boolean {
  if (!matchesTraceFilter(traceFilterOf(status), row.status)) return false;
  const needle = text.trim().toLowerCase();
  return !needle || row.word.toLowerCase().includes(needle);
}

/**
 * Sidecar order, or „Schlechteste zuerst" = DESCENDING loss with the unscored
 * rows at the end — a Wortprobe nobody measured is not the best one. Ties keep
 * the sidecar order, so the list does not reshuffle under equal losses.
 */
export function sortWordRows(rows: readonly WordRow[], sort: WordSort): WordRow[] {
  if (sort === 'reihenfolge') return [...rows];
  return rows
    .map((row, index) => ({ row, index }))
    .sort((a, b) => (b.row.loss ?? -Infinity) - (a.row.loss ?? -Infinity) || a.index - b.index)
    .map((entry) => entry.row);
}

/** Is there anything to rank by? Without one computed score „Schlechteste
 * zuerst" would silently be the sidecar order again — the toolbar says so. */
export const wordsRankable = (rows: readonly WordRow[]): boolean => rows.some((row) => row.loss !== null);

/**
 * Whether a `sort=schlechteste` in the URL has stopped describing the list —
 * „Neu laden" drops the measurements, a pasted link arrives without any, and
 * the Fremdhand tab was never swept. The view then drops the axis, so the link,
 * the toolbar and the row order agree again.
 *
 * `loaded` and the row count are the two silences that are NOT an answer about
 * the rows: a read still in flight and a tab with nothing in it would otherwise
 * eat a deep link's ranking before its data arrived.
 */
export function rankingIsStale(rows: readonly WordRow[], sort: WordSort, loaded: boolean): boolean {
  return loaded && rows.length > 0 && sort === 'schlechteste' && !wordsRankable(rows);
}

/**
 * Progress of the manual reference set for this tab — counted over the tab's
 * WHOLE list, not the filtered slice, so the tally stays the tab's truth while
 * searching. The clipped specimens leave the DENOMINATOR: they are not work
 * anyone can do, and counting them would keep the tally short of its total for
 * good. They get their own number instead.
 */
export function wordTally(rows: readonly WordRow[]): { done: number; total: number; incomplete: number } {
  return {
    done: rows.filter((row) => row.status === 'authored').length,
    total: rows.filter((row) => row.status !== 'incomplete').length,
    incomplete: rows.filter((row) => row.status === 'incomplete').length,
  };
}
