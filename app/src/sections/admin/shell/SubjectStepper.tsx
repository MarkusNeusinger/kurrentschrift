// The Subjekt-Stepper: the ‹ › pair in a detail head, and the one key binding
// that does the same thing without the mouse (Vorgabe V24, author decision
// P1-Q11 b — Alt+Shift+←/→).
//
// It exists as one component because all three details need the same thing and
// got none of it consistently: Buchstaben had hand-rolled ‹ › buttons and no
// keys, Übergänge and Wörter had no stepper at all. What it steps through is
// decided by `subjectNav.ts` — the order the overview published — and the
// caption that names that order is the head's `note`, because a control whose
// meaning changes with a filter has to say so where it is (§9.4: no
// decision-carrying state in a hover).
//
// The buttons keep working when the Kurztasten are switched off. Only the KEYS
// are switchable; ‹ › is a control, not a shortcut.

import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import { IconButton } from '@mui/material';
import type { ReactNode } from 'react';

import { useSubjectStepper, type SubjectStep } from '@/sections/admin/shell/useSubjectStepper';
import { TOUCH_TARGET } from '@/styles/hitArea';

export type SubjectStepperProps = SubjectStep & {
  prevLabel: string;
  nextLabel: string;
  /** What the two arrows stand around — the subject as the head draws it (the
   * letter's picker chip, the join's keys, the word). Keeping it INSIDE the
   * stepper is what makes „‹ Gegenstand ›" the same shape in all three views. */
  between: ReactNode;
};

export function SubjectStepper({ prev, next, onStep, prevLabel, nextLabel, between }: SubjectStepperProps) {
  useSubjectStepper({ prev, next, onStep });
  // Both grow to the 44px floor rather than wearing an invisible hit area: they
  // stand 8px from the subject beside them, so an overlay would steal its taps
  // (§9.3, „wo Nachbarn dicht stehen").
  const target = { width: TOUCH_TARGET, height: TOUCH_TARGET } as const;
  return (
    <>
      <IconButton size="small" disabled={!prev} aria-label={prevLabel} onClick={() => prev && onStep(prev)} sx={target}>
        <ChevronLeftIcon fontSize="small" />
      </IconButton>
      {between}
      <IconButton size="small" disabled={!next} aria-label={nextLabel} onClick={() => next && onStep(next)} sx={target}>
        <ChevronRightIcon fontSize="small" />
      </IconButton>
    </>
  );
}
