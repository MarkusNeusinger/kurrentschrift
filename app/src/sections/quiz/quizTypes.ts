// Quiz option lists + view types. Domain truth (letters, glyph keys, split
// logic) lives in domain/glyphs.ts — this file only carries what the quiz
// surface itself offers the learner.

// Scripts selectable in the quiz. Only Kurrent (the Loth 1866 source) has data
// today; the others are shown disabled so the menu reflects the planned scope.
export interface ScriptOption {
  id: string;
  label: string;
  available: boolean;
}

export const SCRIPTS: ScriptOption[] = [
  { id: 'kurrent', label: 'Kurrent', available: true },
  { id: 'suetterlin', label: 'Sütterlin', available: false },
  { id: 'offenbacher', label: 'Offenbacher', available: false },
];

// Difficulty levels for the quiz. The idea: show each letter in progressively
// less-clean hands so the learner trains beyond copybook-perfect forms. v1 only
// has the clean Loth 1866 teaching plate, so the rougher levels are listed but
// disabled ("bald") until real, messier handwriting sources are added to the DB
// (a post-MVP data task — see docs/concepts/architektur.md §12). Once those
// sources exist the quiz picks crops by difficulty instead of always Loth; the
// `difficulty` state already threads through the quiz so only the crop source
// has to change here.
export type Difficulty = 'clean' | 'worn' | 'messy';

export interface DifficultyOption {
  id: Difficulty;
  label: string;
  hint: string;
  available: boolean;
}

export const DIFFICULTIES: DifficultyOption[] = [
  { id: 'clean', label: 'Sauber', hint: 'klare Lehrtafel', available: true },
  { id: 'worn', label: 'Geübt', hint: 'flüssige Alltagshand', available: false },
  { id: 'messy', label: 'Krakelig', hint: 'unsaubere, schwer lesbare Hand', available: false },
];
