// The quiz prompt: the glyph "as written" (animated ductus) or the static Loth
// crop, with a toggle so the learner can switch between the two at will (compare
// the synthesised pen against the real specimen). The chosen view lives in the
// engine, so it persists across questions and only resets when a new session
// starts; the written form is still preferred whenever a traced canonical
// exists, falling back to the crop when the written render reports none (a 404
// race) or the glyph was never traced.

import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import HighlightOffIcon from '@mui/icons-material/HighlightOff';
import { Box, Chip, Fade, Paper, ToggleButton, ToggleButtonGroup } from '@mui/material';
import { useEffect, useState } from 'react';

import { WrittenGlyph } from '@/components/WrittenGlyph';
import { de } from '@/locales';
import { questionCropUrl, type Difficulty } from '@/sections/quiz/quizTypes';
import { type PromptView, type QuizItem } from '@/sections/quiz/useQuizEngine';

// Absolute, centred crop placement shared by the reveal's base (target) crop and
// the overlaid (picked) crop, so the two land pixel-identical and a correct pick
// reads as a true, fully coincident match. maxWidth is the Paper's content width —
// its padding box (the abs-positioning reference) minus the 16px padding each side —
// and maxHeight matches the idle crop, so nothing shifts when the reveal lands.
const overlayCropSx = {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  maxWidth: 'calc(100% - 32px)',
  maxHeight: 240,
  objectFit: 'contain',
  userSelect: 'none',
} as const;

export function QuestionVisual({
  item,
  hasDuctus,
  qNonce,
  view,
  setView,
  difficulty,
  verdict,
  overlayUrl,
}: {
  item: QuizItem;
  hasDuctus: boolean;
  qNonce: number;
  view: PromptView;
  setView: (v: PromptView) => void;
  difficulty: Difficulty;
  verdict: 'idle' | 'correct' | 'wrong' | 'revealed';
  // The crop of the picked letter to blend over the prompt once answered
  // ("Doppelbelichtung"): the prompt's own crop on a correct pick, the wrong
  // letter's crop on a miss, null when the picked letter has no locked specimen.
  overlayUrl: string | null;
}) {
  // The match/deviation reveal only shows after a concrete pick — a given-up
  // ("revealed") question keeps the plain solution list without the overlay.
  const overlayActive = verdict === 'correct' || verdict === 'wrong';
  const tone = verdict === 'correct' ? 'success' : 'error';
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
        // Neutral white work surface — it frames the scanned chart crop, so the
        // specimen reads true against an even ground rather than the paper grain.
        bgcolor: '#fff',
        borderColor: verdict === 'correct' ? 'success.main' : verdict === 'wrong' ? 'error.main' : 'divider',
        transition: 'border-color 120ms',
      }}
    >
      {overlayActive ? (
        // On reveal the comparison is crop ↔ crop, never written ↔ crop: the
        // target's own crop is the base (so the learner also sees the solution)
        // and the picked crop blends over it at identical geometry. Same letter
        // on a correct pick → the two coincide exactly.
        <Box
          component="img"
          src={questionCropUrl(item.key, difficulty)}
          alt={de.quiz.play.cropAlt}
          sx={overlayCropSx}
          draggable={false}
        />
      ) : showWritten ? (
        <WrittenGlyph
          key={`${item.key}-${qNonce}`}
          glyphKey={item.key}
          height={220}
          // Inherit the Paper's white work-surface ground (the chart-crop frame
          // is #fff per the surface rule) instead of the default white box.
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

      {canWrite && !overlayActive && (
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
            bgcolor: '#fff',
            '& .MuiToggleButton-root': { py: 0.25, px: 1 },
          }}
        >
          <ToggleButton value="written">{de.quiz.play.viewWritten}</ToggleButton>
          <ToggleButton value="crop">{de.quiz.play.viewCrop}</ToggleButton>
        </ToggleButtonGroup>
      )}

      {/* Double exposure: once answered, the picked letter's crop blends over the
          prompt — fully coincident (green, match) on a correct pick, a second
          ghosted form (red, deviation) on a miss — under a verdict badge. */}
      {overlayActive && (
        <Fade in appear timeout={320}>
          <Box sx={{ position: 'absolute', inset: 0, borderRadius: 'inherit', overflow: 'hidden', pointerEvents: 'none' }}>
            {/* the colour wash that makes the box "leuchtet auf" */}
            <Box sx={{ position: 'absolute', inset: 0, bgcolor: `${tone}.main`, opacity: 0.14 }} />
            {/* the picked crop, multiply-blended over the base target crop at the
                exact same geometry — so a correct pick (same crop) overlaps cleanly
                and a miss ghosts a visibly different form over the solution */}
            {overlayUrl && (
              <Box
                component="img"
                src={overlayUrl}
                alt={de.quiz.play.overlayAlt}
                sx={{ ...overlayCropSx, opacity: 0.55, mixBlendMode: 'multiply' }}
              />
            )}
            <Chip
              size="small"
              color={tone}
              icon={verdict === 'correct' ? <CheckCircleIcon /> : <HighlightOffIcon />}
              label={verdict === 'correct' ? de.quiz.play.matchStrong : de.quiz.play.matchWeak}
              sx={{ position: 'absolute', top: 8, left: '50%', transform: 'translateX(-50%)', fontWeight: 600 }}
            />
          </Box>
        </Fade>
      )}
    </Paper>
  );
}
