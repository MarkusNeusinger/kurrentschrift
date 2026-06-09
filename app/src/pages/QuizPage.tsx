// QuizPage — public reading drill (`/quiz`). Shows a real letter crop from the
// source chart and asks the learner which Latin letter it is. Deliberately
// simple for now: it consumes whatever bboxes have been marked (via the admin
// chart editor) and maps each glyph_key back to its `answer` letter, so the
// vocabulary grows as letters get marked. The richer version (animated ductus
// playback, whole words, orthography-rule explanations on a miss) is the P1
// Lese-Cluster work — see docs/concepts/vision.md §4 and mvp-roadmap.md.
//
// Ending a session ("beenden") opens a results screen that surfaces which
// letters were missed most and which ones the learner tends to confuse, so the
// drill turns into targeted feedback rather than an endless stream.

import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import HighlightOffIcon from '@mui/icons-material/HighlightOff';
import ReplayIcon from '@mui/icons-material/Replay';
import TuneIcon from '@mui/icons-material/Tune';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  Divider,
  LinearProgress,
  Paper,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { cropUrl } from '../api';
import { PaperBackground } from '../components/PaperBackground';
import { PublicHeader } from '../components/PublicHeader';
import { WrittenGlyph } from '../components/WrittenGlyph';
import { DIFFICULTIES, knownGlyph, SCRIPTS, type Difficulty, type KnownGlyph } from '../constants';
import { useAdmin } from '../state';

const garamond = "'EB Garamond', Georgia, 'Times New Roman', serif";

type CaseMode = 'lower' | 'upper' | 'mixed';
type AnswerMode = 'type' | 'choice';

interface QuizItem {
  key: string;
  kg: KnownGlyph;
}

// Per-letter miss counts (keyed by the rendered glyph the learner saw, e.g. `ſ`)
// and confusion tallies (keyed `seen→guessed`). Both accumulate across a session
// and feed the end screen.
type MissMap = Record<string, number>;
type ConfusionMap = Record<string, number>;

const CONFUSION_SEP = '→';

const ALPHABET = Array.from({ length: 26 }, (_, i) => String.fromCharCode(97 + i));

const sample = <T,>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];

// Display the option/solution in the case of the shown glyph so the prompt and
// the answer read consistently (a Versal crop → uppercase label).
const inCase = (letter: string, kg: KnownGlyph): string =>
  kg.letterCase === 'upper' ? letter.toUpperCase() : letter;

// Pick the crop for a question. Difficulty is threaded in already: once messier
// handwriting sources land in the DB, this is the single place that branches on
// it to pull a less-clean hand instead of the clean Loth plate. Today every
// level resolves to the same Loth crop (rough levels are disabled in setup).
const questionCropUrl = (key: string, _difficulty: Difficulty): string => cropUrl(key);

