// QuizView — public reading drill (`/quiz`). Shows a form of the old German
// cursive (a single glyph or a whole word, written Zug um Zug) and asks the
// learner to read it from four choices. It consumes whatever bboxes have been
// locked + traced in the public Sütterlin source, so the vocabulary grows as
// letters and words become available.
//
// The view itself is just the shell: boot states, the page chrome and the
// setup → play → results switch. All quiz logic lives in useQuizEngine; the
// three panels are purely presentational. The shared page header shows on setup;
// during play and on the results screen the panels carry their own chrome (the
// score band / the Auswertung eyebrow), so the focus stays on the card.

import { Box } from '@mui/material';

import { BootStatus } from '@/components/BootStatus';
import { PageContainer } from '@/components/PageContainer';
import { PageHeader } from '@/components/PageHeader';
import { PublicLayout } from '@/layouts/public/PublicLayout';
import { de } from '@/locales';
import { QuizPlayPanel } from '@/sections/quiz/QuizPlayPanel';
import { QuizResultsPanel } from '@/sections/quiz/QuizResultsPanel';
import { QuizSetupPanel } from '@/sections/quiz/QuizSetupPanel';
import { useQuizEngine } from '@/sections/quiz/useQuizEngine';
import { useAdmin } from '@/context/AdminContext';

export function QuizView() {
  const { source, loadError, waking } = useAdmin();
  const quiz = useQuizEngine();

  // Boot/error states render inside PublicLayout so the header nav and footer
  // stay usable during a cold start instead of vanishing with the page.
  if (loadError) {
    return (
      <PublicLayout footer>
        <BootStatus
          variant="error"
          title={de.common.boot.sourceUnreachable}
          message={loadError}
          onRetry={() => window.location.reload()}
          retryLabel={de.common.boot.retry}
        />
      </PublicLayout>
    );
  }

  if (!source) {
    return (
      <PublicLayout footer>
        <BootStatus
          variant="loading"
          message={waking ? de.common.boot.sourceColdStart : de.common.boot.loadingTemplate}
        />
      </PublicLayout>
    );
  }

  const onSetup = !quiz.started;

  return (
    <PublicLayout footer>
      {/* The content rides the shared `text` column, capped to a compact
          measure so the answer grid doesn't sprawl. On setup it sits flush-left
          so the page header lines up with the other tool pages (/tafel,
          /federprobe); once the drill starts (no header) the flashcards centre
          for focus. */}
      <PageContainer width="text" sx={{ pt: { xs: 4, sm: 6 } }}>
        <Box sx={{ maxWidth: 760, mx: onSetup ? 0 : 'auto' }}>
        {onSetup && (
          <PageHeader eyebrow={de.common.nav.read} title={de.quiz.title}>
            {de.quiz.setup.introLead}
            <Box component="span" sx={{ color: 'text.secondary' }}>
              {de.quiz.setup.introRest}
            </Box>
          </PageHeader>
        )}

        {onSetup ? (
          <QuizSetupPanel
            script={quiz.script}
            setScript={quiz.setScript}
            mode={quiz.mode}
            setMode={quiz.setMode}
            difficulty={quiz.difficulty}
            setDifficulty={quiz.setDifficulty}
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
            qNonce={quiz.qNonce}
            choices={quiz.choices}
            verdict={quiz.verdict}
            picked={quiz.picked}
            difficulty={quiz.difficulty}
            reducedMotion={quiz.reducedMotion}
            stats={quiz.stats}
            onPickChoice={quiz.pickChoice}
            onAdvance={quiz.advance}
            onQuit={quiz.finish}
          />
        )}
        </Box>
      </PageContainer>
    </PublicLayout>
  );
}
