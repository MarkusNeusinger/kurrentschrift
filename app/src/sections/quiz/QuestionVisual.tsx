// The quiz prompt: the glyph "as written" (animated ductus) when it has a traced
// canonical, else the static Loth crop. If the written render reports no canonical
// (a 404 race), it falls back to the crop for this question.

import { Box, Paper } from '@mui/material';
import { useEffect, useState } from 'react';

import { WrittenGlyph } from '@/components/WrittenGlyph';
import { questionCropUrl, type Difficulty } from '@/sections/quiz/quizTypes';
import { type QuizItem } from '@/sections/quiz/useQuizEngine';

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
  // Reset the fallback whenever the question changes.
  useEffect(() => setFellBack(false), [item.key, qNonce]);
  const showWritten = hasDuctus && !fellBack;

  return (
    <Paper
      variant="outlined"
      sx={{
        p: 2,
        minHeight: 200,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: '#fff',
        borderColor: verdict === 'correct' ? 'success.main' : verdict === 'wrong' ? 'error.main' : 'divider',
        transition: 'border-color 120ms',
      }}
    >
      {showWritten ? (
        <WrittenGlyph
          key={`${item.key}-${qNonce}`}
          glyphKey={item.key}
          height={220}
          onUnavailable={() => setFellBack(true)}
        />
      ) : (
        <Box
          component="img"
          src={questionCropUrl(item.key, difficulty)}
          alt="Kurrent-Buchstabe"
          sx={{ maxWidth: '100%', maxHeight: 260, objectFit: 'contain', userSelect: 'none' }}
          draggable={false}
        />
      )}
    </Paper>
  );
}