export function QuizPage() {
  const { source, bboxesByKey, glyphsByKey, loadError, waking } = useAdmin();

  const [script, setScript] = useState('kurrent');
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

  const inputRef = useRef<HTMLInputElement | null>(null);

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
  const allItems = useMemo<QuizItem[]>(
    () =>
      Object.entries(bboxesByKey)
        .filter(([, b]) => b.locked)
        .map(([key]) => {
          const kg = knownGlyph(key);
          return kg ? { key, kg } : null;
        })
        .filter((x): x is QuizItem => x !== null),
    [bboxesByKey],
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
    nextQuestion(pool, current?.key);
  }, [pool, current, nextQuestion]);

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

  // Cancel a pending advance on unmount.
  useEffect(() => clearAdvance, [clearAdvance]);

  // Keep the typing field focused for a fast keyboard loop.
  useEffect(() => {
    if (started && !finished && answerMode === 'type' && verdict !== 'correct') inputRef.current?.focus();
  }, [started, finished, answerMode, current, verdict]);

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

  // ---- render helpers ----------------------------------------------------

  if (loadError) {
    return (
      <CenterPage>
        <Typography variant="h6" gutterBottom>
          Vorlage nicht erreichbar
        </Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          {loadError}
        </Typography>
        <Button variant="outlined" onClick={() => window.location.reload()}>
          Erneut versuchen
        </Button>
      </CenterPage>
    );
  }

  if (!source) {
    return (
      <CenterPage>
        <CircularProgress />
        <Typography color="text.secondary" sx={{ mt: 2 }}>
          {waking ? 'Vorlage startet (Cold Start), einen Moment…' : 'lade Vorlage…'}
        </Typography>
      </CenterPage>
    );
  }

  return (
    <PaperBackground>
      <PublicHeader tone="paper" />
      <Container maxWidth="sm" sx={{ py: { xs: 4, sm: 6 } }}>
        <Stack spacing={3}>
          <Typography component="h1" sx={{ fontFamily: garamond, fontStyle: 'italic', fontSize: '2rem', lineHeight: 1.1 }}>
            Buchstaben-Quiz
          </Typography>

          {!started ? (
            <SetupPanel
              script={script}
              setScript={setScript}
              caseMode={caseMode}
              setCaseMode={setCaseMode}
              answerMode={answerMode}
              setAnswerMode={setAnswerMode}
              difficulty={difficulty}
              setDifficulty={setDifficulty}
              lowerCount={lowerCount}
              upperCount={upperCount}
              poolSize={pool.length}
              onStart={start}
            />
          ) : finished ? (
            <ResultsPanel
              stats={stats}
              misses={misses}
              confusions={confusions}
              onReplay={start}
              onSetup={() => {
                setStarted(false);
                setFinished(false);
              }}
            />
          ) : (
            <PlayPanel
              current={current}
              hasDuctus={current ? glyphsByKey[current.key] != null : false}
              qNonce={qNonce}
              choices={choices}
              input={input}
              setInput={setInput}
              verdict={verdict}
              wrongChoices={wrongChoices}
              answerMode={answerMode}
              difficulty={difficulty}
              stats={stats}
              inputRef={inputRef}
              onSubmitTyped={submitTyped}
              onPickChoice={pickChoice}
              onReveal={reveal}
              onAdvance={advance}
              onQuit={finish}
            />
          )}
        </Stack>
      </Container>
    </PaperBackground>
  );
}

// --- subcomponents --------------------------------------------------------

function CenterPage({ children }: { children: React.ReactNode }) {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: 'background.default',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        p: 4,
      }}
    >
      {children}
    </Box>
  );
}

// The quiz prompt: the glyph "as written" (animated ductus) when it has a traced
// canonical, else the static Loth crop. If the written render reports no canonical
// (a 404 race), it falls back to the crop for this question.
function QuestionVisual({
  item,
  hasDuctus,
  qNonce,
  difficulty,
  verdict,
}: {
  item: QuizItem;
  hasDuctus: boolean;
  qNonce: number;
  difficulty: Difficulty;
  verdict: 'idle' | 'correct' | 'wrong' | 'revealed';
}) {
  const [fellBack, setFellBack] = useState(false);
  // Reset the fallback whenever the question changes.
  useEffect(() => setFellBack(false), [item.key, qNonce]);
  const showWritten = hasDuctus && !fellBack;

  return (
    <Paper
      variant="outlined"
      sx={{
        p: 2,
        minHeight: 200,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: '#fff',
        borderColor: verdict === 'correct' ? 'success.main' : verdict === 'wrong' ? 'error.main' : 'divider',
        transition: 'border-color 120ms',
      }}
    >
      {showWritten ? (
        <WrittenGlyph
          key={`${item.key}-${qNonce}`}
          glyphKey={item.key}
          height={220}
          onUnavailable={() => setFellBack(true)}
        />
      ) : (
        <Box
          component="img"
          src={questionCropUrl(item.key, difficulty)}
          alt="Kurrent-Buchstabe"
          sx={{ maxWidth: '100%', maxHeight: 260, objectFit: 'contain', userSelect: 'none' }}
          draggable={false}
        />
      )}
    </Paper>
  );
}

interface SetupProps {
  script: string;
  setScript: (s: string) => void;
  caseMode: CaseMode;
  setCaseMode: (c: CaseMode) => void;
  answerMode: AnswerMode;
  setAnswerMode: (a: AnswerMode) => void;
  difficulty: Difficulty;
  setDifficulty: (d: Difficulty) => void;
  lowerCount: number;
  upperCount: number;
  poolSize: number;
  onStart: () => void;
}

