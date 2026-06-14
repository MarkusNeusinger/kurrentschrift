// QuizView — public reading drill (`/quiz`). Shows a real letter crop from the
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
//
// The view itself is just the shell: boot states, the page chrome and the
// setup → play → results switch. All quiz logic lives in useQuizEngine; the
// three panels are purely presentational.

import { Container, Stack, Typography } from '@mui/material';

import { BootStatus } from '@/components/BootStatus';
import { PaperBackground } from '@/components/PaperBackground';
import { PublicFooter } from '@/components/PublicFooter';
import { PublicHeader } from '@/components/PublicHeader';
import { de } from '@/locales';
import { QuizPlayPanel } from '@/sections/quiz/QuizPlayPanel';
import { QuizResultsPanel } from '@/sections/quiz/QuizResultsPanel';
import { QuizSetupPanel } from '@/sections/quiz/QuizSetupPanel';
import { useQuizEngine } from '@/sections/quiz/useQuizEngine';
import { useAdmin } from '@/context/AdminContext';
import { garamond } from '@/styles/paper';

export function QuizView() {
  const { source, loadError, waking } = useAdmin();
  const quiz = useQuizEngine();

  if (loadError) {
    return (
      <BootStatus
        variant="error"
        title={de.common.boot.sourceUnreachable}
        message={loadError}
        onRetry={() => window.location.reload()}
        retryLabel={de.common.boot.retry}
      />
    );
  }

  if (!source) {
    return (
      <BootStatus
        variant="loading"
        message={waking ? de.common.boot.sourceColdStart : de.common.boot.loadingTemplate}
      />
    );
  }

  return (
    <PaperBackground>
      <PublicHeader tone="paper" />
      <Container maxWidth="sm" sx={{ py: { xs: 4, sm: 6 } }}>
        <Stack spacing={3}>
          <Typography component="h1" sx={{ fontFamily: garamond, fontStyle: 'italic', fontSize: '2rem', lineHeight: 1.1 }}>
            {de.quiz.title}
          </Typography>

          {!quiz.started ? (
            <QuizSetupPanel
              script={quiz.script}
              setScript={quiz.setScript}
              mode={quiz.mode}
              setMode={quiz.setMode}
              caseMode={quiz.caseMode}
              setCaseMode={quiz.setCaseMode}
              answerMode={quiz.answerMode}
              setAnswerMode={quiz.setAnswerMode}
              difficulty={quiz.difficulty}
              setDifficulty={quiz.setDifficulty}
              lowerCount={quiz.lowerCount}
              upperCount={quiz.upperCount}
              poolSize={quiz.poolSize}
              onStart={quiz.start}
            />
          ) : quiz.finished ? (
            <QuizResultsPanel
              stats={quiz.stats}
              misses={quiz.misses}
              confusions={quiz.confusions}
              onReplay={quiz.start}
              onSetup={quiz.backToSetup}
            />
          ) : (
            <QuizPlayPanel
              current={quiz.current}
              hasDuctus={quiz.hasDuctus}
              qNonce={quiz.qNonce}
              view={quiz.view}
              setView={quiz.setView}
              choices={quiz.choices}
              input={quiz.input}
              setInput={quiz.setInput}
              verdict={quiz.verdict}
              picked={quiz.picked}
              answerMode={quiz.answerMode}
              difficulty={quiz.difficulty}
              stats={quiz.stats}
              onSubmitTyped={quiz.submitTyped}
              onPickChoice={quiz.pickChoice}
              onReveal={quiz.reveal}
              onAdvance={quiz.advance}
              onQuit={quiz.finish}
            />
          )}
        </Stack>
      </Container>
      <PublicFooter />
    </PaperBackground>
  );
}
