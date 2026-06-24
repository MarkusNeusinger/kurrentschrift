// TafelView — the public writing-chart page (`/tafel`, German "Schreibtafel").
// Shows the three German Ausgangsschriften (Kurrent · Sütterlin · Offenbacher)
// one below the other, each with whatever the DB holds today (see useGrundtafeln):
//   - written  — Original/Geschrieben toggle. "Geschrieben" renders every locked,
//     traced letter "as written" (WrittenGlyph); tapping one replays the ductus.
//   - original — only the Original scan + an honest "noch nicht nachgeschrieben".
//   - pending  — a placeholder (no chart source seeded yet).
//
// Unlike the quiz this page does NOT ride the pinned AdminProvider (one source):
// useGrundtafeln fetches all chart sources read-only and groups them by style.

import { Box, Chip, Dialog, DialogContent, IconButton, Link, Paper, Stack, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { useState } from 'react';

import { BootStatus } from '@/components/BootStatus';
import { CategoryHeading } from '@/components/CategoryHeading';
import { PageContainer } from '@/components/PageContainer';
import { Prose } from '@/components/Prose';
import { WrittenGlyph } from '@/components/WrittenGlyph';
import { PublicLayout } from '@/layouts/public/PublicLayout';
import { chartUrl } from '@/lib/api';
import type { SourceOut } from '@/lib/api';
import { de } from '@/locales';
import { garamond, paper } from '@/styles/paper';
import { useGrundtafeln, type Grundtafel, type WrittenLetter } from '@/sections/tafel/useGrundtafeln';

type View = 'original' | 'written';

// Friendly German labels for the short license codes stored on a source; the raw
// code is the fallback for anything not mapped here.
const LICENSE_LABELS: Record<string, string> = {
  PD: 'Gemeinfrei (Public Domain)',
  CC0: 'CC0 (gemeinfrei)',
};

// The provenance of one chart source (title, attribution, license, link), shown
// under each script that has a scan.
function SourceProvenance({ source }: { source: SourceOut }) {
  return (
    <Paper variant="outlined" sx={{ p: 2, bgcolor: paper.hi }}>
      <Stack spacing={1}>
        <Typography component="h4" variant="h6" sx={{ fontFamily: garamond, fontWeight: 400, fontStyle: 'italic' }}>
          {de.tafel.source.heading}
        </Typography>
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {source.title}
        </Typography>
        {source.attribution && (
          <Typography variant="caption" sx={{ color: paper.inkSoft }}>
            {source.attribution}
          </Typography>
        )}
        <Typography variant="caption" sx={{ color: paper.inkSoft }}>
          {de.tafel.source.licenseLabel}: {LICENSE_LABELS[source.license] ?? source.license}
        </Typography>
        {source.origin_url && (
          <Link
            href={source.origin_url}
            target="_blank"
            rel="noopener noreferrer"
            variant="body2"
            sx={{ color: paper.viridian, alignSelf: 'flex-start' }}
          >
            {de.tafel.source.originLink}
          </Link>
        )}
      </Stack>
    </Paper>
  );
}

// The Original chart scan.
function OriginalScan({ source }: { source: SourceOut }) {
  return (
    <Paper variant="outlined" sx={{ p: 1, bgcolor: '#fff' }}>
      <Box
        component="img"
        src={chartUrl(source.id)}
        alt={de.tafel.originalAlt}
        sx={{ display: 'block', width: '100%', height: 'auto', userSelect: 'none' }}
        draggable={false}
      />
    </Paper>
  );
}

// The grid of written letters; each card opens the replay modal.
function WrittenGrid({ letters, onReplay }: { letters: WrittenLetter[]; onReplay: (l: WrittenLetter) => void }) {
  if (letters.length === 0) {
    return <Typography sx={{ color: paper.inkSoft }}>{de.tafel.empty}</Typography>;
  }
  return (
    <Box sx={{ display: 'grid', gap: 1.5, gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))' }}>
      {letters.map((l) => (
        <Paper
          key={l.key}
          variant="outlined"
          onClick={() => onReplay(l)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onReplay(l);
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
            bgcolor: '#fff',
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
  );
}

// One script's section: heading + Feder/state caption, then the body by state.
function GrundtafelSection({ tafel, onReplay }: { tafel: Grundtafel; onReplay: (l: WrittenLetter) => void }) {
  // Original is the default everywhere; the written grid is one toggle away.
  const [view, setView] = useState<View>('original');
  const feder = de.tafel.feder[tafel.styleId];

  return (
    <Stack component="section" spacing={2} aria-label={tafel.name}>
      <Box>
        <CategoryHeading>{tafel.name}</CategoryHeading>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
          {feder ? (
            <Typography variant="body2" sx={{ color: paper.inkSoft }}>
              {feder}
            </Typography>
          ) : null}
          <Chip
            size="small"
            label={de.tafel.state[tafel.state]}
            variant="outlined"
            sx={{
              color: tafel.state === 'written' ? paper.viridian : paper.inkSoft,
              borderColor: tafel.state === 'written' ? paper.viridian : paper.line,
              bgcolor: 'transparent',
            }}
          />
        </Box>
      </Box>

      {tafel.state === 'written' && tafel.source ? (
        <>
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
          {view === 'written' ? (
            <WrittenGrid letters={tafel.letters} onReplay={onReplay} />
          ) : (
            <OriginalScan source={tafel.source} />
          )}
          <SourceProvenance source={tafel.source} />
        </>
      ) : tafel.state === 'original' && tafel.source ? (
        <>
          <OriginalScan source={tafel.source} />
          <SourceProvenance source={tafel.source} />
        </>
      ) : (
        <Paper
          variant="outlined"
          sx={{ p: { xs: 3, sm: 5 }, bgcolor: paper.hi, textAlign: 'center', borderStyle: 'dashed' }}
        >
          <Typography sx={{ color: paper.inkSoft, maxWidth: '50ch', mx: 'auto' }}>{de.tafel.pendingNote}</Typography>
        </Paper>
      )}
    </Stack>
  );
}

export function TafelView() {
  const { tafeln, loadError, waking } = useGrundtafeln();
  // The letter shown large in the replay modal, or null when closed.
  const [active, setActive] = useState<WrittenLetter | null>(null);

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

  if (!tafeln) {
    return (
      <BootStatus
        variant="loading"
        message={waking ? de.common.boot.sourceColdStart : de.common.boot.loadingTemplate}
      />
    );
  }

  return (
    <PublicLayout footer>
      <PageContainer width="text" sx={{ py: { xs: 4, sm: 6 } }}>
        <Stack spacing={{ xs: 5, sm: 7 }}>
          <Stack spacing={1.5}>
            <Typography component="h1" variant="h1" sx={{ fontFamily: garamond, fontStyle: 'italic' }}>
              {de.tafel.title}
            </Typography>
            <Prose align="left">
              <Typography sx={{ color: paper.inkSoft }}>{de.tafel.intro}</Typography>
              <Typography sx={{ color: paper.inkSoft, mt: 1.5 }}>{de.tafel.note}</Typography>
            </Prose>
          </Stack>

          {tafeln.map((t) => (
            <GrundtafelSection key={t.styleId} tafel={t} onReplay={setActive} />
          ))}
        </Stack>
      </PageContainer>

      {/* Replay modal: a large WrittenGlyph that re-writes the ductus on open
          (fresh mount per letter) — and its own replay button for another pass. */}
      <Dialog
        open={active !== null}
        onClose={() => setActive(null)}
        maxWidth="xs"
        fullWidth
        aria-label={active ? `${active.glyph} — ${de.tafel.title}` : de.tafel.title}
      >
        <DialogContent sx={{ position: 'relative', bgcolor: '#fff', display: 'flex', justifyContent: 'center', py: 4 }}>
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
