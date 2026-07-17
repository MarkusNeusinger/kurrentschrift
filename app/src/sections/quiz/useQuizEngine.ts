// useQuizEngine — all quiz state + logic for the reading drill, no JSX. The view
// (QuizView) only switches between the setup/play/results panels and feeds them
// from this hook. Pool derivation, question picking, verdicts, scoring and the
// miss/confusion tallies all live here so the panels stay purely presentational.
//
// The drill reads in two modes (architektur.md §14, "Tinte & Vergleich" handoff):
//   • letters — a single glyph "as written"; the learner names the Latin letter.
//   • words   — a whole word "as written"; the learner reads the word.
// Both flow identically: a question is shown, four choices offered; a correct
// pick auto-advances, a wrong pick freezes and shows the two forms side by side
// ("deine Wahl ↔ richtig") until the learner clicks Weiter.

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { knownGlyph, quizKeysFromLocked, type KnownGlyph } from '@/domain/glyphs';
import { glyphKeysOf, shapeText } from '@/domain/shaping';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion';
import { type Difficulty } from '@/sections/quiz/quizTypes';
import { similarity, WORD_BANK, type WordEntry } from '@/sections/quiz/wordBank';
import { getQuizWords, type QuizWordOut } from '@/lib/api';
import type { QuizSourceData } from '@/sections/quiz/useQuizSource';

// DB row → the engine's WordEntry (null → undefined for the optional fields).
const toEntry = (r: QuizWordOut): WordEntry => ({
  word: r.word,
  distractors: r.distractors,
  era: r.era,
  note: r.note ?? undefined,
  fugen: r.fugen ?? undefined,
});

// Quiz subject: single letters or whole words.
export type QuizMode = 'letters' | 'words';
export type Verdict = 'idle' | 'correct' | 'wrong';

// Pause after a correct pick before the next question loads, so the green
// "Super Übereinstimmung" reveal registers. Exported so the play panel's
// auto-advance progress bar runs for exactly this long.
export const AUTO_ADVANCE_MS = 1300;

// A question is one glyph (letters mode) or one whole word (words mode).
export interface LetterQuestion {
  kind: 'letter';
  key: string; // glyph_key — rendered via WrittenGlyph (crop fallback)
  kg: KnownGlyph;
}
export interface WordQuestion {
  kind: 'word';
  word: string; // the clean display/answer form (no Fuge marker)
  render: string; // the form passed to WrittenWord — may carry a Fuge marker `|`
  note?: string; // optional gloss for a dated/rare word, shown in the reveal
}
export type Question = LetterQuestion | WordQuestion;

// One multiple-choice option, unified across modes.
export interface Choice {
  // The canonical answer compared against the solution: a lowercase letter
  // (letters) or the word itself (words).
  value: string;
  // What's printed on the button: the cased letter or the word.
  label: string;
  // The written form to render in the comparison when this option is picked:
  // a glyph_key (letters) or the word string (words). Null when no traced form
  // exists — a bare-alphabet filler letter, or a distractor word not fully
  // traced — and the comparison then shows the label in plain type instead.
  renderKey: string | null;
}

// A renderable reference used by the results screen to draw a glyph/word form.
export interface TallyRef {
  label: string; // human label (modern letter / the word)
  renderKey: string | null; // glyph_key (letter) or word (word) to render; null → label only
  kind: 'letter' | 'word';
}
export interface MissEntry extends TallyRef {
  count: number;
}
// Per-question miss counts, keyed by a stable id (one entry per letter/word).
export type MissMap = Record<string, MissEntry>;
export interface ConfusionEntry {
  correct: TallyRef;
  guessed: TallyRef;
  count: number;
}
// Confusion tallies keyed `correct__guessed`, feeding "Häufig verwechselt".
export type ConfusionMap = Record<string, ConfusionEntry>;

const ALPHABET = Array.from({ length: 26 }, (_, i) => String.fromCharCode(97 + i));

const sample = <T,>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];

