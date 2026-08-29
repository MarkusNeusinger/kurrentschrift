// SpecimenStrip — a row of letters "as written" (WrittenGlyph) on their own
// hairline surface, each labelled with its Antiqua letter: the marked specimen
// of design-system §9 for prose that talks about letter forms (the
// Schriftkunde's Buchstaben-Besonderheiten, the Lesart page's confusable
// pairs). A click writes a letter again.
//
// Data flow (payloads.ts): the PAGE fetches the render payloads of all its
// specimens in ONE batch (`useSpecimenPayloads`, renderCache →
// /write/glyphs?keys=…) as soon as the section comes near, and hands the map
// down; every cell renders from `data` and fetches nothing itself. A strip
// mounts its cells only in view, so the write-in plays when the reader
// arrives rather than at page load below the fold. While the batch is in
// flight the frame holds the space; once it has answered and none of the
// strip's glyphs can be written (no canonical, engine unreachable) the strip
// withdraws entirely — no empty frame, no error box inside public prose.

import { Box, ButtonBase, Typography } from '@mui/material';
import type { SxProps, Theme } from '@mui/material/styles';
import { useState } from 'react';

import type { Specimen, SpecimenPayloads } from '@/components/SpecimenStrip/payloads';
import { WrittenGlyph } from '@/components/WrittenGlyph';
import { useInView } from '@/hooks/useInView';
import type { GlyphRenderData } from '@/lib/api';
import { de } from '@/locales';
import { garamond, paper } from '@/styles/paper';

// One written form with its Antiqua label; a click writes it again (remount —
// the payload is already here, only the reveal restarts).
function SpecimenCell({ glyphKey, label, data, height }: { glyphKey: string; label: string; data: GlyphRenderData; height: number }) {
  const [run, setRun] = useState(0);
  return (
    <ButtonBase
      onClick={() => setRun((r) => r + 1)}
      aria-label={`${label} — ${de.common.writtenGlyph.replay}`}
      sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5, px: 0.5, borderRadius: '3px' }}
    >
      <Box sx={{ height, display: 'flex', alignItems: 'center' }}>
        <WrittenGlyph key={run} glyphKey={glyphKey} data={data} height={height} surfaceBg="transparent" showReplay={false} />
      </Box>
      <Typography variant="caption" component="span" aria-hidden sx={{ fontFamily: garamond, fontStyle: 'italic', color: paper.sepia, lineHeight: 1 }}>
        {label}
      </Typography>
    </ButtonBase>
  );
}

interface SpecimenStripProps {
  specimens: readonly Specimen[];
  payloads: SpecimenPayloads | null;
  /** Rendered glyph height in px (the full ascender..descender lineature, so
   *  every letter of a strip shares one scale). */
  height?: number;
  sx?: SxProps<Theme>;
}

export function SpecimenStrip({ specimens, payloads, height = 84, sx }: SpecimenStripProps) {
  const [ref, inView] = useInView<HTMLDivElement>('120px');
  const forms = specimens.map((s) => ({ ...s, data: payloads?.get(s.key) ?? null }));
  if (payloads && forms.every((f) => !f.data)) return null;
  return (
    <Box
      ref={ref}
      sx={[
        {
          display: 'flex',
          alignItems: 'flex-end',
          gap: 1,
          px: 1.25,
          py: 0.75,
          minHeight: height + 30,
          border: `1px solid ${paper.line}`,
          borderRadius: '3px',
          bgcolor: paper.hi,
          flexShrink: 0,
        },
        ...(Array.isArray(sx) ? sx : [sx]),
      ]}
    >
      {inView &&
        forms.map((f, i) => f.data && <SpecimenCell key={`${f.key}-${i}`} glyphKey={f.key} label={f.label} data={f.data} height={height} />)}
    </Box>
  );
}
