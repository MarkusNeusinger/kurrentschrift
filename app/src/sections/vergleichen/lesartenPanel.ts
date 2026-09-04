// The pure half of the Lesart page's readings block (VergleichenView): which
// of its five states one answer means, and whether the provenance line under
// the grid has anything to say. No React, no fetch.
//
// The distinction that matters is between „no word looks like this one" and
// „there is no dictionary to look in". Live on 2026-09-02 the server answered
// `{"readings": [], "dictionary": null}` for every word, and the page printed
// „sie ist wohl eindeutig" — a conclusion drawn from an empty shelf — with
// the note that the dictionary was missing right underneath it (website audit
// 2026-09-02, finding 1). The two are exclusive here, and `noReadings` is
// reachable only WITH a dictionary.

import type { LesartDictionaryOut, LesartReadingOut } from '@/lib/api';

export type LesartenState =
  /** No answer for the current text yet. */
  | 'loading'
  /** The request failed — the server is unreachable. */
  | 'error'
  /** The server has no dictionary loaded, so it cannot name words at all. */
  | 'noDictionary'
  /** A dictionary answered, but it was bucketed by an older look-alike fold
   * than the one the server now folds a guess with — so for exactly the pairs
   * the fold gained (g/p since 2026-09-04), it looks in a bucket the words are
   * not in. An empty answer then says nothing about the reading. */
  | 'staleDictionary'
  /** A dictionary answered, and nothing in it looks like this reading. */
  | 'noReadings'
  /** Readings to show. */
  | 'readings';

export function lesartenState(
  readings: readonly LesartReadingOut[] | null,
  dictionary: LesartDictionaryOut | null | undefined,
  failed: boolean,
): LesartenState {
  if (failed) return 'error';
  if (readings === null) return 'loading';
  if (readings.length > 0) return 'readings';
  if (!dictionary) return 'noDictionary';
  // Same rule as the empty shelf above, one step further in: a vocabulary the
  // server can no longer search by today's classes may not be quoted as
  // evidence that nothing looks like the guess.
  return dictionary.stale ? 'staleDictionary' : 'noReadings';
}

/** The provenance line („Wortformen aus … igerman98") belongs under the grid
 * only when a dictionary actually stands behind the answer; without one the
 * state above already carries the whole message. */
export function showsDictionaryNote(
  dictionary: LesartDictionaryOut | null | undefined,
): dictionary is LesartDictionaryOut {
  return !!dictionary;
}
