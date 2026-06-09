// QuizResultsPanel — the end-of-session Auswertung: hit rate, the letters that
// were missed most (worst-first bars) and the confusion pairs ("ſ für f
// gehalten"), plus replay/back-to-setup actions. Purely presentational; the
// tallies accumulate in useQuizEngine and arrive via props.

import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ReplayIcon from '@mui/icons-material/Replay';
import TuneIcon from '@mui/icons-material/Tune';
import { Alert, Box, Button, Chip, Divider, LinearProgress, Paper, Stack, Typography } from '@mui/material';
import { useMemo } from 'react';

import { CONFUSION_SEP, type ConfusionMap, type MissMap } from '@/sections/quiz/useQuizEngine';
import { garamond } from '@/styles/paper';

interface ResultsProps {
  stats: { correct: number; seen: number; streak: number; bestStreak: number };
  misses: MissMap;
  confusions: ConfusionMap;
  onReplay: () => void;
  onSetup: () => void;
}

export function QuizResultsPanel(p: ResultsProps) {
  const pct = p.stats.seen > 0 ? Math.round((p.stats.correct / p.stats.seen) * 100) : 0;

  // Worst letters first; cap the list so the screen stays scannable.
  const topMisses = useMemo(
    () =>
      Object.entries(p.misses)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 6),
    [p.misses],
  );
  const maxMiss = topMisses.length ? topMisses[0][1] : 0;

  const topConfusions = useMemo(
    () =>
      Object.entries(p.confusions)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([key, count]) => {
          const [seen, guessed] = key.split(CONFUSION_SEP);
          return { seen, guessed, count };
        }),
    [p.confusions],
  );

  return (
    <Paper variant="outlined" sx={{ p: 3 }}>
      <Stack spacing={3}>
        <Box>
          <Typography variant="overline" color="text.secondary">
            Auswertung
          </Typography>
          <Typography sx={{ fontFamily: garamond, fontSize: '1.75rem', lineHeight: 1.2 }}>
            {p.stats.correct} von {p.stats.seen} richtig
          </Typography>
          <LinearProgress
            variant="determinate"
            value={pct}
            color={pct >= 80 ? 'success' : pct >= 50 ? 'primary' : 'warning'}
            sx={{ mt: 1.5, height: 8, borderRadius: 4 }}
          />
          <Box sx={{ display: 'flex', gap: 1, mt: 1.5, flexWrap: 'wrap' }}>
            <Chip size="small" label={`${pct}% Trefferquote`} />
            <Chip size="small" variant="outlined" color="primary" label={`Beste Serie ${p.stats.bestStreak}`} />
          </Box>
        </Box>

        <Divider />

        {/* Letters that were missed most */}
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Diese Buchstaben fielen schwer
          </Typography>
          {topMisses.length === 0 ? (
            <Alert severity="success" icon={<CheckCircleIcon />} sx={{ py: 0.5 }}>
              Kein einziger Fehler — sauber gelesen!
            </Alert>
          ) : (
            <Stack spacing={1}>
              {topMisses.map(([glyph, count]) => (
                <Box key={glyph} sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Box
                    sx={{
                      fontFamily: garamond,
                      fontSize: '1.6rem',
                      width: 36,
                      textAlign: 'center',
                      flexShrink: 0,
                    }}
                  >
                    {glyph}
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <Box
                      sx={{
                        height: 10,
                        borderRadius: 5,
                        bgcolor: 'error.main',
                        opacity: 0.85,
                        width: `${maxMiss ? Math.max(8, (count / maxMiss) * 100) : 0}%`,
                        transition: 'width 200ms',
                      }}
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ width: 64, textAlign: 'right' }}>
                    {count}× falsch
                  </Typography>
                </Box>
              ))}
            </Stack>
          )}
        </Box>

        {/* Confusion pairs */}
        {topConfusions.length > 0 && (
          <>
            <Divider />
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Häufig verwechselt
              </Typography>
              <Stack spacing={1}>
                {topConfusions.map(({ seen, guessed, count }) => (
                  <Box key={`${seen}${CONFUSION_SEP}${guessed}`} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box component="span" sx={{ fontFamily: garamond, fontSize: '1.4rem' }}>
                      {seen}
                    </Box>
                    <Typography component="span" color="text.secondary">
                      für
                    </Typography>
                    <Box component="span" sx={{ fontFamily: garamond, fontSize: '1.4rem' }}>
                      {guessed}
                    </Box>
                    <Typography component="span" color="text.secondary">
                      gehalten
                    </Typography>
                    <Box sx={{ flex: 1 }} />
                    <Chip size="small" variant="outlined" label={`${count}×`} />
                  </Box>
                ))}
              </Stack>
            </Box>
          </>
        )}

        <Divider />

        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
          <Button variant="contained" startIcon={<ReplayIcon />} onClick={p.onReplay} fullWidth>
            Nochmal
          </Button>
          <Button variant="outlined" startIcon={<TuneIcon />} onClick={p.onSetup} fullWidth>
            Einstellungen
          </Button>
        </Stack>
      </Stack>
    </Paper>
  );
}
