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

/**
 * The two Verfahren the strip store actually writes, as the Herkunfts-Chip
 * says them (author decision 2026-09-18, Q8 b): `tools.eigenhand.pfad` stamps
 * `tintenpfad`, an own-hand drawing `authored`. Passed in so this module keeps
 * carrying no German.
 */
export type VerfahrenLabels = {
  tintenpfad: string;
  authored: string;
};

/**
 * How a stored path came to be, as a reader should see it.
 *
 * Anything else is handed back RAW: `verfahren` is a free 64-character column,
 * so a run from another follower must stay readable under its own name rather
 * than be relabelled into one of the two the UI happens to know.
 */
export function verfahrenLabel(verfahren: string, labels: VerfahrenLabels): string {
  if (verfahren === 'tintenpfad') return labels.tintenpfad;
  if (verfahren === 'authored') return labels.authored;
  return verfahren;
}

export type PfadHerkunft = {
  /** The one Verfahren behind every path, RAW — `null` as soon as they differ. */
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
 * `ohneDatum` is the label for a path stored without a day (older rows) and
 * `labels` names the two known Verfahren, so all wording stays in the locale
 * file and this module stays pure.
 *
 * The agreement is decided on the RAW `verfahren` and only then labelled: two
 * followers that happened to share a label would otherwise collapse into one
 * named run, which is exactly the false claim the mixed case exists to avoid.
 */
export function pfadHerkunft(
  pfade: readonly EigenhandPfad[],
  ohneDatum: string,
  labels: VerfahrenLabels,
): PfadHerkunft {
  const verfahren = einheitlich(pfade.map((pfad) => pfad.verfahren));
  const datum = einheitlich(pfade.map((pfad) => pfad.erzeugt_am ?? ohneDatum));
  return {
    verfahren,
    datum,
    // An EMPTY list is not a mixed one — it has nothing to disagree about, and
    // the caller says „no path stored" there rather than naming a run.
    gemischt: pfade.length > 0 && (verfahren === null || datum === null),
    laeufe: pfade.map(
      (pfad) => `${pfad.word}: ${verfahrenLabel(pfad.verfahren, labels)} · ${pfad.erzeugt_am ?? ohneDatum}`,
    ),
  };
}
