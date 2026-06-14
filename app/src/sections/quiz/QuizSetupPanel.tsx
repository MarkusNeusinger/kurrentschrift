// QuizSetupPanel — the setup card shown before a session starts: script,
// letter-case, answer-mode and difficulty toggles plus the start button. Purely
// presentational; all state comes from useQuizEngine via props.

import { Alert, Box, Button, Paper, Stack, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';

import { InfoHint } from '@/components/InfoHint';
import { de, fmt } from '@/locales';
import { DIFFICULTIES, MODES, SCRIPTS, type Difficulty } from '@/sections/quiz/quizTypes';
import { type AnswerMode, type CaseMode, type QuizMode } from '@/sections/quiz/useQuizEngine';

// Whether whole-word mode is offered yet (still a post-MVP task — shown disabled
// with the "bald" marker until then).
const wordsAvailable = MODES.find((m) => m.id === 'words')?.available ?? false;

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
            exclusive
            sx={{ flexWrap: 'wrap' }}
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

        {/* Combined Modus + Groß-/Kleinschreibung: one compact row. The case
            options (Klein/Groß/Gemischt) and the "Wörter" mode are mutually
            exclusive — picking Wörter is its own task, so there's no separate
            "nur groß" toggle to reconcile. */}
        <Field label={de.quiz.setup.taskLabel}>
          <ToggleButtonGroup
            exclusive
            sx={{ flexWrap: 'wrap' }}
            value={p.mode === 'words' ? 'words' : p.caseMode}
            onChange={(_e, v: CaseMode | 'words' | null) => {
              if (!v) return;
              if (v === 'words') {
                p.setMode('words');
              } else {
                p.setMode('letters');
                p.setCaseMode(v);
              }
            }}
          >
            <ToggleButton value="lower">{fmt(de.quiz.setup.caseLower, { count: p.lowerCount })}</ToggleButton>
            <ToggleButton value="upper">{fmt(de.quiz.setup.caseUpper, { count: p.upperCount })}</ToggleButton>
            <ToggleButton value="mixed">{de.quiz.setup.caseMixed}</ToggleButton>
            <ToggleButton value="words" disabled={!wordsAvailable}>
              {de.quiz.setup.modeWords}
              {!wordsAvailable && (
                <Typography component="span" variant="caption" sx={{ ml: 0.75, color: 'text.disabled' }}>
                  {de.common.soon}
                </Typography>
              )}
            </ToggleButton>
          </ToggleButtonGroup>
        </Field>

        <Field label={de.quiz.setup.answerLabel}>
          <ToggleButtonGroup
            exclusive
            sx={{ flexWrap: 'wrap' }}
            value={p.answerMode}
            onChange={(_e, v: AnswerMode | null) => v && p.setAnswerMode(v)}
          >
            <ToggleButton value="type">{de.quiz.setup.answerType}</ToggleButton>
            <ToggleButton value="choice">{de.quiz.setup.answerChoice}</ToggleButton>
          </ToggleButtonGroup>
        </Field>

        <Field
          label={de.quiz.setup.difficultyLabel}
          info={
            <InfoHint title={de.quiz.setup.difficultyLabel}>
              {DIFFICULTIES.map((d) => (
                <Box key={d.id} sx={{ mb: 0.75 }}>
                  <Box component="span" sx={{ color: 'text.primary', fontWeight: 600 }}>
                    {d.label}
                  </Box>
                  {` — ${d.hint}`}
                </Box>
              ))}
              {de.quiz.setup.difficultyHint}
            </InfoHint>
          }
        >
          <ToggleButtonGroup
            exclusive
            sx={{ flexWrap: 'wrap' }}
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

function Field({ label, info, children }: { label: string; info?: React.ReactNode; children: React.ReactNode }) {
  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25, mb: 0.75 }}>
        <Typography variant="overline" color="text.secondary">
          {label}
        </Typography>
        {info}
      </Box>
      {children}
    </Box>
  );
}
