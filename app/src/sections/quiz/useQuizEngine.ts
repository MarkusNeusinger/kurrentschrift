// useQuizEngine — all quiz state + logic for the letter drill, no JSX. The view
// (QuizView) only switches between the setup/play/results panels and feeds them
// from this hook. Pool derivation, question picking, verdicts, scoring and the
// miss/confusion tallies all live here so the panels stay purely presentational.

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { knownGlyph, quizKeysFromLocked, type KnownGlyph } from '@/domain/glyphs';
import { type Difficulty } from '@/sections/quiz/quizTypes';
import { useAdmin } from '@/context/AdminContext';

export type CaseMode = 'lower' | 'upper' | 'mixed';
export type AnswerMode = 'type' | 'choice';
// Quiz subject: single letters (today) or whole words (post-MVP, disabled in
// setup for now).
export type QuizMode = 'letters' | 'words';
// Prompt view: the synthesised pen ("Geschrieben") vs. the real chart cutout
// ("Original"). Lives here (not in QuestionVisual) so the learner's choice
// persists across questions and only resets when a new session starts.
export type PromptView = 'written' | 'crop';

export interface QuizItem {
  key: string;
  kg: KnownGlyph;
}

// One multiple-choice option. Carries the answer letter AND the glyph key whose
// chart crop overlays the prompt when this option is picked (the double-exposure
// match/deviation reveal). `cropKey` is null for a bare-alphabet filler that has
// no locked specimen — then the pick still resolves, just without a crop overlay.
export interface Choice {
  letter: string;
  cropKey: string | null;
}

// Per-letter miss counts (keyed by the rendered glyph the learner saw, e.g. `ſ`)
// and confusion tallies (keyed `seen→guessed`). Both accumulate across a session
// and feed the end screen.
export type MissMap = Record<string, number>;
export type ConfusionMap = Record<string, number>;

export const CONFUSION_SEP = '→';

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

// Display the option/solution in the case of the shown glyph so the prompt and
// the answer read consistently (a Versal crop → uppercase label).
export const inCase = (letter: string, kg: KnownGlyph): string =>
  kg.letterCase === 'upper' ? letter.toUpperCase() : letter;

