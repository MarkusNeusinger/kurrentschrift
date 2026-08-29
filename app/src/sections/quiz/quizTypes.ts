// Quiz option lists + view types. Domain truth (letters, glyph keys, split
// logic) lives in domain/glyphs.ts — this file only carries what the quiz
// surface itself offers the learner.

import { CONFIG } from '@/global-config';
import { cropUrl } from '@/lib/api';
import { de } from '@/locales';
import { type QuizMode } from '@/sections/quiz/useQuizEngine';

// Scripts selectable in the quiz. The quiz pool rides on the site-wide public
// source (CONFIG.sourceId) — currently the Sütterlin 1922 Ausgangsschrift. The
// others carry `available: false` for the planned scope; the setup shows a row
// only when it offers a real choice (see `offersChoice`), so an unavailable
// option is never a greyed-out promise on the learner's first screen.
export interface ScriptOption {
  id: string;
  label: string;
  available: boolean;
}

// A setup row is worth showing only when the learner can actually choose:
// two or more available options. One available option (today: the script,
// the difficulty) is a fact, stated in the summary/source line, not a row.
export const offersChoice = (options: ReadonlyArray<{ available: boolean }>): boolean =>
  options.filter((o) => o.available).length >= 2;

export const SCRIPTS: ScriptOption[] = [
  { id: 'kurrent', label: de.quiz.scripts.kurrent, available: false },
  { id: 'suetterlin', label: de.quiz.scripts.suetterlin, available: true },
  { id: 'offenbacher', label: de.quiz.scripts.offenbacher, available: false },
];

// What the quiz drills: single letters or whole words. Words read from the same
// locked Sütterlin source via WrittenWord; the engine offers only words whose
// every glyph is locked + traced, so the menu can show Wörter unconditionally
// and the start gate handles an empty word pool like an empty letter pool.
export type ModeOption = {
  id: QuizMode;
  label: string;
  available: boolean;
};

export const MODES: ModeOption[] = [
  { id: 'letters', label: de.quiz.setup.modeLetters, available: true },
  { id: 'words', label: de.quiz.setup.modeWords, available: true },
];

// Difficulty levels for the quiz. The idea: show each letter in progressively
// less-clean hands so the learner trains beyond copybook-perfect forms. Today
// only the clean Sütterlin 1922 Ausgangsschrift is in the DB, so the rougher
// levels stay `available: false` — and the row stays hidden (`offersChoice`)
// until real, messier handwriting sources are added (a post-MVP data task —
// see docs/concepts/architektur.md §12). The `difficulty` state already threads
// through the quiz, so only the option flags and the crop source change then.
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
// it to pull a less-clean hand instead of the clean plate. Today every level
// resolves to the same crop of the public source (rough levels are hidden in
// the setup).
export const questionCropUrl = (key: string, _difficulty: Difficulty): string => cropUrl(CONFIG.sourceId, key);
