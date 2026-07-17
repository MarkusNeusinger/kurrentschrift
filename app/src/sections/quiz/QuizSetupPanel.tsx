// QuizSetupPanel — the pre-session setup: three hairline-separated choice rows
// (Schrift · Aufgabe · Schwierigkeit), a one-line summary and the start CTA. No
// boxed "Kasten" any more — the rows sit straight on the page (design handoff
// "Tinte & Vergleich"). Purely presentational; state comes from useQuizEngine.

import { Alert, Box, Stack, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import type { ReactNode } from 'react';

import { InfoHint } from '@/components/InfoHint';
import { de } from '@/locales';
import { DIFFICULTIES, MODES, SCRIPTS, type Difficulty } from '@/sections/quiz/quizTypes';
import { InkButton, OptionChip } from '@/sections/quiz/quizUi';
import { type QuizMode } from '@/sections/quiz/useQuizEngine';
import { display, garamond, paper } from '@/styles/paper';

interface SetupProps {
  script: string;
  setScript: (s: string) => void;
  mode: QuizMode;
  setMode: (m: QuizMode) => void;
  difficulty: Difficulty;
  setDifficulty: (d: Difficulty) => void;
  poolSize: number;
  onStart: () => void;
}

export function QuizSetupPanel(p: SetupProps) {
  const empty = p.poolSize === 0;

  const scriptLabel = SCRIPTS.find((s) => s.id === p.script)?.label ?? p.script;
  const modeLabel = p.mode === 'words' ? de.quiz.setup.modeWords : de.quiz.setup.modeLetters;
  const difficultyLabel = DIFFICULTIES.find((d) => d.id === p.difficulty)?.label ?? p.difficulty;

  return (
    <Stack spacing={0}>
      <Row label={de.quiz.setup.scriptLabel} hint={de.quiz.setup.scriptHint}>
        {SCRIPTS.map((s) => (
          <OptionChip
            key={s.id}
            selected={p.script === s.id}
            disabled={!s.available}
            soon={!s.available}
            soonLabel={de.common.soon}
            onClick={() => p.setScript(s.id)}
          >
            {s.label}
          </OptionChip>
        ))}
      </Row>

      <Row label={de.quiz.setup.taskLabel} hint={de.quiz.setup.taskHint}>
        {MODES.map((m) => (
          <OptionChip
            key={m.id}
            selected={p.mode === m.id}
            disabled={!m.available}
            soon={!m.available}
            soonLabel={de.common.soon}
            onClick={() => p.setMode(m.id)}
          >
            {m.label}
          </OptionChip>
        ))}
      </Row>

      <Row
        label={de.quiz.setup.difficultyLabel}
        hint={de.quiz.setup.difficultyShortHint}
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
        {DIFFICULTIES.map((d) => (
          <OptionChip
            key={d.id}
            selected={p.difficulty === d.id}
            disabled={!d.available}
            soon={!d.available}
            soonLabel={de.common.soon}
            onClick={() => p.setDifficulty(d.id)}
          >
            {d.label}
          </OptionChip>
        ))}
      </Row>

      {/* Summary + start */}
      <Box sx={{ borderTop: `1px solid ${alpha(paper.line, 0.5)}`, pt: { xs: 2.5, sm: 3 }, mt: { xs: 0.5, sm: 1 } }}>
        {empty ? (
          <Alert severity="info">
            {p.mode === 'words'
              ? `${de.quiz.setup.noWords} ${de.quiz.setup.noWordsOther}`
              : `${de.quiz.setup.noLetters} ${de.quiz.setup.noLettersOther}`}
          </Alert>
        ) : (
          <Stack spacing={2} sx={{ alignItems: 'flex-start' }}>
            <Typography sx={{ fontFamily: garamond, fontSize: 16, color: paper.sepia }}>
              {de.quiz.setup.summaryPrefix} ·{' '}
              <Box component="span" sx={{ color: paper.ink, fontWeight: 600 }}>
                {scriptLabel} · {modeLabel} · {difficultyLabel}
              </Box>
            </Typography>
            <InkButton onClick={p.onStart}>{de.quiz.setup.start} →</InkButton>
          </Stack>
        )}
        {/* Provenance line — the quiz names its source like the Tafel and the
            Federprobe do (their italic sepia caption pattern, kept minimal). */}
        <Typography variant="caption" component="p" sx={{ color: paper.sepia, fontStyle: 'italic', mt: 3 }}>
          {de.quiz.setup.sourceNote}
        </Typography>
      </Box>
    </Stack>
  );
}

function Row({
  label,
  hint,
  info,
  children,
}: {
  label: string;
  hint: string;
  info?: ReactNode;
  children: ReactNode;
}) {
  return (
    <Box
      sx={{
        borderTop: `1px solid ${alpha(paper.line, 0.5)}`,
        py: { xs: 2, sm: 2.75 },
        display: 'flex',
        flexDirection: { xs: 'column', sm: 'row' },
        gap: { xs: 1.5, sm: 3 },
        alignItems: { sm: 'center' },
      }}
    >
      <Box sx={{ width: { sm: 210 }, flexShrink: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Typography sx={{ fontFamily: display, fontWeight: 600, fontSize: { xs: 16.5, sm: 18 }, color: paper.ink }}>
            {label}
          </Typography>
          {info}
        </Box>
        <Typography sx={{ fontFamily: garamond, fontSize: { xs: 13, sm: 13.5 }, color: paper.sepia, mt: 0.25 }}>
          {hint}
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>{children}</Box>
    </Box>
  );
}
