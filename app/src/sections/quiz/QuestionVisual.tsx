// The quiz prompt: the glyph "as written" (animated ductus) or the static Loth
// crop, with a toggle so the learner can switch between the two at will (compare
// the synthesised pen against the real specimen). The chosen view lives in the
// engine, so it persists across questions and only resets when a new session
// starts; the written form is still preferred whenever a traced canonical
// exists, falling back to the crop when the written render reports none (a 404
// race) or the glyph was never traced.

import { Box, Paper, ToggleButton, ToggleButtonGroup } from '@mui/material';
import { useEffect, useState } from 'react';

import { WrittenGlyph } from '@/components/WrittenGlyph';
import { de } from '@/locales';
import { questionCropUrl, type Difficulty } from '@/sections/quiz/quizTypes';
import { type PromptView, type QuizItem } from '@/sections/quiz/useQuizEngine';
import { paper } from '@/styles/paper';

export function QuestionVisual({
  item,
  hasDuctus,
  qNonce,
  view,
  setView,
  difficulty,
  verdict,
}: {
  item: QuizItem;
  hasDuctus: boolean;
  qNonce: number;
  view: PromptView;
  setView: (v: PromptView) => void;
  difficulty: Difficulty;
  verdict: 'idle' | 'correct' | 'wrong' | 'revealed';
}) {
  const [fellBack, setFellBack] = useState(false);
  // Only the per-question fallback resets on a new question; the learner's
  // Geschrieben/Original choice (view) is owned by the engine and stays put.
  useEffect(() => {
    setFellBack(false);
  }, [item.key, qNonce]);

  // The written form is offered only when the glyph has a traced canonical (and
  // the render didn't 404). Otherwise the crop is the only option and the toggle
  // is hidden.
  const canWrite = hasDuctus && !fellBack;
  const showWritten = canWrite && view === 'written';

  return (
    <Paper
      variant="outlined"
      sx={{
        // Fixed height so the box never resizes when the learner toggles between
        // the written render and the (taller) chart crop.
        position: 'relative',
        p: 2,
        width: '100%',
        height: 280,
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
          sx={{ maxWidth: '100%', maxHeight: 240, objectFit: 'contain', userSelect: 'none' }}
          draggable={false}
        />
      )}

      {canWrite && (
        <ToggleButtonGroup
          size="small"
          exclusive
          value={view}
          onChange={(_, v: PromptView | null) => v && setView(v)}
          aria-label={de.quiz.play.viewToggleAria}
          // Tucked into the top-right corner of the box, overlaying the prompt,
          // so the toggle stays put while the glyph stays centred.
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            bgcolor: paper.hi,
            '& .MuiToggleButton-root': { py: 0.25, px: 1 },
          }}
        >
          <ToggleButton value="written">{de.quiz.play.viewWritten}</ToggleButton>
          <ToggleButton value="crop">{de.quiz.play.viewCrop}</ToggleButton>
        </ToggleButtonGroup>
      )}
    </Paper>
  );
}
