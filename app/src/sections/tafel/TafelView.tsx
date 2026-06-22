// TafelView — the public writing-chart page (`/tafel`, German "Schreibtafel").
// Shows the source teaching chart two ways, switched by one toggle:
//   - "Original": the raw chart scan the templates were authored from.
//   - "Geschrieben" (written): every letter that has a traced canonical,
//     rendered "as written" (WrittenGlyph) — the chart writing itself. Tapping a
//     letter opens it large and replays the ductus.
//
// Like the quiz, this rides on the site-wide public source (CONFIG.sourceId) via
// the pinned AdminProvider mounted in the route, so it reads the same bboxes +
// glyph status the admin curated — but it never follows the admin's runtime
// source switcher.

import { Box, Container, Dialog, DialogContent, IconButton, Paper, Stack, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { useMemo, useState } from 'react';

import { BootStatus } from '@/components/BootStatus';
import { WrittenGlyph } from '@/components/WrittenGlyph';
import { useAdmin } from '@/context/AdminContext';
import { CONFIG } from '@/global-config';
import { LETTERS, glyphKeyFor, type Position } from '@/domain/glyphs';
import { PublicLayout } from '@/layouts/public/PublicLayout';
import { chartUrl } from '@/lib/api';
import { de } from '@/locales';
import { garamond, paper } from '@/styles/paper';

type View = 'original' | 'written';

// One representative position per letter prefers the medial form (the body shape
// most letters share), falling back to initial then final.
const PREFERRED_POSITIONS: Position[] = ['medial', 'initial', 'final'];

interface WrittenLetter {
  key: string; // representative glyph_key with a canonical
  glyph: string; // the rendered character (ſ, A, ch, …)
}

export function TafelView() {
  const { source, glyphsByKey, loadError, waking } = useAdmin();
  const [view, setView] = useState<View>('original');
  // The letter shown large in the replay modal, or null when closed.
  const [active, setActive] = useState<WrittenLetter | null>(null);

  // Every letter that owns a traced canonical, deduped to one entry per letter
  // (its three positions usually share one authored form), ordered by the
  // alphabet registry. glyphKeyFor folds the s/ſ allograph key overrides in, so
  // the two never collapse into one card.
  const letters = useMemo<WrittenLetter[]>(() => {
    const out: WrittenLetter[] = [];
    for (const letter of LETTERS) {
      let repKey: string | undefined;
      for (const position of PREFERRED_POSITIONS) {
        const key = glyphKeyFor(letter, position);
        if (glyphsByKey[key]?.has_data) {
          repKey = key;
          break;
        }
      }
      if (repKey) out.push({ key: repKey, glyph: letter.glyph });
    }
    return out;
  }, [glyphsByKey]);

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
    <PublicLayout footer>
      <Container maxWidth="md" sx={{ py: { xs: 4, sm: 6 } }}>
        <Stack spacing={3}>
          <Stack spacing={1.5}>
            <Typography component="h1" sx={{ fontFamily: garamond, fontStyle: 'italic', fontSize: '2rem', lineHeight: 1.1 }}>
              {de.tafel.title}
            </Typography>
            <Typography sx={{ color: paper.inkSoft, maxWidth: '60ch' }}>{de.tafel.intro}</Typography>
          </Stack>

          <ToggleButtonGroup
            size="small"
            exclusive
            value={view}
            onChange={(_, v: View | null) => v && setView(v)}
            aria-label={de.tafel.viewToggleAria}
            sx={{ alignSelf: 'flex-start' }}
          >
            <ToggleButton value="original">{de.tafel.viewOriginal}</ToggleButton>
            <ToggleButton value="written">{de.tafel.viewWritten}</ToggleButton>
          </ToggleButtonGroup>

          {view === 'original' ? (
            <Stack spacing={1}>
              <Paper variant="outlined" sx={{ p: 1, bgcolor: paper.hi, overflow: 'auto', maxHeight: '75vh' }}>
                <Box
                  component="img"
                  src={chartUrl(CONFIG.sourceId)}
                  alt={de.tafel.originalAlt}
                  sx={{ display: 'block', width: '100%', height: 'auto', userSelect: 'none' }}
                  draggable={false}
                />
              </Paper>
              {(source.attribution || source.title) && (
                <Typography variant="caption" sx={{ color: paper.inkSoft }}>
                  {source.attribution ?? source.title}
                </Typography>
              )}
            </Stack>
          ) : letters.length === 0 ? (
            <Typography sx={{ color: paper.inkSoft }}>{de.tafel.empty}</Typography>
          ) : (
            <Box
              sx={{
                display: 'grid',
                gap: 1.5,
                gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))',
              }}
            >
              {letters.map((l) => (
                <Paper
                  key={l.key}
                  variant="outlined"
                  onClick={() => setActive(l)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      setActive(l);
                    }
                  }}
                  aria-label={`${l.glyph} — ${de.tafel.replayHint}`}
                  sx={{
                    p: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    minHeight: 130,
                    cursor: 'pointer',
                    bgcolor: paper.hi,
                    transition: 'border-color 120ms, box-shadow 120ms',
                    '&:hover, &:focus-visible': {
                      borderColor: paper.viridian,
                      boxShadow: `0 0 0 1px ${paper.viridian}`,
                    },
                  }}
                >
                  {/* pointerEvents off so the click always lands on the card, not
                      WrittenGlyph's own replay button — the card opens the modal. */}
                  <Box sx={{ pointerEvents: 'none' }}>
                    <WrittenGlyph glyphKey={l.key} height={104} tight surfaceBg="transparent" />
                  </Box>
                </Paper>
              ))}
            </Box>
          )}
        </Stack>
      </Container>

      {/* Replay modal: a large WrittenGlyph that re-writes the ductus on open
          (fresh mount per letter) — and its own replay button for another pass. */}
      <Dialog
        open={active !== null}
        onClose={() => setActive(null)}
        maxWidth="xs"
        fullWidth
        aria-label={active ? `${active.glyph} — ${de.tafel.title}` : de.tafel.title}
      >
        <DialogContent sx={{ position: 'relative', bgcolor: paper.hi, display: 'flex', justifyContent: 'center', py: 4 }}>
          <IconButton
            onClick={() => setActive(null)}
            aria-label={de.tafel.close}
            size="small"
            sx={{ position: 'absolute', top: 8, right: 8, color: 'text.secondary' }}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
          {active && <WrittenGlyph key={active.key} glyphKey={active.key} height={280} surfaceBg="transparent" />}
        </DialogContent>
      </Dialog>
    </PublicLayout>
  );
}
