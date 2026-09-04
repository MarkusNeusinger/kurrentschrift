// TafelSkeleton — what `/tafel` shows while useGrundtafeln loads: the page's own
// three sections at their finished HEIGHT, not a spinner.
//
// Why the height and not a spinner: the route's entire measured CLS is one shift.
// Until `/sources` answers, the document is exactly one viewport tall, so the
// footer stands inside the viewport; when the three sections mount at once the
// document jumps to 3132 px (mobile) / 4494 px (desktop) and the footer leaves
// it — 0.097 / 0.112 (frontend-stack.md, „CLS auf /tafel", measured for #517).
// Reserving each section's box up front means nothing that is already on screen
// moves when the data lands.
//
// What is reserved, per script: the real heading and the real Feder caption
// (both are fixed German copy, so they can be drawn at once and never move), a
// box the size of the state chip, the plate's box at its own aspect ratio
// (RESERVED_CHART_RATIO), and the provenance card. The Original/Geschrieben
// toggle is NOT reserved — it exists only on the written script, knowing which
// one that is would mean knowing the data, and it sits below the fold on both
// viewports, where a shift costs nothing.
//
// The shimmer is MUI's wave; `prefers-reduced-motion` turns it off entirely
// (`animation={false}`) rather than leaving a 1.6 s loop running under a user
// who asked for stillness.

import { Box, Paper, Skeleton, Stack, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { visuallyHidden } from '@mui/utils';

import { CategoryHeading } from '@/components/CategoryHeading';
import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion';
import { de } from '@/locales';
import { styleLabel } from '@/locales/de/common';
import { RESERVED_CHART_RATIO, STYLE_ORDER } from '@/sections/tafel/useGrundtafeln';
import { paper } from '@/styles/paper';

// MUI's default skeleton grey is a cool neutral and reads as a hole cut in the
// warm paper. The reserved boxes take the ink at low opacity instead, so an
// empty section still belongs to the page it is holding open.
const TINT = alpha(paper.ink, 0.07);

// The state chip's own box (MUI Chip size="small": 24 px tall), reserved so the
// caption row — which IS above the fold on the first script — keeps its height
// when the real label arrives.
const CHIP_W = 148;
const CHIP_H = 24;

// The provenance card's five lines — „Über die Vorlage", the plate's title, the
// attribution, the licence and the origin link — at the heights they render at
// (measured on the live card: 235 px total at 390 px, 192 px from md up). Only
// the attribution differs between the two: it is one line on a wide screen and
// three on a phone, which is the whole 43 px.
const PROVENANCE_LINES = [
  { key: 'heading', w: '38%', h: 28 },
  { key: 'title', w: '72%', h: 27 },
  { key: 'attribution', w: '100%', h: { xs: 65, md: 22 } },
  { key: 'license', w: '54%', h: 22 },
  { key: 'link', w: '30%', h: 27 },
];

type PlaceholderProps = {
  styleId: string;
  /** The first section carries the page's one spoken status and the cold-start line. */
  lead?: boolean;
  waking?: boolean;
};

function GrundtafelPlaceholder({ styleId, lead = false, waking = false }: PlaceholderProps) {
  const reduced = usePrefersReducedMotion();
  const animation = reduced ? (false as const) : ('wave' as const);
  const ratio = RESERVED_CHART_RATIO[styleId] ?? '4 / 3';
  const notice = lead && waking ? de.common.boot.sourceColdStart : null;

  return (
    <Stack component="section" spacing={2} aria-label={styleLabel(styleId)}>
      <Box sx={{ position: 'relative' }}>
        {/* One spoken status for the whole page, parked in the first section's
            heading block: `visuallyHidden` is absolutely positioned, so it takes
            no room in the Stack that spaces the sections. */}
        {lead && (
          <Box component="p" role="status" sx={visuallyHidden}>
            {notice ?? de.common.boot.loadingTemplate}
          </Box>
        )}
        <CategoryHeading>{styleLabel(styleId)}</CategoryHeading>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
          <Typography variant="body2" sx={{ color: paper.inkSoft }}>
            {de.tafel.feder[styleId]}
          </Typography>
          <Skeleton variant="rounded" animation={animation} sx={{ width: CHIP_W, height: CHIP_H, bgcolor: TINT }} />
        </Box>
      </Box>

      {/* The plate's box, in the same outlined white Paper OriginalScan uses. */}
      <Paper variant="outlined" sx={{ p: 1, bgcolor: '#fff' }}>
        {/* The ratio sits on the BOX, not on the Skeleton: MUI gives its root an
            own height, which wins over an `aspect-ratio` and made all three
            plates the same size. The Skeleton just fills the reserved box. */}
        <Box sx={{ position: 'relative', width: '100%', aspectRatio: ratio }}>
          <Skeleton
            variant="rectangular"
            animation={animation}
            sx={{ position: 'absolute', inset: 0, width: '100%', height: '100%', bgcolor: TINT }}
          />
          {/* The cold-start line lives INSIDE the reserved box, so saying it
              costs no layout at all. Cloud Run can take ~a minute to wake. */}
          {notice ? (
            <Box
              sx={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                p: 3,
              }}
            >
              <Typography aria-hidden variant="body2" sx={{ color: paper.inkSoft, textAlign: 'center', maxWidth: '34ch' }}>
                {notice}
              </Typography>
            </Box>
          ) : null}
        </Box>
      </Paper>

      {/* The provenance card's box. */}
      <Paper variant="outlined" sx={{ p: 2, bgcolor: paper.hi }}>
        <Stack spacing={1}>
          {PROVENANCE_LINES.map((line) => (
            // `height` goes through sx, not the prop — the prop takes a number
            // or string, never a responsive object.
            <Skeleton key={line.key} variant="rounded" animation={animation} sx={{ width: line.w, height: line.h, bgcolor: TINT }} />
          ))}
        </Stack>
      </Paper>
    </Stack>
  );
}

/**
 * The three reserved sections, in the page's own order. `waking` shows the
 * cold-start line inside the first reserved plate box.
 *
 * Returns a fragment on purpose: the caller's `<Stack>` spaces the sections, and
 * a wrapper element would collapse the three gaps into one.
 */
export function TafelSkeleton({ waking }: { waking: boolean }) {
  return (
    <>
      {STYLE_ORDER.map((styleId, i) => (
        <GrundtafelPlaceholder key={styleId} styleId={styleId} lead={i === 0} waking={waking} />
      ))}
    </>
  );
}
