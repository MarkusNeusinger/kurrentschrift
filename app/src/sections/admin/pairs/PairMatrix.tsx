// Pair matrix (redesign R1) — every two-letter combination of one chosen
// letter, server-composed via /write/word (single glyphs + generated Übergang),
// capitals only on the left. A read-only QA surface: an unnatural join shows up
// here directly instead of hiding inside a longer word. Cells fetch lazily
// (IntersectionObserver) through WrittenWord's shared render cache, so a full
// row of ~60 combinations doesn't fire at once on mount.

import { Alert, Box, ButtonBase, Typography } from '@mui/material';
import { useMemo, useState } from 'react';

import { WrittenWord } from '@/components/WrittenWord';
import { useAdmin } from '@/context/AdminContext';
import { glyphKeyFor, LETTERS, POSITIONS } from '@/domain/glyphs';
import type { Letter } from '@/domain/glyphs';
import { useInView } from '@/hooks/useInView';
import { de, fmt } from '@/locales/admin';
import { garamond } from '@/styles/paper';

const CELL_H = 88; // px — big enough to judge a join, small enough for a grid

function PairCell({ text, sourceId }: { text: string; sourceId: string }) {
  const [ref, inView] = useInView<HTMLDivElement>();
  return (
    <Box
      ref={ref}
      sx={{
        border: 1,
        borderColor: 'divider',
        borderRadius: 1,
        bgcolor: '#fff',
        p: 0.5,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 0.25,
        minWidth: 96,
      }}
    >
      <Typography variant="caption" color="text.secondary" sx={{ fontFamily: garamond }}>
        {text}
      </Typography>
      <Box sx={{ height: CELL_H, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {inView && <WrittenWord text={text} sourceId={sourceId} height={CELL_H} animate={false} showLineature />}
      </Box>
    </Box>
  );
}

function CellGrid({ pairs, sourceId }: { pairs: string[]; sourceId: string }) {
  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
      {pairs.map((p) => (
        <PairCell key={p} text={p} sourceId={sourceId} />
      ))}
    </Box>
  );
}

export function PairMatrix() {
  const { source, sourceId, glyphsByKey } = useAdmin();
  const authored = useMemo(() => {
    const hasCanon = (letter: Letter) => POSITIONS.some((p) => glyphsByKey[glyphKeyFor(letter, p)]?.has_data);
    return {
      lower: LETTERS.filter((l) => l.group === 'lower' && hasCanon(l)),
      upper: LETTERS.filter((l) => l.group === 'upper' && hasCanon(l)),
    };
  }, [glyphsByKey]);
  const pickable = useMemo(() => [...authored.lower, ...authored.upper], [authored]);
  const [picked, setPicked] = useState<string | null>(null);
  const letter = pickable.find((l) => l.glyph === picked) ?? pickable[0];

  if (!source) return null;

  // Right side of a pair is always lowercase; the left side may also be a
  // capital — so a lowercase letter gets both directions, a capital only the
  // "as first letter" row.
  const asFirst = letter ? authored.lower.map((r) => letter.glyph + r.glyph) : [];
  const asSecond =
    letter && letter.group === 'lower'
      ? [...authored.lower, ...authored.upper].filter((l) => l.glyph !== letter.glyph).map((l) => l.glyph + letter.glyph)
      : [];

  return (
    <Box sx={{ overflowY: 'auto', height: '100%', p: { xs: 2, md: 3 } }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6">{de.admin.pairs.title}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 720 }}>
          {de.admin.pairs.intro}
        </Typography>
      </Box>

      {pickable.length === 0 ? (
        <Alert severity="info">{de.admin.pairs.empty}</Alert>
      ) : (
        <>
          <Box sx={{ display: 'flex', alignItems: 'baseline', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
              {de.admin.pairs.pickLetter}
            </Typography>
            {pickable.map((l) => (
              <ButtonBase
                key={l.glyph}
                onClick={() => setPicked(l.glyph)}
                sx={{
                  fontFamily: garamond,
                  fontSize: 20,
                  lineHeight: 1,
                  px: 1,
                  py: 0.5,
                  borderRadius: 1,
                  border: 1,
                  borderColor: letter?.glyph === l.glyph ? 'primary.main' : 'divider',
                  bgcolor: letter?.glyph === l.glyph ? 'action.selected' : 'transparent',
                }}
              >
                {l.glyph}
              </ButtonBase>
            ))}
          </Box>

          {letter && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <Box>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  {fmt(de.admin.pairs.asFirst, { glyph: letter.glyph })}
                </Typography>
                <CellGrid pairs={asFirst} sourceId={sourceId} />
              </Box>
              {asSecond.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>
                    {fmt(de.admin.pairs.asSecond, { glyph: letter.glyph })}
                  </Typography>
                  <CellGrid pairs={asSecond} sourceId={sourceId} />
                </Box>
              )}
            </Box>
          )}
        </>
      )}
    </Box>
  );
}
