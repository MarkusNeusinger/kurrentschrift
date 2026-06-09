// QuizSetupPanel — the setup card shown before a session starts: script,
// letter-case, answer-mode and difficulty toggles plus the start button. Purely
// presentational; all state comes from useQuizEngine via props.

import { Alert, Box, Button, Paper, Stack, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';

import { DIFFICULTIES, SCRIPTS, type Difficulty } from '@/sections/quiz/quizTypes';
import { type AnswerMode, type CaseMode } from '@/sections/quiz/useQuizEngine';

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

export function QuizSetupPanel(p: SetupProps) {
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