function SetupPanel(p: SetupProps) {
  const noLetters = p.poolSize === 0;
  return (
    <Paper variant="outlined" sx={{ p: 3 }}>
      <Stack spacing={3}>
        <Typography color="text.secondary" sx={{ lineHeight: 1.7 }}>
          Erkenne die Kurrent-Buchstaben: Jeder Buchstabe wird dir Zug um Zug geschrieben — in der Reihenfolge der Feder —
          und du tippst (oder wählst), welcher es ist. Richtig → weiter, falsch → noch einmal. Am Ende zeigt dir die
          Auswertung, welche Buchstaben dir schwerfielen.
        </Typography>

        <Field label="Schrift">
          <ToggleButtonGroup
            size="small"
            exclusive
            value={p.script}
            onChange={(_e, v: string | null) => v && p.setScript(v)}
          >
            {SCRIPTS.map((s) => (
              <ToggleButton key={s.id} value={s.id} disabled={!s.available}>
                {s.label}
                {!s.available && (
                  <Typography component="span" variant="caption" sx={{ ml: 0.75, color: 'text.disabled' }}>
                    bald
                  </Typography>
                )}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Field>

        <Field label="Buchstaben">
          <ToggleButtonGroup
            size="small"
            exclusive
            value={p.caseMode}
            onChange={(_e, v: CaseMode | null) => v && p.setCaseMode(v)}
          >
            <ToggleButton value="lower">Klein ({p.lowerCount})</ToggleButton>
            <ToggleButton value="upper">Groß ({p.upperCount})</ToggleButton>
            <ToggleButton value="mixed">Gemischt</ToggleButton>
          </ToggleButtonGroup>
        </Field>

        <Field label="Antwort">
          <ToggleButtonGroup
            size="small"
            exclusive
            value={p.answerMode}
            onChange={(_e, v: AnswerMode | null) => v && p.setAnswerMode(v)}
          >
            <ToggleButton value="type">Tippen</ToggleButton>
            <ToggleButton value="choice">Auswahl (Multiple Choice)</ToggleButton>
          </ToggleButtonGroup>
        </Field>

        <Field label="Schwierigkeit">
          <ToggleButtonGroup
            size="small"
            exclusive
            value={p.difficulty}
            onChange={(_e, v: Difficulty | null) => v && p.setDifficulty(v)}
          >
            {DIFFICULTIES.map((d) => (
              <ToggleButton key={d.id} value={d.id} disabled={!d.available}>
                {d.label}
                {!d.available && (
                  <Typography component="span" variant="caption" sx={{ ml: 0.75, color: 'text.disabled' }}>
                    bald
                  </Typography>
                )}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.75 }}>
            Höhere Stufen zeigen denselben Buchstaben in unsaubereren Handschriften — sobald solche Vorlagen verfügbar sind.
          </Typography>
        </Field>

        {noLetters ? (
          <Alert severity="info">
            Für diese Auswahl sind noch keine Buchstaben freigegeben.{' '}
            {p.caseMode === 'upper'
              ? 'Großbuchstaben erscheinen hier, sobald sie im Admin-Bereich fertig kalibriert und gesperrt sind.'
              : 'Buchstaben erscheinen hier, sobald sie im Admin-Bereich fertig kalibriert und gesperrt sind.'}
          </Alert>
        ) : (
          <Button variant="contained" size="large" onClick={p.onStart}>
            Quiz starten
          </Button>
        )}
      </Stack>
    </Paper>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <Box>
      <Typography variant="overline" color="text.secondary" sx={{ display: 'block', mb: 0.75 }}>
        {label}
      </Typography>
      {children}
    </Box>
  );
}

interface PlayProps {
  current: QuizItem | null;
  // Whether the shown glyph has a traced canonical, so it can be rendered "as
  // written" (animated ductus) instead of the static crop.
  hasDuctus: boolean;
  // Per-question nonce; remounts the WrittenGlyph so the writing animation replays.
  qNonce: number;
  choices: string[];
  input: string;
  setInput: (s: string) => void;
  verdict: 'idle' | 'correct' | 'wrong' | 'revealed';
  wrongChoices: Set<string>;
  answerMode: AnswerMode;
  difficulty: Difficulty;
  stats: { correct: number; seen: number; streak: number; bestStreak: number };
  inputRef: React.RefObject<HTMLInputElement | null>;
  onSubmitTyped: () => void;
  onPickChoice: (c: string) => void;
  onReveal: () => void;
  onAdvance: () => void;
  onQuit: () => void;
}

function PlayPanel(p: PlayProps) {
  const { current, verdict } = p;
  const solved = verdict === 'correct';
  const showSolution = verdict === 'correct' || verdict === 'revealed';

  if (!current) {
    return (
      <Alert severity="info">
        Keine Buchstaben für diese Auswahl.{' '}
        <Button size="small" onClick={p.onQuit}>
          zurück
        </Button>
      </Alert>
    );
  }

  return (
    <Stack spacing={3}>
      {/* Scoreboard */}
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
        <Chip size="small" label={`Richtig ${p.stats.correct}/${p.stats.seen}`} />
        <Chip size="small" color="primary" variant="outlined" label={`Serie ${p.stats.streak}`} />
        <Box sx={{ flex: 1 }} />
        <Button size="small" color="inherit" sx={{ color: 'text.secondary' }} onClick={p.onQuit}>
          beenden
        </Button>
      </Box>

      {/* The letter — rendered "as written" (animated ductus) when a canonical
          exists, otherwise the static Loth crop. */}
      <QuestionVisual item={current} hasDuctus={p.hasDuctus} qNonce={p.qNonce} difficulty={p.difficulty} verdict={verdict} />

      {/* Solution reveal */}
      {showSolution && (
        <Alert
          icon={solved ? <CheckCircleIcon /> : <HighlightOffIcon />}
          severity={solved ? 'success' : 'warning'}
        >
          Das ist{' '}
          <Box component="span" sx={{ fontWeight: 600 }}>
            {inCase(current.kg.answer, current.kg)}
          </Box>{' '}
          <Box component="span" sx={{ color: 'text.secondary' }}>
            ({current.kg.label})
          </Box>
          {/* When we showed the generated written form, surface the original Loth
              crop so the learner can compare it against the cut-out specimen. */}
          {p.hasDuctus && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
              <Typography variant="caption" color="text.secondary">
                in der Vorlage:
              </Typography>
              <Box
                component="img"
                src={cropUrl(current.key)}
                alt="Loth-Vorlage"
                sx={{ height: 56, maxWidth: 120, objectFit: 'contain', bgcolor: '#fff', borderRadius: 0.5, p: 0.25 }}
                draggable={false}
              />
            </Box>
          )}
        </Alert>
      )}

      {verdict === 'wrong' && (
        <Alert severity="error" sx={{ py: 0.25 }}>
          Nicht richtig — versuch es nochmal.
        </Alert>
      )}

      {/* Answer controls */}
      {p.answerMode === 'type' ? (
        <Stack direction="row" spacing={1}>
          <TextField
            inputRef={p.inputRef}
            value={p.input}
            onChange={(e) => p.setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') p.onSubmitTyped();
            }}
            placeholder="Welcher Buchstabe?"
            disabled={showSolution}
            autoComplete="off"
            slotProps={{ htmlInput: { maxLength: 2, style: { textTransform: 'lowercase' } } }}
            fullWidth
          />
          <Button variant="contained" onClick={p.onSubmitTyped} disabled={showSolution || !p.input.trim()}>
            Prüfen
          </Button>
        </Stack>
      ) : (
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
          {p.choices.map((c) => {
            const isWrong = p.wrongChoices.has(c);
            // Highlight the right answer green whether the learner got it or
            // revealed it.
            const isCorrect = showSolution && c === current.kg.answer;
            return (
              <Button
                key={c}
                variant={isCorrect ? 'contained' : 'outlined'}
                color={isCorrect ? 'success' : isWrong ? 'error' : 'primary'}
                disabled={isWrong || showSolution}
                onClick={() => p.onPickChoice(c)}
                sx={{ py: 1.25, fontSize: '1.05rem' }}
              >
                {inCase(c, current.kg)}
              </Button>
            );
          })}
        </Box>
      )}

      {/* Reveal / skip */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {showSolution ? (
          <Tooltip title="Nächster Buchstabe">
            <Button endIcon={<ArrowForwardIcon />} onClick={p.onAdvance}>
              Weiter
            </Button>
          </Tooltip>
        ) : (
          <Button size="small" color="inherit" sx={{ color: 'text.secondary' }} onClick={p.onReveal}>
            Lösung zeigen
          </Button>
        )}
      </Box>
    </Stack>
  );
}

interface ResultsProps {
  stats: { correct: number; seen: number; streak: number; bestStreak: number };
  misses: MissMap;
  confusions: ConfusionMap;
  onReplay: () => void;
  onSetup: () => void;
}

function ResultsPanel(p: ResultsProps) {
  const pct = p.stats.seen > 0 ? Math.round((p.stats.correct / p.stats.seen) * 100) : 0;

  // Worst letters first; cap the list so the screen stays scannable.
  const topMisses = useMemo(
    () =>
      Object.entries(p.misses)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 6),
    [p.misses],
  );
  const maxMiss = topMisses.length ? topMisses[0][1] : 0;

  const topConfusions = useMemo(
    () =>
      Object.entries(p.confusions)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([key, count]) => {
          const [seen, guessed] = key.split(CONFUSION_SEP);
          return { seen, guessed, count };
        }),
    [p.confusions],
  );

  return (
    <Paper variant="outlined" sx={{ p: 3 }}>
      <Stack spacing={3}>
        <Box>
          <Typography variant="overline" color="text.secondary">
            Auswertung
          </Typography>
          <Typography sx={{ fontFamily: garamond, fontSize: '1.75rem', lineHeight: 1.2 }}>
            {p.stats.correct} von {p.stats.seen} richtig
          </Typography>
          <LinearProgress
            variant="determinate"
            value={pct}
            color={pct >= 80 ? 'success' : pct >= 50 ? 'primary' : 'warning'}
            sx={{ mt: 1.5, height: 8, borderRadius: 4 }}
          />
          <Box sx={{ display: 'flex', gap: 1, mt: 1.5, flexWrap: 'wrap' }}>
            <Chip size="small" label={`${pct}% Trefferquote`} />
            <Chip size="small" variant="outlined" color="primary" label={`Beste Serie ${p.stats.bestStreak}`} />
          </Box>
        </Box>

        <Divider />

        {/* Letters that were missed most */}
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Diese Buchstaben fielen schwer
          </Typography>
          {topMisses.length === 0 ? (
            <Alert severity="success" icon={<CheckCircleIcon />} sx={{ py: 0.5 }}>
              Kein einziger Fehler — sauber gelesen!
            </Alert>
          ) : (
            <Stack spacing={1}>
              {topMisses.map(([glyph, count]) => (
                <Box key={glyph} sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Box
                    sx={{
                      fontFamily: garamond,
                      fontSize: '1.6rem',
                      width: 36,
                      textAlign: 'center',
                      flexShrink: 0,
                    }}
                  >
                    {glyph}
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <Box
                      sx={{
                        height: 10,
                        borderRadius: 5,
                        bgcolor: 'error.main',
                        opacity: 0.85,
                        width: `${maxMiss ? Math.max(8, (count / maxMiss) * 100) : 0}%`,
                        transition: 'width 200ms',
                      }}
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ width: 64, textAlign: 'right' }}>
                    {count}× falsch
                  </Typography>
                </Box>
              ))}
            </Stack>
          )}
        </Box>

        {/* Confusion pairs */}
        {topConfusions.length > 0 && (
          <>
            <Divider />
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Häufig verwechselt
              </Typography>
              <Stack spacing={1}>
                {topConfusions.map(({ seen, guessed, count }) => (
                  <Box key={`${seen}${CONFUSION_SEP}${guessed}`} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box component="span" sx={{ fontFamily: garamond, fontSize: '1.4rem' }}>
                      {seen}
                    </Box>
                    <Typography component="span" color="text.secondary">
                      für
                    </Typography>
                    <Box component="span" sx={{ fontFamily: garamond, fontSize: '1.4rem' }}>
                      {guessed}
                    </Box>
                    <Typography component="span" color="text.secondary">
                      gehalten
                    </Typography>
                    <Box sx={{ flex: 1 }} />
                    <Chip size="small" variant="outlined" label={`${count}×`} />
                  </Box>
                ))}
              </Stack>
            </Box>
          </>
        )}

        <Divider />

        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
          <Button variant="contained" startIcon={<ReplayIcon />} onClick={p.onReplay} fullWidth>
            Nochmal
          </Button>
          <Button variant="outlined" startIcon={<TuneIcon />} onClick={p.onSetup} fullWidth>
            Einstellungen
          </Button>
        </Stack>
      </Stack>
    </Paper>
  );
}
