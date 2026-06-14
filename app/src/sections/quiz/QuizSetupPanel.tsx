// QuizSetupPanel — the setup card shown before a session starts: script,
// letter-case, answer-mode and difficulty toggles plus the start button. Purely
// presentational; all state comes from useQuizEngine via props.

import { Alert, Box, Button, Paper, Stack, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';

import { de, fmt } from '@/locales';
import { DIFFICULTIES, MODES, SCRIPTS, type Difficulty } from '@/sections/quiz/quizTypes';
import { type AnswerMode, type CaseMode, type QuizMode } from '@/sections/quiz/useQuizEngine';

interface SetupProps {
  script: string;
  setScript: (s: string) => void;
  mode: QuizMode;
  setMode: (m: QuizMode) => void;
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

export function QuizSetupPanel(p: SetupProps) {
  const noLetters = p.poolSize === 0;
  return (
    <Paper variant="outlined" sx={{ p: 3 }}>
      <Stack spacing={3}>
        <Typography color="text.secondary" sx={{ lineHeight: 1.7 }}>
          {de.quiz.setup.intro}
        </Typography>

        <Field label={de.quiz.setup.scriptLabel}>
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
                    {de.common.soon}
                  </Typography>
                )}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Field>

        <Field label={de.quiz.setup.modeLabel}>
          <ToggleButtonGroup
            size="small"
            exclusive
            value={p.mode}
            onChange={(_e, v: QuizMode | null) => v && p.setMode(v)}
          >
            {MODES.map((m) => (
              <ToggleButton key={m.id} value={m.id} disabled={!m.available}>
                {m.label}
                {!m.available && (
                  <Typography component="span" variant="caption" sx={{ ml: 0.75, color: 'text.disabled' }}>
                    {de.common.soon}
                  </Typography>
                )}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Field>

        <Field label={de.quiz.setup.lettersLabel}>
          <ToggleButtonGroup
            size="small"
            exclusive
            value={p.caseMode}
            onChange={(_e, v: CaseMode | null) => v && p.setCaseMode(v)}
          >
            <ToggleButton value="lower">{fmt(de.quiz.setup.caseLower, { count: p.lowerCount })}</ToggleButton>
            <ToggleButton value="upper">{fmt(de.quiz.setup.caseUpper, { count: p.upperCount })}</ToggleButton>
            <ToggleButton value="mixed">{de.quiz.setup.caseMixed}</ToggleButton>
          </ToggleButtonGroup>
        </Field>

        <Field label={de.quiz.setup.answerLabel}>
          <ToggleButtonGroup
            size="small"
            exclusive
            value={p.answerMode}
            onChange={(_e, v: AnswerMode | null) => v && p.setAnswerMode(v)}
          >
            <ToggleButton value="type">{de.quiz.setup.answerType}</ToggleButton>
            <ToggleButton value="choice">{de.quiz.setup.answerChoice}</ToggleButton>
          </ToggleButtonGroup>
        </Field>

        <Field label={de.quiz.setup.difficultyLabel}>
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
                    {de.common.soon}
                  </Typography>
                )}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.75 }}>
            {de.quiz.setup.difficultyHint}
          </Typography>
        </Field>

        {noLetters ? (
          <Alert severity="info">
            {de.quiz.setup.noLetters}{' '}
            {p.caseMode === 'upper' ? de.quiz.setup.noLettersUpper : de.quiz.setup.noLettersOther}
          </Alert>
        ) : (
          <Button variant="contained" size="large" onClick={p.onStart}>
            {de.quiz.setup.start}
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
