// Small shared building blocks for the quiz surface (design handoff "Tinte &
// Vergleich"): the dark "ink" CTA, the setup option chip and the per-screen
// eyebrow. Kept together so the three panels can't drift on these primitives.

import { Box, Button, ButtonBase, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import type { ReactNode, Ref } from 'react';

import { garamond, paper, quiz, quizRadius } from '@/styles/paper';

// The dark "ink" call-to-action ("Quiz starten →", "Weiter →", "Weiter üben →").
// Full width on mobile, inline on desktop.
export function InkButton({
  onClick,
  children,
  fullWidthMobile = true,
  disabled,
  buttonRef,
}: {
  onClick: () => void;
  children: ReactNode;
  fullWidthMobile?: boolean;
  disabled?: boolean;
  // Underlying <button> element, for callers that move focus programmatically
  // (the play panel focuses "Weiter" after a wrong pick disables the grid).
  buttonRef?: Ref<HTMLButtonElement>;
}) {
  return (
    <Button
      ref={buttonRef}
      onClick={onClick}
      disabled={disabled}
      sx={{
        bgcolor: paper.ink,
        color: paper.hi,
        fontFamily: garamond,
        fontSize: 17,
        letterSpacing: '0.02em',
        px: { xs: 3, sm: 4.5 },
        py: 1.25,
        borderRadius: '6px',
        boxShadow: '0 4px 14px rgba(36,26,16,0.22)',
        width: fullWidthMobile ? { xs: '100%', sm: 'auto' } : 'auto',
        '&:hover': { bgcolor: paper.inkSoft, boxShadow: '0 6px 18px rgba(36,26,16,0.26)' },
        '&.Mui-disabled': { bgcolor: paper.lo, color: paper.sepia, boxShadow: 'none' },
      }}
    >
      {children}
    </Button>
  );
}

// A setup option chip: a viridian-ringed, dot-marked pill when selected; a quiet
// hairline pill otherwise. `soon` appends the "bald" marker for not-yet-available
// options (Kurrent / Offenbacher, the rougher difficulties).
export function OptionChip({
  selected,
  disabled,
  soon,
  soonLabel,
  onClick,
  children,
}: {
  selected: boolean;
  disabled?: boolean;
  soon?: boolean;
  soonLabel?: string;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <ButtonBase
      disabled={disabled}
      onClick={onClick}
      aria-pressed={selected}
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 0.75,
        px: 2,
        py: 1,
        borderRadius: quizRadius,
        border: '1px solid',
        borderWidth: selected ? '1.5px' : '1px',
        borderColor: selected ? paper.viridian : quiz.border,
        bgcolor: selected ? alpha(paper.viridian, 0.1) : 'transparent',
        color: selected ? paper.ink : paper.sepia,
        fontFamily: garamond,
        fontSize: { xs: 16, sm: 16.5 },
        opacity: disabled ? 0.5 : 1,
        transition: 'border-color 120ms ease, color 120ms ease, background-color 120ms ease',
        '&:hover': disabled ? {} : { borderColor: paper.viridian, color: paper.ink },
      }}
    >
      {selected && (
        <Box aria-hidden sx={{ width: 7, height: 7, borderRadius: '50%', bgcolor: paper.viridian, flexShrink: 0 }} />
      )}
      {children}
      {soon && soonLabel && (
        <Typography component="span" variant="caption" sx={{ ml: 0.25, color: 'text.disabled' }}>
          {soonLabel}
        </Typography>
      )}
    </ButtonBase>
  );
}

// A small per-screen eyebrow (viridian dot + tracked uppercase label), matching
// the handoff's "● EINRICHTUNG / ● AUSWERTUNG" markers.
export function QuizEyebrow({ children }: { children: ReactNode }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Box aria-hidden sx={{ width: 7, height: 7, borderRadius: '50%', bgcolor: paper.viridian }} />
      <Typography
        variant="overline"
        sx={{ color: paper.sepia, textTransform: 'uppercase', letterSpacing: '0.1em', lineHeight: 1 }}
      >
        {children}
      </Typography>
    </Box>
  );
}

// A quiet inline text affordance (the play screen's "Abbrechen", the results
// screen's "Einstellungen"): garamond, sepia, viridian on hover. One primitive
// so the two read identically instead of each rolling its own button reset.
export function QuietButton({ onClick, children }: { onClick: () => void; children: ReactNode }) {
  return (
    <ButtonBase
      onClick={onClick}
      sx={{
        fontFamily: garamond,
        fontSize: 15,
        color: paper.sepia,
        px: 0.5,
        borderRadius: quizRadius,
        transition: 'color 120ms ease',
        '&:hover': { color: paper.viridian },
      }}
    >
      {children}
    </ButtonBase>
  );
}
