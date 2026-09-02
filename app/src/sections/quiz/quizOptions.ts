// The quiz's option tables and the rule that decides whether a setup row is
// worth showing. Split out of quizTypes.ts so the Node-run crawler prerender
// (lib/seo/prerender.ts) can read the SAME availability facts the SPA reads:
// the setup hides a row that offers no real choice, and the prerendered page
// must hide it too — otherwise crawlers and AI answers keep offering scripts
// and difficulty levels the site does not have (website audit 2026-09-02).
//
// Therefore this module stays free of React, of the `@/` alias and of
// `import.meta.env` (global-config): plain Node loads it via type stripping,
// which knows neither the alias nor extensionless resolution. Relative imports
// WITH the .ts extension on purpose — same reason as sections/schriftkunde/
// sections.ts and tryTargets.ts. `quizTypes.ts` re-exports everything here, so
// call sites inside the SPA keep importing from there.
import { quiz } from '../../locales/de/quiz.ts';
import type { QuizMode } from './useQuizEngine.ts';

// Scripts selectable in the quiz. The quiz pool rides on the site-wide public
// source (CONFIG.sourceId) — currently the Sütterlin 1922 Ausgangsschrift. The
// others carry `available: false` for the planned scope.
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

// The single available option of a row that offers no choice — what the copy
// states as a fact instead of rendering a menu. Null when a row happens to
// have none (an empty pool), so a caller must handle that case explicitly.
export const soleOption = <T extends { available: boolean }>(options: readonly T[]): T | null => {
  const open = options.filter((o) => o.available);
  return open.length === 1 ? open[0] : null;
};

export const SCRIPTS: ScriptOption[] = [
  { id: 'kurrent', label: quiz.scripts.kurrent, available: false },
  { id: 'suetterlin', label: quiz.scripts.suetterlin, available: true },
  { id: 'offenbacher', label: quiz.scripts.offenbacher, available: false },
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
  { id: 'letters', label: quiz.setup.modeLetters, available: true },
  { id: 'words', label: quiz.setup.modeWords, available: true },
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
  { id: 'clean', label: quiz.difficulties.clean.label, hint: quiz.difficulties.clean.hint, available: true },
  { id: 'worn', label: quiz.difficulties.worn.label, hint: quiz.difficulties.worn.hint, available: false },
  { id: 'messy', label: quiz.difficulties.messy.label, hint: quiz.difficulties.messy.hint, available: false },
];
