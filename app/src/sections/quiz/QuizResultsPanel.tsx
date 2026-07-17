// QuizResultsPanel — the end-of-session Auswertung (design handoff "Tinte &
// Vergleich"): the hit-rate card, "Häufig verwechselt" (the confusion pairs the
// learner mixed up) and "Machte Mühe" (the forms that cost the most), or a clean
// "sauber gelesen" note when nothing was missed. The forms render "as written"
// (WrittenGlyph / WrittenWord), with a plain-type fallback. The tallies
// accumulate in useQuizEngine and arrive via props.

import { Box, Stack, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useEffect, useMemo, useState } from 'react';

import { WrittenGlyph } from '@/components/WrittenGlyph';
import { WrittenWord } from '@/components/WrittenWord';
import { de } from '@/locales';
import { InkButton, QuietButton, QuizEyebrow } from '@/sections/quiz/quizUi';
import { type ConfusionMap, type MissMap, type TallyRef } from '@/sections/quiz/useQuizEngine';
import { cardSurface, display, garamond, paper, pigment, quiz, quizRadius } from '@/styles/paper';

interface ResultsProps {
  stats: { correct: number; seen: number; streak: number; bestStreak: number };
  misses: MissMap;
  confusions: ConfusionMap;
  onReplay: () => void;
  onSetup: () => void;
}

// A small written form for the results lists, with a plain-type fallback.
function ResultForm({ refr, height }: { refr: TallyRef; height: number }) {
  const [unavailable, setUnavailable] = useState(false);
  // Word compose fetch failed (cache evicted + refetch exhausted) — fall back
  // to plain type instead of letting the pill spin forever. Post-answer surface,
  // so plain text gives nothing away.
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    setUnavailable(false);
    setFailed(false);
  }, [refr.renderKey]);

  if (!refr.renderKey || unavailable || failed) {
    return (
      // Deliberate display sizing: the plain-type stand-in scales with the
      // written form's pixel height, not the type ladder.
      <Typography component="span" sx={{ fontFamily: display, fontWeight: 600, fontSize: height * 0.6, color: paper.ink }}>
        {refr.label}
      </Typography>
    );
  }
  if (refr.kind === 'word') {
    return (
      <WrittenWord
        text={refr.renderKey}
        animate={false}
        height={height}
        maxWidth={220}
        surfaceBg="transparent"
        showLineature={false}
        onError={() => setFailed(true)}
      />
    );
  }
  return (
    <WrittenGlyph glyphKey={refr.renderKey} animate={false} height={height} tight surfaceBg="transparent" onUnavailable={() => setUnavailable(true)} />
  );
}

