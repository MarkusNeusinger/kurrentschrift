// QuizPlayPanel — the running drill: a slim score band, the question card, the
// verdict line, the 2×2 answer grid and the advance affordance. All state comes
// from useQuizEngine via props; a correct pick auto-advances (a progress bar
// runs for AUTO_ADVANCE_MS), a wrong pick waits for "Weiter →".

import { Box, Button, ButtonBase, Stack, Typography, keyframes } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useEffect, useRef } from 'react';

import { de, fmt } from '@/locales';
import { QuestionVisual } from '@/sections/quiz/QuestionVisual';
import { InkButton, QuietButton } from '@/sections/quiz/quizUi';
import { type Difficulty } from '@/sections/quiz/quizTypes';
import { AUTO_ADVANCE_MS, inCase, type Choice, type Question, type Verdict } from '@/sections/quiz/useQuizEngine';
import { display, garamond, paper, pigment, quiz, quizRadius } from '@/styles/paper';

const fillBar = keyframes`from { width: 0%; } to { width: 100%; }`;

interface PlayProps {
  current: Question | null;
  qNonce: number;
  choices: Choice[];
  verdict: Verdict;
  picked: Choice | null;
  difficulty: Difficulty;
  reducedMotion: boolean;
  stats: { correct: number; seen: number; streak: number; bestStreak: number };
  onPickChoice: (c: Choice) => void;
  onAdvance: () => void;
  onQuit: () => void;
}

