// The quiz card — the "Arbeitsfläche" the form is read on (design handoff
// "Tinte & Vergleich"). A warm work surface (a shade lighter than the page) with
// an inner hairline frame and a faint exercise-book ruling that the rendered
// glyph carries with it. Three states:
//
//   • idle  — the form written Zug um Zug (WrittenGlyph / WrittenWord), an "i"
//             affordance top-right and a faint centre divider.
//   • correct — the card glows viridian; the matching Antiqua letter/word presses
//             through behind the form like letterpress.
//   • wrong — the card glows vermilion and shows the two forms side by side:
//             "deine Wahl" (red) ↔ "richtig" (near-black), so the difference is
//             legible at a glance.
//
// Letters render via WrittenGlyph (with a chart-crop fallback if a glyph has no
// canonical yet); words via WrittenWord. The comparison forms are static and
// tinted (inkColor), never a second write-in performance.

import { Box, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useEffect, useState } from 'react';

import { WrittenGlyph } from '@/components/WrittenGlyph';
import { WrittenWord } from '@/components/WrittenWord';
import { de } from '@/locales';
import { questionCropUrl, type Difficulty } from '@/sections/quiz/quizTypes';
import { inCase, type Choice, type Question, type Verdict } from '@/sections/quiz/useQuizEngine';
import { cardSurface, display, inkState, paper, pigment, schulheft } from '@/styles/paper';

// Quiz-local rendering tokens (the card is a sanctioned work surface, not the
// paper identity): the inner hairline frame and the two comparison ink tones.
// paper.line (not the fainter paper.lo) so the frame + centre divider actually
// read on the warm card.
const INNER_FRAME = paper.line;
const YOURS_INK = schulheft.marginRed; // the learner's wrong pick, in printed-margin red
const RIGHT_INK = inkState.oxidized; // the correct form, near-black

// The Antiqua letter/word that presses through behind a correct form.
function letterpressText(q: Question): string {
  return q.kind === 'word' ? q.word : inCase(q.kg.answer, q.kg);
}

// One written form (letter or word), with graceful fallbacks: a chart crop for a
// glyph without a canonical, plain Antiqua type when nothing can be rendered.
function WrittenForm({
  kind,
  renderKey,
  label,
  inkColor,
  animate = true,
  height,
  cropUrl,
  fallbackColor,
  word,
}: {
  kind: 'letter' | 'word';
  renderKey: string | null;
  label: string;
  inkColor?: string;
  animate?: boolean;
  height: number;
  // Chart-crop URL to fall back to when a letter has no canonical (prompt only).
  cropUrl?: string;
  // Colour of the plain-type fallback.
  fallbackColor?: string;
  // Larger Antiqua type for a word fallback vs. a single letter.
  word?: boolean;
}) {
  const [unavailable, setUnavailable] = useState(false);
  useEffect(() => setUnavailable(false), [renderKey]);

  const fallback = (
    <Typography
      sx={{ fontFamily: display, fontWeight: 600, fontSize: word ? '2rem' : '2.6rem', color: fallbackColor ?? inkColor ?? 'text.primary' }}
    >
      {label}
    </Typography>
  );

  if (kind === 'word') {
    if (!renderKey) return fallback;
    return (
      <WrittenWord
        text={renderKey}
        inkColor={inkColor}
        animate={animate}
        height={height}
        surfaceBg="transparent"
        // The prompt is the riddle: the default aria-label carries the word
        // itself and would hand the solution to the DOM/screen reader.
        ariaLabel={de.common.writtenWord.ariaLabelNeutral}
      />
    );
  }
  // letter
  if (renderKey && !unavailable) {
    return (
      <WrittenGlyph
        glyphKey={renderKey}
        inkColor={inkColor}
        animate={animate}
        height={height}
        surfaceBg="transparent"
        onUnavailable={() => setUnavailable(true)}
      />
    );
  }
  if (cropUrl) {
    return (
      <Box
        component="img"
        src={cropUrl}
        alt={de.quiz.play.cropAlt}
        sx={{ maxWidth: '100%', maxHeight: height + 40, objectFit: 'contain', userSelect: 'none' }}
        draggable={false}
      />
    );
  }
  return fallback;
}