export function QuizResultsPanel(p: ResultsProps) {
  const { correct, seen } = p.stats;
  const pct = seen > 0 ? Math.round((correct / seen) * 100) : 0;

  const topMisses = useMemo(() => Object.values(p.misses).sort((a, b) => b.count - a.count).slice(0, 6), [p.misses]);
  const topConfusions = useMemo(
    () => Object.values(p.confusions).sort((a, b) => b.count - a.count).slice(0, 4),
    [p.confusions],
  );
  const clean = topMisses.length === 0;

  return (
    <Stack spacing={3}>
      <QuizEyebrow>{de.quiz.results.heading}</QuizEyebrow>

      {/* Hit-rate card */}
      <Box sx={{ bgcolor: cardSurface, border: `1px solid ${paper.line}`, borderRadius: '6px', p: { xs: 3, sm: 3.5 }, textAlign: 'center' }}>
        <Typography variant="overline" sx={{ color: paper.sepia, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          {de.quiz.results.hitRateLabel}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'baseline', justifyContent: 'center', gap: 1, mt: 0.5 }}>
          {/* Deliberate display figures: the score readout (46/24) is a scoreboard
              number pair outside the type ladder, not running text. */}
          <Typography component="span" sx={{ fontFamily: display, fontWeight: 600, fontSize: 46, color: paper.ink, lineHeight: 1 }}>
            {correct}
          </Typography>
          <Typography component="span" sx={{ fontFamily: display, fontSize: 24, color: paper.sepiaFaint }}>
            / {seen}
          </Typography>
          <Typography component="span" variant="body1" sx={{ fontFamily: garamond, color: paper.viridianText, ml: 0.5 }}>
            {pct} %
          </Typography>
        </Box>
        <Box sx={{ mt: 2, height: 4, borderRadius: 2, bgcolor: alpha(paper.line, 0.4), overflow: 'hidden' }}>
          <Box sx={{ height: '100%', width: `${pct}%`, bgcolor: paper.viridian, transition: 'width 300ms ease' }} />
        </Box>
      </Box>

      {/* Confusions */}
      {topConfusions.length > 0 && (
        <Box>
          {/* Real section heading (semantics + ladder size); Playfair headings
              carry weight 600 per design-system §3. */}
          <Typography component="h2" variant="h6" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink }}>
            {de.quiz.results.confusionsHeading}
          </Typography>
          <Typography component="p" variant="caption" sx={{ color: paper.sepia, mb: 1.25 }}>
            {de.quiz.results.confusionsHint}
          </Typography>
          <Stack spacing={1}>
            {topConfusions.map((c) => (
              <Box
                key={`${c.correct.renderKey ?? c.correct.label}__${c.guessed.renderKey ?? c.guessed.label}`}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.25,
                  bgcolor: quiz.face,
                  border: `1px solid ${quiz.pillBorder}`,
                  borderRadius: quizRadius,
                  px: 1.75,
                  py: 1,
                }}
              >
                <ResultForm refr={c.correct} height={32} />
                <Typography component="span" aria-hidden sx={{ fontFamily: display, color: paper.sepiaFaint }}>
                  ↔
                </Typography>
                <ResultForm refr={c.guessed} height={32} />
                <Typography component="span" variant="caption" sx={{ color: paper.sepia, ml: 0.5 }}>
                  {c.correct.label} / {c.guessed.label}
                </Typography>
                <Box sx={{ flex: 1 }} />
                <Typography component="span" variant="caption" sx={{ color: pigment.oxblood }}>
                  ·{c.count}
                  {de.quiz.results.times}
                </Typography>
              </Box>
            ))}
          </Stack>
        </Box>
      )}

      {/* Misses — or the clean note when nothing was missed */}
      {clean ? (
        <Box
          sx={{
            border: `1px solid ${paper.viridian}`,
            bgcolor: alpha(paper.viridian, 0.08),
            borderRadius: '6px',
            px: 2,
            py: 1.5,
            textAlign: 'center',
          }}
        >
          <Typography variant="body2" sx={{ color: paper.ink }}>
            <Box component="span" sx={{ color: paper.viridianText, mr: 0.75 }}>
              ✓
            </Box>
            {de.quiz.results.cleanNote}
          </Typography>
        </Box>
      ) : (
        <Box>
          {/* Real section heading (semantics + ladder size); Playfair headings
              carry weight 600 per design-system §3. */}
          <Typography component="h2" variant="h6" sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, mb: 1.25 }}>
            {de.quiz.results.missesHeading}
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {topMisses.map((m) => (
              <Box
                key={m.renderKey ?? m.label}
                sx={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 0.75,
                  bgcolor: quiz.face,
                  border: `1px solid ${quiz.pillBorder}`,
                  borderRadius: quizRadius,
                  px: 1.25,
                  py: 0.75,
                }}
              >
                <ResultForm refr={m} height={28} />
                {/* Name the letter next to the written form — but only when a
                    form is actually drawn; without a renderKey ResultForm already
                    falls back to the plain label, so this would double it. */}
                {m.renderKey && (
                  <Typography component="span" variant="caption" sx={{ fontWeight: 600, color: paper.ink }}>
                    {m.label}
                  </Typography>
                )}
                <Typography component="span" variant="caption" sx={{ color: paper.sepia }}>
                  ·{m.count}
                  {de.quiz.results.times}
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>
      )}

      {/* Actions */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2.5, flexWrap: 'wrap', pt: 0.5 }}>
        <InkButton onClick={p.onReplay} fullWidthMobile={false}>
          {de.quiz.results.replay} →
        </InkButton>
        <QuietButton onClick={p.onSetup}>{de.quiz.results.settings}</QuietButton>
      </Box>
    </Stack>
  );
}
