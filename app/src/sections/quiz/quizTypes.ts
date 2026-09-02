// Quiz option lists + view types. Domain truth (letters, glyph keys, split
// logic) lives in domain/glyphs.ts — this file only carries what the quiz
// surface itself offers the learner.
//
// The option TABLES themselves (SCRIPTS/MODES/DIFFICULTIES and `offersChoice`)
// live in quizOptions.ts, which the Node-run crawler prerender reads too — the
// setup and the prerendered page must offer the same choices. They are
// re-exported here so SPA call sites keep one import path.

import { CONFIG } from '@/global-config';
import { cropUrl } from '@/lib/api';
import { type Difficulty } from '@/sections/quiz/quizOptions';

export {
  DIFFICULTIES,
  MODES,
  offersChoice,
  SCRIPTS,
  type Difficulty,
  type DifficultyOption,
  type ModeOption,
  type ScriptOption,
} from '@/sections/quiz/quizOptions';

// Pick the crop for a question. Difficulty is threaded in already: once messier
// handwriting sources land in the DB, this is the single place that branches on
// it to pull a less-clean hand instead of the clean plate. Today every level
// resolves to the same crop of the public source (rough levels are hidden in
// the setup).
export const questionCropUrl = (key: string, _difficulty: Difficulty): string => cropUrl(CONFIG.sourceId, key);
