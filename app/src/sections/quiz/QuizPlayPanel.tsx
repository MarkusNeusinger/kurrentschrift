// QuizPlayPanel — the running drill: scoreboard, the question visual, the
// typed-input field or multiple-choice buttons, the solution reveal and the
// weiter/Lösung-zeigen actions. All quiz state and verdict logic comes from
// useQuizEngine via props; the panel only owns the input element itself
// (ref + auto-focus).

import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import HighlightOffIcon from '@mui/icons-material/HighlightOff';
import { Alert, Box, Button, Chip, Stack, TextField, Tooltip } from '@mui/material';
import { useEffect, useRef } from 'react';

import { de, fmt } from '@/locales';
import { QuestionVisual } from '@/sections/quiz/QuestionVisual';
import { questionCropUrl, type Difficulty } from '@/sections/quiz/quizTypes';
import { inCase, type AnswerMode, type Choice, type PromptView, type QuizItem } from '@/sections/quiz/useQuizEngine';

interface PlayProps {
  current: QuizItem | null;
  // Whether the shown glyph has a traced canonical, so it can be rendered "as
  // written" (animated ductus) instead of the static crop.
  hasDuctus: boolean;
  // Per-question nonce; remounts the WrittenGlyph so the writing animation replays.
  qNonce: number;
  // Prompt view toggle (Geschrieben/Original), lifted to the engine so it
  // persists across questions.
  view: PromptView;
  setView: (v: PromptView) => void;
  choices: Choice[];
  input: string;
  setInput: (s: string) => void;
  verdict: 'idle' | 'correct' | 'wrong' | 'revealed';
  // The option the learner picked (colours its button, drives the crop overlay).
  picked: Choice | null;
  answerMode: AnswerMode;
  difficulty: Difficulty;
  stats: { correct: number; seen: number; streak: number; bestStreak: number };
  onSubmitTyped: () => void;
  onPickChoice: (c: Choice) => void;
  onReveal: () => void;
  onAdvance: () => void;
  onQuit: () => void;
}

export function QuizPlayPanel(p: PlayProps) {
  const { current, verdict } = p;
  const solved = verdict === 'correct';
  // Every answer is one-shot now, so the solution shows the moment a question is
  // answered (right, wrong or given up).
  const answered = verdict !== 'idle';
  const showSolution = answered;

  const inputRef = useRef<HTMLInputElement | null>(null);

  // Keep the typing field focused for a fast keyboard loop while a question is
  // open. (The panel only renders while a session runs, so no started/finished
  // re-check is needed.)
  useEffect(() => {
    if (p.answerMode === 'type' && verdict === 'idle') inputRef.current?.focus();
  }, [p.answerMode, current, verdict]);

  if (!current) {
    return (
      <Alert severity="info">
        {de.quiz.play.emptyPool}{' '}
        <Button size="small" onClick={p.onQuit}>
          {de.quiz.play.back}
        </Button>
      </Alert>
    );
  }

  // The crop to blend over the prompt once answered: the prompt's own crop on a
  // correct pick (a perfect match), the picked letter's crop on a miss (null when
  // it has no locked specimen — then only the colour wash shows).
  const overlayUrl =
    verdict === 'correct'
      ? questionCropUrl(current.key, p.difficulty)
      : verdict === 'wrong' && p.picked?.cropKey
        ? questionCropUrl(p.picked.cropKey, p.difficulty)
        : null;

  return (
    <Stack spacing={3}>
      {/* Scoreboard */}
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
        <Chip size="small" label={fmt(de.quiz.play.score, { correct: p.stats.correct, seen: p.stats.seen })} />
        <Chip size="small" color="primary" variant="outlined" label={`${de.quiz.play.streak} ${p.stats.streak}`} />
        <Box sx={{ flex: 1 }} />
        <Button size="small" color="inherit" sx={{ color: 'text.secondary' }} onClick={p.onQuit}>
          {de.quiz.play.quit}
        </Button>
      </Box>

      {/* The letter — rendered "as written" (animated ductus) when a canonical
          exists, otherwise the static Loth crop. */}
      <QuestionVisual
        item={current}
        hasDuctus={p.hasDuctus}
        qNonce={p.qNonce}
        view={p.view}
        setView={p.setView}
        difficulty={p.difficulty}
        verdict={verdict}
        overlayUrl={overlayUrl}
      />

      {/* Solution reveal */}
      {showSolution && (
        <Alert
          icon={solved ? <CheckCircleIcon /> : <HighlightOffIcon />}
          severity={solved ? 'success' : 'warning'}
        >
          {de.quiz.play.solutionIs}{' '}
          <Box component="span" sx={{ fontWeight: 600 }}>
            {inCase(current.kg.answer, current.kg)}
          </Box>{' '}
          <Box component="span" sx={{ color: 'text.secondary' }}>
            ({current.kg.label})
          </Box>
        </Alert>
      )}

      {/* Answer controls */}
      {p.answerMode === 'type' ? (
        <Stack direction="row" spacing={1}>
          <TextField
            inputRef={inputRef}
            value={p.input}
            onChange={(e) => p.setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') p.onSubmitTyped();
            }}
            placeholder={de.quiz.play.inputPlaceholder}
            disabled={showSolution}
            autoComplete="off"
            slotProps={{ htmlInput: { maxLength: 2, style: { textTransform: 'lowercase' } } }}
            fullWidth
          />
          <Button variant="contained" onClick={p.onSubmitTyped} disabled={showSolution || !p.input.trim()}>
            {de.quiz.play.check}
          </Button>
        </Stack>
      ) : (
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
          {p.choices.map((c) => {
            const isAnswer = c.letter === current.kg.answer;
            const isPick = p.picked?.letter === c.letter;
            // Once answered: the right option turns green, the learner's wrong
            // pick turns red. Force the colour through the disabled state so the
            // verdict stays legible while the buttons are locked.
            const showCorrect = answered && isAnswer;
            const showWrong = answered && isPick && !isAnswer;
            return (
              <Button
                key={c.letter}
                variant={showCorrect || showWrong ? 'contained' : 'outlined'}
                color={showCorrect ? 'success' : showWrong ? 'error' : 'primary'}
                disabled={answered}
                onClick={() => p.onPickChoice(c)}
                sx={{
                  py: 1.5,
                  fontSize: '1.4rem',
                  fontWeight: 500,
                  ...(showCorrect && {
                    '&.Mui-disabled': { bgcolor: 'success.main', color: 'success.contrastText', opacity: 1 },
                  }),
                  ...(showWrong && {
                    '&.Mui-disabled': { bgcolor: 'error.main', color: 'error.contrastText', opacity: 1 },
                  }),
                }}
              >
                {inCase(c.letter, current.kg)}
              </Button>
            );
          })}
        </Box>
      )}

      {/* Reveal / skip */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {showSolution ? (
          <Tooltip title={de.quiz.play.nextTooltip}>
            <Button endIcon={<ArrowForwardIcon />} onClick={p.onAdvance}>
              {de.quiz.play.next}
            </Button>
          </Tooltip>
        ) : (
          <Button size="small" color="inherit" sx={{ color: 'text.secondary' }} onClick={p.onReveal}>
            {de.quiz.play.reveal}
          </Button>
        )}
      </Box>
    </Stack>
  );
}
