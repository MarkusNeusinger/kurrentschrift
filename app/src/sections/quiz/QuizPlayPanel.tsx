// QuizPlayPanel — the running drill: scoreboard, the question visual, the
// typed-input field or multiple-choice buttons, the solution reveal and the
// weiter/Lösung-zeigen actions. All quiz state and verdict logic comes from
// useQuizEngine via props; the panel only owns the input element itself
// (ref + auto-focus).

import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import HighlightOffIcon from '@mui/icons-material/HighlightOff';
import { Alert, Box, Button, Chip, Stack, TextField, Tooltip, Typography } from '@mui/material';
import { useEffect, useRef } from 'react';

import { CONFIG } from '@/global-config';
import { cropUrl } from '@/lib/api';
import { de, fmt } from '@/locales';
import { QuestionVisual } from '@/sections/quiz/QuestionVisual';
import { type Difficulty } from '@/sections/quiz/quizTypes';
import { inCase, type AnswerMode, type QuizItem } from '@/sections/quiz/useQuizEngine';

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
  onSubmitTyped: () => void;
  onPickChoice: (c: string) => void;
  onReveal: () => void;
  onAdvance: () => void;
  onQuit: () => void;
}

export function QuizPlayPanel(p: PlayProps) {
  const { current, verdict } = p;
  const solved = verdict === 'correct';
  const showSolution = verdict === 'correct' || verdict === 'revealed';

  const inputRef = useRef<HTMLInputElement | null>(null);

  // Keep the typing field focused for a fast keyboard loop. (The panel only
  // renders while a session is running, so started/finished need no re-check.)
  useEffect(() => {
    if (p.answerMode === 'type' && verdict !== 'correct') inputRef.current?.focus();
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
      <QuestionVisual item={current} hasDuctus={p.hasDuctus} qNonce={p.qNonce} difficulty={p.difficulty} verdict={verdict} />

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
          {/* When we showed the generated written form, surface the original Loth
              crop so the learner can compare it against the cut-out specimen. */}
          {p.hasDuctus && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
              <Typography variant="caption" color="text.secondary">
                {de.quiz.play.inSource}
              </Typography>
              <Box
                component="img"
                src={cropUrl(CONFIG.sourceId, current.key)}
                alt={de.quiz.play.sourceCropAlt}
                sx={{ height: 56, maxWidth: 120, objectFit: 'contain', bgcolor: '#fff', borderRadius: 0.5, p: 0.25 }}
                draggable={false}
              />
            </Box>
          )}
        </Alert>
      )}

      {verdict === 'wrong' && (
        <Alert severity="error" sx={{ py: 0.25 }}>
          {de.quiz.play.wrong}
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
