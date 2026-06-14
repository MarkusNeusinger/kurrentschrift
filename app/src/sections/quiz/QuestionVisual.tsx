// The quiz prompt: the glyph "as written" (animated ductus) or the static Loth
// crop, with a toggle so the learner can switch between the two at will (compare
// the synthesised pen against the real specimen). Defaults to the written form
// when a traced canonical exists, falling back to the crop if the written render
// reports none (a 404 race) or the glyph was never traced.

import { Box, Paper, Stack, ToggleButton, ToggleButtonGroup } from '@mui/material';
import { useEffect, useState } from 'react';

import { WrittenGlyph } from '@/components/WrittenGlyph';
import { de } from '@/locales';
import { questionCropUrl, type Difficulty } from '@/sections/quiz/quizTypes';
import { type QuizItem } from '@/sections/quiz/useQuizEngine';
import { paper } from '@/styles/paper';

type View = 'written' | 'crop';

export function QuestionVisual({
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
  const [view, setView] = useState<View>('written');
  // Reset the fallback and the toggle to the default written view whenever the
  // question changes.
  useEffect(() => {
    setFellBack(false);
    setView('written');
  }, [item.key, qNonce]);

  // The written form is offered only when the glyph has a traced canonical (and
  // the render didn't 404). Otherwise the crop is the only option and the toggle
  // is hidden.
  const canWrite = hasDuctus && !fellBack;
  const showWritten = canWrite && view === 'written';

  return (
    <Stack spacing={1.5} sx={{ alignItems: 'center' }}>
      <Paper
        variant="outlined"
        sx={{
          p: 2,
          width: '100%',
          minHeight: 200,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          // Paper tone rather than stark white — the fresh-ink render and the
          // aged-paper crop both sit on the page's cream ground.
          bgcolor: paper.hi,
          borderColor: verdict === 'correct' ? 'success.main' : verdict === 'wrong' ? 'error.main' : 'divider',
          transition: 'border-color 120ms',
        }}
      >
        {showWritten ? (
          <WrittenGlyph
            key={`${item.key}-${qNonce}`}
            glyphKey={item.key}
            height={220}
            // Inherit the Paper's cream ground instead of the default white box.
            surfaceBg="transparent"
            onUnavailable={() => setFellBack(true)}
          />
        ) : (
          <Box
            component="img"
            src={questionCropUrl(item.key, difficulty)}
            alt={de.quiz.play.cropAlt}
            sx={{ maxWidth: '100%', maxHeight: 260, objectFit: 'contain', userSelect: 'none' }}
            draggable={false}
          />
        )}
      </Paper>

      {canWrite && (
        <ToggleButtonGroup
          size="small"
          exclusive
          value={view}
          onChange={(_, v: View | null) => v && setView(v)}
          aria-label={de.quiz.play.viewToggleAria}
        >
          <ToggleButton value="written">{de.quiz.play.viewWritten}</ToggleButton>
          <ToggleButton value="crop">{de.quiz.play.viewCrop}</ToggleButton>
        </ToggleButtonGroup>
      )}
    </Stack>
  );
}