export function useQuizEngine() {
  const { bboxesByKey, glyphsByKey } = useAdmin();

  const [script, setScript] = useState('suetterlin');
  const [mode, setMode] = useState<QuizMode>('letters');
  // Defaults the learner most often wants: all letters at once, picked from
  // multiple choice.
  const [caseMode, setCaseMode] = useState<CaseMode>('mixed');
  const [answerMode, setAnswerMode] = useState<AnswerMode>('choice');
  const [difficulty, setDifficulty] = useState<Difficulty>('clean');
  // Prompt view (Geschrieben/Original). Persists across questions; only a new
  // session resets it to the written default.
  const [view, setView] = useState<PromptView>('written');
  const [started, setStarted] = useState(false);
  const [finished, setFinished] = useState(false);

  const [current, setCurrent] = useState<QuizItem | null>(null);
  // Bumped on every new question so the WrittenGlyph remounts and replays its
  // writing animation even when the same letter happens to come up again.
  const [qNonce, setQNonce] = useState(0);
  const [choices, setChoices] = useState<Choice[]>([]);
  const [input, setInput] = useState('');
  const [verdict, setVerdict] = useState<'idle' | 'correct' | 'wrong' | 'revealed'>('idle');
  // The option the learner picked (or a synthesised one for the typed guess), so
  // the play panel can colour the picked button and overlay its crop. Null while
  // the question is unanswered or was given up via the reveal button. Every answer
  // is now one-shot — the first pick is final — so there is no wrong-then-retry
  // bookkeeping to track.
  const [picked, setPicked] = useState<Choice | null>(null);
  const [stats, setStats] = useState({ correct: 0, seen: 0, streak: 0, bestStreak: 0 });
  const [misses, setMisses] = useState<MissMap>({});
  const [confusions, setConfusions] = useState<ConfusionMap>({});

  // Pending "advance after a correct answer" timer, tracked so it can be
  // cancelled when the learner quits/restarts (or the page unmounts) before it
  // fires — otherwise a late advance would mutate quiz state off the play screen.
  const advanceTimer = useRef<number | null>(null);

  const clearAdvance = useCallback(() => {
    if (advanceTimer.current !== null) {
      window.clearTimeout(advanceTimer.current);
      advanceTimer.current = null;
    }
  }, []);

  // Only locked (finished) letters that resolve to a known glyph. Locking is
  // the admin's "this one is final" marker, so the public quiz never surfaces
  // a half-calibrated crop — the vocabulary grows as letters get locked.
  //
  // quizKeysFromLocked collapses each letter to ONE entry by default (its three
  // positions share one form), so a unified letter appears once; only a letter
  // explicitly split into per-position variants surfaces one entry per position.
  // The representative key it returns prefers a position that owns a canonical,
  // so WrittenGlyph/cropUrl resolve to a real form.
  const allItems = useMemo<QuizItem[]>(
    () =>
      quizKeysFromLocked(bboxesByKey, (key) => glyphsByKey[key]?.has_data === true)
        .map((key) => {
          const kg = knownGlyph(key);
          return kg ? { key, kg } : null;
        })
        .filter((x): x is QuizItem => x !== null),
    [bboxesByKey, glyphsByKey],
  );

  const lowerCount = useMemo(() => allItems.filter((i) => i.kg.letterCase === 'lower').length, [allItems]);
  const upperCount = useMemo(() => allItems.filter((i) => i.kg.letterCase === 'upper').length, [allItems]);

  const pool = useMemo(
    () => allItems.filter((i) => caseMode === 'mixed' || i.kg.letterCase === caseMode),
    [allItems, caseMode],
  );

  // Distractors prefer real specimens so every option can overlay its own crop:
  // other locked letters of the SAME case (so the displayed case and the overlaid
  // crop agree), deduped by answer letter. Top up from the bare alphabet (no crop)
  // only when too few letters are locked to supply three.
  const buildChoices = useCallback((item: QuizItem, fromPool: QuizItem[]): Choice[] => {
    const correctLetter = item.kg.answer;
    const correct: Choice = { letter: correctLetter, cropKey: item.key };

    const byLetter = new Map<string, QuizItem>();
    for (const i of fromPool) {
      if (i.kg.letterCase !== item.kg.letterCase || i.kg.answer === correctLetter) continue;
      if (!byLetter.has(i.kg.answer)) byLetter.set(i.kg.answer, i);
    }
    const distractors: Choice[] = shuffle(Array.from(byLetter.values()))
      .slice(0, 3)
      .map((i) => ({ letter: i.kg.answer, cropKey: i.key }));

    if (distractors.length < 3) {
      const used = new Set([correctLetter, ...distractors.map((d) => d.letter)]);
      for (const c of shuffle(ALPHABET.filter((l) => !used.has(l)))) {
        if (distractors.length >= 3) break;
        distractors.push({ letter: c, cropKey: null });
      }
    }

    return shuffle([correct, ...distractors]);
  }, []);

  // Resolve a typed guess to a locked specimen of the same case as the prompt, so
  // a wrong typed answer can overlay the guessed letter's crop too. Null when the
  // guessed letter has no locked form.
  const cropKeyForLetter = useCallback(
    (letter: string, like: KnownGlyph): string | null =>
      allItems.find((i) => i.kg.answer === letter && i.kg.letterCase === like.letterCase)?.key ?? null,
    [allItems],
  );

  const nextQuestion = useCallback(
    (fromPool: QuizItem[], excludeKey?: string) => {
      if (fromPool.length === 0) {
        setCurrent(null);
        return;
      }
      let pick = sample(fromPool);
      // Avoid an immediate repeat when there's something else to show.
      if (fromPool.length > 1 && excludeKey) {
        let guard = 0;
        while (pick.key === excludeKey && guard < 12) {
          pick = sample(fromPool);
          guard += 1;
        }
      }
      setCurrent(pick);
      setQNonce((n) => n + 1);
      setChoices(buildChoices(pick, fromPool));
      setInput('');
      setVerdict('idle');
      setPicked(null);
    },
    [buildChoices],
  );

  const start = useCallback(() => {
    clearAdvance();
    setStats({ correct: 0, seen: 0, streak: 0, bestStreak: 0 });
    setMisses({});
    setConfusions({});
    // A fresh session starts back on the written form regardless of how the
    // previous run ended up toggled.
    setView('written');
    setFinished(false);
    setStarted(true);
    nextQuestion(pool);
  }, [pool, nextQuestion, clearAdvance]);

  const advance = useCallback(() => {
    // Defensive: a manual advance cancels any pending auto-advance so the two
    // can never stack into a double skip.
    clearAdvance();
    nextQuestion(pool, current?.key);
  }, [pool, current, nextQuestion, clearAdvance]);

  // Advance after a pause so the green "Super Übereinstimmung" overlay (which
  // fades in over ~320ms) stays on screen long enough to register; cancels any
  // previous pending advance first.
  const scheduleAdvance = useCallback(() => {
    clearAdvance();
    advanceTimer.current = window.setTimeout(() => {
      advanceTimer.current = null;
      advance();
    }, 1150);
  }, [clearAdvance, advance]);

  // End the session: show the results screen if anything was answered, otherwise
  // drop straight back to setup (nothing to report). Either way, cancel a
  // pending advance so it can't change the question after we leave the drill.
  const finish = useCallback(() => {
    clearAdvance();
    if (stats.seen > 0) setFinished(true);
    else setStarted(false);
  }, [stats.seen, clearAdvance]);

  // Back from the results screen to the setup card.
  const backToSetup = useCallback(() => {
    setStarted(false);
    setFinished(false);
  }, []);

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

  // Tally a miss for the shown glyph, plus the specific confusion when the
  // learner offered a concrete (single-letter) wrong guess.
  const recordMiss = useCallback((kg: KnownGlyph, guess?: string) => {
    setMisses((m) => ({ ...m, [kg.glyph]: (m[kg.glyph] ?? 0) + 1 }));
    if (guess && /^[a-z]$/.test(guess) && guess !== kg.answer) {
      const key = `${kg.glyph}${CONFUSION_SEP}${inCase(guess, kg)}`;
      setConfusions((c) => ({ ...c, [key]: (c[key] ?? 0) + 1 }));
    }
  }, []);

  const submitTyped = useCallback(() => {
    // One-shot: only an unanswered question accepts a submit. The first guess is
    // final — wrong reveals the solution and waits for "Weiter".
    if (!current || verdict !== 'idle') return;
    const guess = input.trim().toLowerCase();
    if (!guess) return;
    if (guess === current.kg.answer) {
      markResult(true);
      setVerdict('correct');
      scheduleAdvance();
    } else {
      // Wrong → reveal immediately and overlay the guessed letter's crop (when
      // it has a locked specimen) over the prompt.
      setPicked({ letter: guess, cropKey: cropKeyForLetter(guess, current.kg) });
      recordMiss(current.kg, guess);
      markResult(false);
      setVerdict('wrong');
    }
  }, [current, input, verdict, markResult, recordMiss, scheduleAdvance, cropKeyForLetter]);

  const pickChoice = useCallback(
    (choice: Choice) => {
      // One-shot: the first pick is final. Guard against a late double-count.
      if (!current || verdict !== 'idle') return;
      setPicked(choice);
      if (choice.letter === current.kg.answer) {
        markResult(true);
        setVerdict('correct');
        scheduleAdvance();
      } else {
        recordMiss(current.kg, choice.letter);
        markResult(false);
        setVerdict('wrong');
      }
    },
    [current, verdict, markResult, recordMiss, scheduleAdvance],
  );

  const reveal = useCallback(() => {
    if (!current) return;
    recordMiss(current.kg);
    markResult(false);
    setVerdict('revealed');
  }, [current, markResult, recordMiss]);

  // Whether the current glyph has a traced canonical, so the play panel can
  // render it "as written" (animated ductus) instead of the static crop.
  const hasDuctus = current ? glyphsByKey[current.key]?.has_data === true : false;

  return {
    // setup state
    script,
    setScript,
    mode,
    setMode,
    caseMode,
    setCaseMode,
    answerMode,
    setAnswerMode,
    difficulty,
    setDifficulty,
    lowerCount,
    upperCount,
    poolSize: pool.length,
    // session state
    started,
    finished,
    // per-question state
    current,
    hasDuctus,
    qNonce,
    view,
    setView,
    choices,
    input,
    setInput,
    verdict,
    picked,
    // session tallies
    stats,
    misses,
    confusions,
    // actions
    start,
    advance,
    finish,
    backToSetup,
    submitTyped,
    pickChoice,
    reveal,
  };
}
