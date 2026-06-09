// Quiz option lists + view types. Domain truth (letters, glyph keys, split
// logic) lives in domain/glyphs.ts — this file only carries what the quiz
// surface itself offers the learner.

import { cropUrl } from '@/lib/api';
import { de } from '@/locales';

// Scripts selectable in the quiz. Only Kurrent (the Loth 1866 source) has data
// today; the others are shown disabled so the menu reflects the planned scope.
export interface ScriptOption {
  id: string;
  label: string;
  available: boolean;
}

export const SCRIPTS: ScriptOption[] = [
  { id: 'kurrent', label: de.quiz.scripts.kurrent, available: true },
  { id: 'suetterlin', label: de.quiz.scripts.suetterlin, available: false },
  { id: 'offenbacher', label: de.quiz.scripts.offenbacher, available: false },
];

// Difficulty levels for the quiz. The idea: show each letter in progressively
// less-clean hands so the learner trains beyond copybook-perfect forms. v1 only
// has the clean Loth 1866 teaching plate, so the rougher levels are listed but
// disabled (the UI shows the German "bald" = "soon" marker) until real, messier handwriting sources are added to the DB
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
  { id: 'clean', label: de.quiz.difficulties.clean.label, hint: de.quiz.difficulties.clean.hint, available: true },
  { id: 'worn', label: de.quiz.difficulties.worn.label, hint: de.quiz.difficulties.worn.hint, available: false },
  { id: 'messy', label: de.quiz.difficulties.messy.label, hint: de.quiz.difficulties.messy.hint, available: false },
];

// Pick the crop for a question. Difficulty is threaded in already: once messier
// handwriting sources land in the DB, this is the single place that branches on
// it to pull a less-clean hand instead of the clean Loth plate. Today every
// level resolves to the same Loth crop (rough levels are disabled in setup).
export const questionCropUrl = (key: string, _difficulty: Difficulty): string => cropUrl(key);