export function QuizPlayPanel(p: PlayProps) {
  const { current, verdict } = p;
  const answered = verdict !== 'idle';

  // After a pick every answer button disables, so keyboard focus would fall
  // back to <body>; move it onto the one actionable control ("Weiter →") — it
  // renders on a wrong pick and, for reduced-motion users, on a correct one
  // too (no auto-advance there). After the advance the buttons re-enable, so
  // focus returns to the answer grid instead of being lost to <body>.
  const advanceRef = useRef<HTMLButtonElement>(null);
  const firstChoiceRef = useRef<HTMLButtonElement>(null);
  const answeredRef = useRef(false);
  useEffect(() => {
    if (verdict !== 'idle') {
      answeredRef.current = true;
      advanceRef.current?.focus();
    }
  }, [verdict]);
  useEffect(() => {
    if (answeredRef.current) {
      answeredRef.current = false;
      firstChoiceRef.current?.focus();
    }
  }, [p.qNonce]);

  if (!current) {
    return (
      <Stack spacing={2} sx={{ alignItems: 'flex-start' }}>
        <Typography color="text.secondary">{de.quiz.play.emptyPool}</Typography>
        <Button onClick={p.onQuit}>{de.quiz.play.back}</Button>
      </Stack>
    );
  }

  const correctValue = current.kind === 'word' ? current.word : current.kg.answer;

  // The verdict / question line under the card.
  let message: React.ReactNode;
  if (verdict === 'correct') {
    // Ladder sizes (h5/h6/body1), Playfair character kept locally; component="p"
    // because the verdict line is a status message, not a document heading.
    message = (
      <Typography component="p" variant="h5" sx={{ fontFamily: display, fontWeight: 600, color: paper.viridianText }}>
        {de.quiz.play.matchStrong}
      </Typography>
    );
  } else if (verdict === 'wrong') {
    const text =
      current.kind === 'word'
        ? fmt(de.quiz.play.solutionWord, { word: current.word })
        : fmt(de.quiz.play.solutionLetter, { letter: inCase(current.kg.answer, current.kg) });
    message = (
      <Typography component="p" variant="h6" sx={{ fontFamily: display, fontWeight: 500, color: pigment.oxblood }}>{text}</Typography>
    );
  } else {
    message = (
      <Typography variant="body1" sx={{ fontFamily: garamond, color: 'text.secondary' }}>
        {current.kind === 'word' ? de.quiz.play.questionWord : de.quiz.play.questionLetter}
      </Typography>
    );
  }

  return (
    <Stack spacing={2.5}>
      {/* Score band */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <ScoreStat label={de.quiz.play.scoreLabel} value={`${p.stats.correct}/${p.stats.seen}`} />
        <Box sx={{ width: '1px', height: 18, bgcolor: paper.line }} />
        <ScoreStat label={de.quiz.play.streakLabel} value={p.stats.streak} />
        <Box sx={{ flex: 1 }} />
        <QuietButton onClick={p.onQuit}>{de.quiz.play.quit}</QuietButton>
      </Box>

      <QuestionVisual
        question={current}
        qNonce={p.qNonce}
        verdict={verdict}
        picked={p.picked}
        difficulty={p.difficulty}
      />

      {/* Verdict / question line — live region so screen readers hear the
          right/wrong verdict without leaving the answer grid */}
      <Box aria-live="polite" sx={{ minHeight: 34, textAlign: 'center' }}>{message}</Box>

      {/* Gloss for a dated/rare word, revealed only after the pick so it never
          gives the answer away. */}
      {answered && current.kind === 'word' && current.note && (
        <Typography
          variant="body2"
          sx={{ mt: -1, textAlign: 'center', fontFamily: garamond, fontStyle: 'italic', color: paper.sepia }}
        >
          {current.note}
        </Typography>
      )}

      {/* Answer grid */}
      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
        {p.choices.map((c, idx) => {
          const isAnswer = c.value === correctValue;
          const isPick = p.picked?.value === c.value;
          const showCorrect = answered && isAnswer;
          const showWrong = answered && isPick && !isAnswer;
          return (
            <ButtonBase
              key={c.value}
              ref={idx === 0 ? firstChoiceRef : undefined}
              disabled={answered}
              onClick={() => p.onPickChoice(c)}
              sx={{
                position: 'relative',
                height: { xs: 58, sm: 64 },
                borderRadius: quizRadius,
                border: '1px solid',
                fontFamily: display,
                fontWeight: 500,
                // Deliberate display sizing: the answer options are letterform
                // specimens scaled to the button, not running text.
                fontSize: current.kind === 'word' ? { xs: 17, sm: 23 } : { xs: 26, sm: 30 },
                transition: 'transform 120ms ease, border-color 120ms ease, box-shadow 120ms ease',
                // Resolved palette first, then the unanswered interactive state.
                ...(answered
                  ? {
                      bgcolor: showCorrect
                        ? alpha(paper.viridian, 0.1)
                        : showWrong
                          ? alpha(pigment.vermilion, 0.1)
                          : quiz.resolvedFace,
                      borderColor: showCorrect ? paper.viridian : showWrong ? pigment.vermilion : 'transparent',
                      color: showCorrect ? paper.ink : showWrong ? pigment.oxblood : quiz.resolvedText,
                      '&.Mui-disabled': {
                        color: showCorrect ? paper.ink : showWrong ? pigment.oxblood : quiz.resolvedText,
                      },
                    }
                  : {
                      bgcolor: quiz.face,
                      borderColor: quiz.border,
                      color: paper.ink,
                      boxShadow: '0 1px 2px rgba(60,40,20,0.05)',
                      '&:hover': {
                        borderColor: paper.viridian,
                        transform: 'translateY(-2px)',
                        boxShadow: '0 4px 12px rgba(60,40,20,0.10)',
                      },
                    }),
              }}
            >
              {c.label}
              {(showCorrect || showWrong) && (
                <Box
                  component="span"
                  aria-hidden
                  sx={{
                    position: 'absolute',
                    top: 5,
                    right: 8,
                    fontSize: 15,
                    fontWeight: 700,
                    color: showCorrect ? paper.viridian : pigment.vermilion,
                  }}
                >
                  {showCorrect ? '✓' : '✕'}
                </Box>
              )}
            </ButtonBase>
          );
        })}
      </Box>

      {/* Advance affordance */}
      <Box sx={{ minHeight: 48, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {verdict === 'correct' && !p.reducedMotion ? (
          <Stack spacing={1} sx={{ width: '100%', alignItems: 'center' }}>
            <Typography variant="caption" sx={{ color: paper.sepia, fontFamily: garamond }}>
              {de.quiz.play.autoNext}
            </Typography>
            <Box sx={{ width: 176, height: 3, borderRadius: 2, bgcolor: alpha(paper.line, 0.42), overflow: 'hidden' }}>
              <Box sx={{ height: '100%', bgcolor: paper.viridian, animation: `${fillBar} ${AUTO_ADVANCE_MS}ms linear forwards` }} />
            </Box>
          </Stack>
        ) : answered ? (
          <InkButton buttonRef={advanceRef} onClick={p.onAdvance}>{de.quiz.play.next} →</InkButton>
        ) : null}
      </Box>
    </Stack>
  );
}

function ScoreStat({ label, value }: { label: string; value: string | number }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.75 }}>
      <Typography
        variant="overline"
        sx={{ color: paper.sepia, textTransform: 'uppercase', letterSpacing: '0.08em', lineHeight: 1 }}
      >
        {label}
      </Typography>
      <Typography component="span" variant="body1" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, lineHeight: 1 }}>
        {value}
      </Typography>
    </Box>
  );
}