// Fisher–Yates: an unbiased, transitive shuffle — unlike `sort(() => Math.random()
// - 0.5)`, whose comparator is non-transitive and engine-dependent.
const shuffle = <T,>(arr: T[]): T[] => {
  const out = [...arr];
  for (let i = out.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
};

// Draw `k` distinct words from (word, weight) pairs, probability proportional
// to weight — strong cursive confusions come up more often, weak ones still
// appear, so the options change from round to round.
const weightedSample = (entries: Array<[string, number]>, k: number): string[] => {
  const pool = [...entries];
  const out: string[] = [];
  while (out.length < k && pool.length > 0) {
    const total = pool.reduce((sum, [, w]) => sum + w, 0);
    let r = Math.random() * total;
    let i = 0;
    while (i < pool.length - 1 && (r -= pool[i][1]) > 0) i += 1;
    out.push(pool[i][0]);
    pool.splice(i, 1);
  }
  return out;
};

// Display the option/solution in the case of the shown glyph so the prompt and
// the answer read consistently (a Versal crop → uppercase label).
export const inCase = (letter: string, kg: KnownGlyph): string =>
  kg.letterCase === 'upper' ? letter.toUpperCase() : letter;

const questionId = (q: Question): string => (q.kind === 'word' ? `W:${q.word}` : `L:${q.key}`);

export function useQuizEngine({ bboxesByKey, glyphsByKey }: Pick<QuizSourceData, 'bboxesByKey' | 'glyphsByKey'>) {
  const reducedMotion = usePrefersReducedMotion();

  // The word bank: fetched from the DB (GET /quiz-words), falling back to the
  // bundled WORD_BANK until — or unless — the API answers, so the quiz always
  // has words even offline or before the seed migration has run.
  const [words, setWords] = useState<WordEntry[]>(WORD_BANK);
  useEffect(() => {
    let alive = true;
    // Cold-start retry like the other boot reads (min-instances=0 backend) — a
    // failed first request would otherwise silently pin the bundled fallback
    // bank for the whole session.
    getQuizWords({ retries: 3 })
      .then((rows) => {
        if (alive && rows.length > 0) setWords(rows.map(toEntry));
      })
      .catch(() => {
        /* keep the bundled fallback */
      });
    return () => {
      alive = false;
    };
  }, []);

  const [script, setScript] = useState('suetterlin');
  const [mode, setMode] = useState<QuizMode>('letters');
  const [difficulty, setDifficulty] = useState<Difficulty>('clean');
  const [started, setStarted] = useState(false);
  const [finished, setFinished] = useState(false);

  const [current, setCurrent] = useState<Question | null>(null);
  // Bumped on every new question so WrittenGlyph/WrittenWord remount and replay
  // their write-in even when the same item happens to come up again.
  const [qNonce, setQNonce] = useState(0);
  const [choices, setChoices] = useState<Choice[]>([]);
  const [verdict, setVerdict] = useState<Verdict>('idle');
  // The option the learner picked, so the play panel can colour the picked
  // button and render its form in the comparison. Null while unanswered.
  const [picked, setPicked] = useState<Choice | null>(null);
  const [stats, setStats] = useState({ correct: 0, seen: 0, streak: 0, bestStreak: 0 });
  const [misses, setMisses] = useState<MissMap>({});
  const [confusions, setConfusions] = useState<ConfusionMap>({});

  // Pending auto-advance timer, tracked so it can be cancelled when the learner
  // quits/restarts (or the page unmounts) before it fires.
  const advanceTimer = useRef<number | null>(null);
  const clearAdvance = useCallback(() => {
    if (advanceTimer.current !== null) {
      window.clearTimeout(advanceTimer.current);
      advanceTimer.current = null;
    }
  }, []);

  // Is this exact glyph_key locked AND traced (a canonical exists)? The bar a
  // glyph must clear to render "as written".
  const isKeyReady = useCallback(
    (key: string): boolean => bboxesByKey[key]?.locked === true && glyphsByKey[key]?.has_data === true,
    [bboxesByKey, glyphsByKey],
  );

  // ——— Letters pool ———
  // Only locked letters that resolve to a known glyph. quizKeysFromLocked
  // collapses each letter to ONE quiz unit (its positions share a form) unless
  // explicitly split; the rep key prefers a position that owns a canonical.
  const letterPool = useMemo<LetterQuestion[]>(
    () =>
      quizKeysFromLocked(bboxesByKey, (key) => glyphsByKey[key]?.has_data === true)
        .map((key) => {
          const kg = knownGlyph(key);
          return kg ? ({ kind: 'letter', key, kg } as LetterQuestion) : null;
        })
        .filter((x): x is LetterQuestion => x !== null),
    [bboxesByKey, glyphsByKey],
  );

  // ——— Words pool ———
  // A word is offered only when EVERY glyph it needs is locked + traced, so a
  // word is never shown half-written. Distractor renderability is computed the
  // same way (for the comparison).
  const isWordRenderable = useCallback(
    (word: string): boolean => {
      const keys = glyphKeysOf(shapeText(word));
      return keys.length > 0 && keys.every(isKeyReady);
    },
    [isKeyReady],
  );
  // Keep only fully-renderable words — checking the render form (with its Fuge
  // marker), so a compound is offered exactly when its round Schluss-s glyph
  // (`s-round-medial`) is traced too, never shown with the wrong s.
  const wordPool = useMemo<WordEntry[]>(
    () => words.filter((e) => isWordRenderable(e.fugen ?? e.word)),
    [isWordRenderable, words],
  );

  const poolSize = mode === 'words' ? wordPool.length : letterPool.length;

  // ——— Choice construction ———
  // Letter distractors prefer real specimens so each can render its own form:
  // other locked letters of the SAME case, deduped by answer letter. Top up from
  // the bare alphabet (no form) only when too few letters are locked.
  const buildLetterChoices = useCallback((item: LetterQuestion, pool: LetterQuestion[]): Choice[] => {
    const correctLetter = item.kg.answer;
    const correct: Choice = { value: correctLetter, label: inCase(correctLetter, item.kg), renderKey: item.key };

    const byLetter = new Map<string, LetterQuestion>();
    for (const i of pool) {
      if (i.kg.letterCase !== item.kg.letterCase || i.kg.answer === correctLetter) continue;
      if (!byLetter.has(i.kg.answer)) byLetter.set(i.kg.answer, i);
    }
    const distractors: Choice[] = shuffle(Array.from(byLetter.values()))
      .slice(0, 3)
      .map((i) => ({ value: i.kg.answer, label: inCase(i.kg.answer, item.kg), renderKey: i.key }));

    if (distractors.length < 3) {
      const used = new Set([correctLetter, ...distractors.map((d) => d.value)]);
      for (const c of shuffle(ALPHABET.filter((l) => !used.has(l)))) {
        if (distractors.length >= 3) break;
        distractors.push({ value: c, label: inCase(c, item.kg), renderKey: null });
      }
    }
    return shuffle([correct, ...distractors]);
  }, []);

  // Word distractors: one of the entry's pinned misreads is always offered (the
  // hand-curated anchor); the remaining slots are drawn from the WHOLE bank by
  // the similarity rules, weighted by score — so every round shows different but
  // plausible misreads instead of a fixed trio. Each is rendered "as written" in
  // the comparison only when fully traced (its render form may carry a Fuge
  // marker).
  const buildWordChoices = useCallback(
    (entry: WordEntry): Choice[] => {
      const answer = entry.word;
      const renderFormOf = (w: string): string => words.find((e) => e.word === w)?.fugen ?? w;
      const correct: Choice = { value: answer, label: answer, renderKey: entry.fugen ?? answer };

      const pinned = entry.distractors.filter((d) => d !== answer);
      const anchor = pinned.length > 0 ? [sample(pinned)] : [];
      // Score every bank word as a misread of the answer; undrawn pins rejoin
      // the pool with a strong weight so multi-pin entries still rotate.
      const PINNED_WEIGHT = 8;
      const scored: Array<[string, number]> = pinned
        .filter((d) => !anchor.includes(d))
        .map((d) => [d, PINNED_WEIGHT] as [string, number]);
      for (const e of words) {
        if (e.word === answer || pinned.includes(e.word)) continue;
        const score = similarity(answer, e.word);
        if (score > 0) scored.push([e.word, score]);
      }
      const pool = [...anchor, ...weightedSample(scored, 3 - anchor.length)];
      // Top up from the rest of the bank if a word has too few near-forms, so
      // three options are always available.
      if (pool.length < 3) {
        for (const w of shuffle(words.map((e) => e.word))) {
          if (pool.length >= 3) break;
          if (w !== answer && !pool.includes(w)) pool.push(w);
        }
      }
      const distractors: Choice[] = pool.slice(0, 3).map((d) => {
        const rf = renderFormOf(d);
        return { value: d, label: d, renderKey: isWordRenderable(rf) ? rf : null };
      });
      return shuffle([correct, ...distractors]);
    },
    [isWordRenderable, words],
  );

  const nextQuestion = useCallback(
    (excludeId?: string) => {
      if (mode === 'words') {
        if (wordPool.length === 0) {
          setCurrent(null);
          return;
        }
        let pick = sample(wordPool);
        if (wordPool.length > 1 && excludeId) {
          let guard = 0;
          while (`W:${pick.word}` === excludeId && guard < 12) {
            pick = sample(wordPool);
            guard += 1;
          }
        }
        setCurrent({ kind: 'word', word: pick.word, render: pick.fugen ?? pick.word, note: pick.note });
        setChoices(buildWordChoices(pick));
      } else {
        if (letterPool.length === 0) {
          setCurrent(null);
          return;
        }
        let pick = sample(letterPool);
        if (letterPool.length > 1 && excludeId) {
          let guard = 0;
          while (`L:${pick.key}` === excludeId && guard < 12) {
            pick = sample(letterPool);
            guard += 1;
          }
        }
        setCurrent({ kind: 'letter', key: pick.key, kg: pick.kg });
        setChoices(buildLetterChoices(pick, letterPool));
      }
      setQNonce((n) => n + 1);
      setVerdict('idle');
      setPicked(null);
    },
    [mode, wordPool, letterPool, buildWordChoices, buildLetterChoices],
  );

  const start = useCallback(() => {
    clearAdvance();
    setStats({ correct: 0, seen: 0, streak: 0, bestStreak: 0 });
    setMisses({});
    setConfusions({});
    setFinished(false);
    setStarted(true);
    nextQuestion();
  }, [nextQuestion, clearAdvance]);

  const advance = useCallback(() => {
    clearAdvance();
    nextQuestion(current ? questionId(current) : undefined);
  }, [current, nextQuestion, clearAdvance]);

  const scheduleAdvance = useCallback(() => {
    clearAdvance();
    advanceTimer.current = window.setTimeout(() => {
      advanceTimer.current = null;
      advance();
    }, AUTO_ADVANCE_MS);
  }, [clearAdvance, advance]);

  const finish = useCallback(() => {
    clearAdvance();
    if (stats.seen > 0) setFinished(true);
    else setStarted(false);
  }, [stats.seen, clearAdvance]);

  const backToSetup = useCallback(() => {
    clearAdvance();
    setStarted(false);
    setFinished(false);
  }, [clearAdvance]);

  // Cancel a pending advance on unmount.
  useEffect(() => clearAdvance, [clearAdvance]);

  const markResult = useCallback((ok: boolean) => {
    setStats((s) => {
      const streak = ok ? s.streak + 1 : 0;
      return {
        correct: s.correct + (ok ? 1 : 0),
        seen: s.seen + 1,
        streak,
        bestStreak: Math.max(s.bestStreak, streak),
      };
    });
  }, []);

  const refOf = useCallback((q: Question): TallyRef => {
    if (q.kind === 'word') return { label: q.word, renderKey: q.render, kind: 'word' };
    return { label: inCase(q.kg.answer, q.kg), renderKey: q.key, kind: 'letter' };
  }, []);

  // Tally a miss for the shown item, plus the confusion against the wrong guess.
  const recordMiss = useCallback(
    (q: Question, guess: Choice) => {
      const correctRef = refOf(q);
      const missId = questionId(q);
      setMisses((m) => ({ ...m, [missId]: { ...correctRef, count: (m[missId]?.count ?? 0) + 1 } }));
      const guessedRef: TallyRef = { label: guess.label, renderKey: guess.renderKey, kind: q.kind };
      const cId = correctRef.renderKey ?? correctRef.label;
      const gId = guessedRef.renderKey ?? guessedRef.label;
      const key = `${cId}__${gId}`;
      setConfusions((c) => ({
        ...c,
        [key]: { correct: correctRef, guessed: guessedRef, count: (c[key]?.count ?? 0) + 1 },
      }));
    },
    [refOf],
  );

  const pickChoice = useCallback(
    (choice: Choice) => {
      // One-shot: the first pick is final. Guard against a late double-count.
      if (!current || verdict !== 'idle') return;
      setPicked(choice);
      const correctValue = current.kind === 'word' ? current.word : current.kg.answer;
      if (choice.value === correctValue) {
        markResult(true);
        setVerdict('correct');
        // Reduced motion: skip the auto-advance (and its bar); the panel offers
        // a manual "Weiter" instead, so nothing jumps unbidden.
        if (!reducedMotion) scheduleAdvance();
      } else {
        recordMiss(current, choice);
        markResult(false);
        setVerdict('wrong');
      }
    },
    [current, verdict, markResult, recordMiss, scheduleAdvance, reducedMotion],
  );

  return {
    // setup state
    script,
    setScript,
    mode,
    setMode,
    difficulty,
    setDifficulty,
    poolSize,
    // session state
    started,
    finished,
    // per-question state
    current,
    qNonce,
    choices,
    verdict,
    picked,
    reducedMotion,
    // session tallies
    stats,
    misses,
    confusions,
    // actions
    start,
    advance,
    finish,
    backToSetup,
    pickChoice,
  };
}
