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

export interface QuizItem {
  key: string;
  kg: KnownGlyph;
}

// Per-letter miss counts (keyed by the rendered glyph the learner saw, e.g. `ſ`)
// and confusion tallies (keyed `seen→guessed`). Both accumulate across a session
// and feed the end screen.
export type MissMap = Record<string, number>;
export type ConfusionMap = Record<string, number>;

export const CONFUSION_SEP = '→';

const ALPHABET = Array.from({ length: 26 }, (_, i) => String.fromCharCode(97 + i));

const sample = <T,>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];

// Display the option/solution in the case of the shown glyph so the prompt and
// the answer read consistently (a Versal crop → uppercase label).
export const inCase = (letter: string, kg: KnownGlyph): string =>
  kg.letterCase === 'upper' ? letter.toUpperCase() : letter;

export function useQuizEngine() {
  const { bboxesByKey, glyphsByKey } = useAdmin();

  const [script, setScript] = useState('suetterlin');
  const [caseMode, setCaseMode] = useState<CaseMode>('lower');
  const [answerMode, setAnswerMode] = useState<AnswerMode>('type');
  const [difficulty, setDifficulty] = useState<Difficulty>('clean');
  const [started, setStarted] = useState(false);
  const [finished, setFinished] = useState(false);

  const [current, setCurrent] = useState<QuizItem | null>(null);
  // Bumped on every new question so the WrittenGlyph remounts and replays its
  // writing animation even when the same letter happens to come up again.
  const [qNonce, setQNonce] = useState(0);
  const [choices, setChoices] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [verdict, setVerdict] = useState<'idle' | 'correct' | 'wrong' | 'revealed'>('idle');
  const [wrongChoices, setWrongChoices] = useState<Set<string>>(new Set());
  const [stats, setStats] = useState({ correct: 0, seen: 0, streak: 0, bestStreak: 0 });
  const [misses, setMisses] = useState<MissMap>({});
  const [confusions, setConfusions] = useState<ConfusionMap>({});

  // Whether the current question has already been answered wrong at least once.
  // A question only counts as "correct" in the tally if it was solved on the
  // first attempt — otherwise a wrong-then-right run would inflate the score and
  // contradict the per-letter miss breakdown shown on the results screen.
  const missedCurrent = useRef(false);

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

  const buildChoices = useCallback((item: QuizItem): string[] => {
    const correct = item.kg.answer;
    const distractors = ALPHABET.filter((c) => c !== correct);
    const picked: string[] = [];
    while (picked.length < 3 && distractors.length) {
      const idx = Math.floor(Math.random() * distractors.length);
      picked.push(distractors.splice(idx, 1)[0]);
    }
    return [correct, ...picked].sort(() => Math.random() - 0.5);
  }, []);

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
      setChoices(buildChoices(pick));
      setInput('');
      setVerdict('idle');
      setWrongChoices(new Set());
      missedCurrent.current = false;
    },
    [buildChoices],
  );

  const start = useCallback(() => {
    clearAdvance();
    setStats({ correct: 0, seen: 0, streak: 0, bestStreak: 0 });
    setMisses({});
    setConfusions({});
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

  // Advance after a short pause so the green "correct" state stays visible;
  // cancels any previous pending advance first.
  const scheduleAdvance = useCallback(() => {
    clearAdvance();
    advanceTimer.current = window.setTimeout(() => {
      advanceTimer.current = null;
      advance();
    }, 650);
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
    // 'correct' and 'revealed' are both terminal for the current question — a
    // late submit must not mark (and double-count) it again.
    if (!current || verdict === 'correct' || verdict === 'revealed') return;
    const guess = input.trim().toLowerCase();
    if (!guess) return;
    if (guess === current.kg.answer) {
      // Right only counts toward the score if no earlier attempt missed it.
      markResult(!missedCurrent.current);
      setVerdict('correct');
      scheduleAdvance();
    } else {
      // Wrong → it does NOT advance; the same letter stays for another try.
      missedCurrent.current = true;
      recordMiss(current.kg, guess);
      setStats((s) => ({ ...s, streak: 0 }));
      setVerdict('wrong');
      setInput('');
    }
  }, [current, input, verdict, markResult, recordMiss, scheduleAdvance]);

  const pickChoice = useCallback(
    (choice: string) => {
      // Terminal once correct or revealed — guard against a late double-count.
      if (!current || verdict === 'correct' || verdict === 'revealed') return;
      if (choice === current.kg.answer) {
        // Right only counts toward the score if no earlier pick missed it.
        markResult(!missedCurrent.current);
        setVerdict('correct');
        scheduleAdvance();
      } else {
        missedCurrent.current = true;
        recordMiss(current.kg, choice);
        setStats((s) => ({ ...s, streak: 0 }));
        setVerdict('wrong');
        setWrongChoices((prev) => new Set(prev).add(choice));
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
    choices,
    input,
    setInput,
    verdict,
    wrongChoices,
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
