// Whose run a drawn path came out of — read off the paths themselves, never
// off the first one.
//
// A Fassung's stored list is not necessarily ONE run: `tools.eigenhand.pfad`
// merges what it followed over what was already there, so re-following a
// single word (`--box`) leaves the other words on their older Verfahren and
// day, and a whole-row run does the same for every box it had to skip. Reading
// the caption off `pfade[0]` therefore put one word's provenance under all of
// them (Copilot review, PR #598).
//
// Kept beside the panel so it is testable without rendering: „these two paths
// come from different runs" is exactly the kind of claim a screenshot cannot
// disprove — two paths from two days still look like two paths.

import type { EigenhandPfad } from '@/lib/api';

export type PfadHerkunft = {
  /** The one Verfahren behind every path — `null` as soon as they differ. */
  verfahren: string | null;
  /** The one day they were followed on — `null` as soon as they differ. */
  datum: string | null;
  /** Whether either of the two differs across the list. */
  gemischt: boolean;
  /** One line per path, „Wort: Verfahren · Datum" — the mixed case's detail. */
  laeufe: string[];
};

/** The single value every entry shares, or `null` when there is no such value. */
function einheitlich(values: readonly string[]): string | null {
  const first = values[0];
  return first !== undefined && values.every((value) => value === first) ? first : null;
}

/**
 * Read the provenance of the paths currently drawn.
 *
 * `ohneDatum` is the label for a path stored without a day (older rows), so the
 * wording stays in the locale file and this module stays pure.
 */
export function pfadHerkunft(pfade: readonly EigenhandPfad[], ohneDatum: string): PfadHerkunft {
  const verfahren = einheitlich(pfade.map((pfad) => pfad.verfahren));
  const datum = einheitlich(pfade.map((pfad) => pfad.erzeugt_am ?? ohneDatum));
  return {
    verfahren,
    datum,
    // An EMPTY list is not a mixed one — it has nothing to disagree about, and
    // the caller says „no path stored" there rather than naming a run.
    gemischt: pfade.length > 0 && (verfahren === null || datum === null),
    laeufe: pfade.map((pfad) => `${pfad.word}: ${pfad.verfahren} · ${pfad.erzeugt_am ?? ohneDatum}`),
  };
}