export function QuestionVisual({
  question,
  qNonce,
  verdict,
  picked,
  difficulty,
}: {
  question: Question;
  qNonce: number;
  verdict: Verdict;
  picked: Choice | null;
  difficulty: Difficulty;
}) {
  const isCorrect = verdict === 'correct';
  const isWrong = verdict === 'wrong';
  const isWord = question.kind === 'word';

  const glow = isCorrect
    ? `0 0 0 2px ${paper.viridian}, 0 0 0 6px ${alpha(paper.viridian, 0.15)}, 0 0 28px ${alpha(paper.viridian, 0.22)}`
    : isWrong
      ? `0 0 0 2px ${pigment.vermilion}, 0 0 0 6px ${alpha(pigment.vermilion, 0.13)}, 0 0 28px ${alpha(pigment.vermilion, 0.2)}`
      : 'none';

  const promptCrop = question.kind === 'letter' ? questionCropUrl(question.key, difficulty) : undefined;

  return (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        minHeight: { xs: 224, sm: 290 },
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        px: { xs: 2, sm: 4 },
        py: { xs: 2.5, sm: 4 },
        bgcolor: cardSurface,
        border: '1px solid',
        borderColor: isCorrect ? paper.viridian : isWrong ? pigment.vermilion : paper.line,
        borderRadius: '6px',
        boxShadow: glow,
        overflow: 'hidden',
        transition: 'border-color 160ms ease, box-shadow 220ms ease',
      }}
    >
      {/* Inner hairline frame. */}
      <Box
        aria-hidden
        sx={{ position: 'absolute', inset: 10, border: `1px solid ${INNER_FRAME}`, borderRadius: '4px', pointerEvents: 'none' }}
      />

      {/* Faint vertical centre divider — single-form states only. */}
      {!isWrong && (
        <Box
          aria-hidden
          sx={{
            position: 'absolute',
            top: '20%',
            bottom: '20%',
            left: '50%',
            width: '1px',
            background: `linear-gradient(${INNER_FRAME}, transparent)`,
            opacity: 0.6,
            pointerEvents: 'none',
          }}
        />
      )}

      {isWrong ? (
        // ——— comparison: deine Wahl ↔ richtig ———
        <Box
          sx={{
            position: 'relative',
            zIndex: 1,
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: { xs: 1, sm: 3 },
          }}
        >
          <CompareColumn label={de.quiz.play.compareYours} labelColor={pigment.oxblood}>
            <WrittenForm
              kind={question.kind}
              renderKey={picked?.renderKey ?? null}
              label={picked?.label ?? ''}
              inkColor={YOURS_INK}
              fallbackColor={YOURS_INK}
              animate={false}
              height={isWord ? 60 : 112}
              word={isWord}
            />
          </CompareColumn>

          <Typography aria-hidden sx={{ fontFamily: display, fontSize: 22, color: paper.sepiaFaint, flexShrink: 0 }}>
            ↔
          </Typography>

          <CompareColumn label={de.quiz.play.compareCorrect} labelColor={paper.ink}>
            <WrittenForm
              kind={question.kind}
              renderKey={question.kind === 'word' ? question.render : question.key}
              label={letterpressText(question)}
              inkColor={RIGHT_INK}
              fallbackColor={RIGHT_INK}
              animate={false}
              height={isWord ? 60 : 112}
              word={isWord}
            />
          </CompareColumn>
        </Box>
      ) : (
        // ——— single form (idle / correct) ———
        <>
          {isCorrect && (
            <Typography
              aria-hidden
              sx={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily: display,
                fontWeight: 600,
                color: paper.ink,
                opacity: 0.1,
                fontSize: isWord ? { xs: '2.8rem', sm: '4.6rem' } : { xs: '7rem', sm: '11rem' },
                lineHeight: 1,
                whiteSpace: 'nowrap',
                pointerEvents: 'none',
                zIndex: 0,
              }}
            >
              {letterpressText(question)}
            </Typography>
          )}
          <Box sx={{ position: 'relative', zIndex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
            <WrittenForm
              key={`prompt-${qNonce}`}
              kind={question.kind}
              renderKey={question.kind === 'word' ? question.render : question.key}
              label={letterpressText(question)}
              height={isWord ? 110 : 150}
              cropUrl={promptCrop}
            />
          </Box>
        </>
      )}
    </Box>
  );
}

function CompareColumn({ label, labelColor, children }: { label: string; labelColor: string; children: React.ReactNode }) {
  return (
    <Box sx={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 86 }}>{children}</Box>
      <Typography
        variant="overline"
        sx={{ color: labelColor, textTransform: 'uppercase', letterSpacing: '0.08em', lineHeight: 1 }}
      >
        {label}
      </Typography>
    </Box>
  );
}
