// Shared wizard vocabulary: the step sequence, the resolved guide values the
// canvas and step panels read, and the commit-callback signatures the canvas
// uses to hand a finished gesture to the wizard (which validates + persists).

import type { CouplingHeight } from '@/lib/api';

export type StepId = 'mask' | 'lineatur' | 'slant' | 'weg' | 'overview';
export const STEPS: { id: StepId; label: string }[] = [
  { id: 'mask', label: 'Ausschluss' },
  { id: 'lineatur', label: 'Lineatur' },
  { id: 'slant', label: 'Schräge' },
  { id: 'weg', label: 'Weg' },
  { id: 'overview', label: 'Übersicht' },
];

// Signal green for the slant guides (canvas lines/handles and the Schräge
// panel's accents). Deliberately distinct from overlayColors' locked green.
export const SLANT_COLOR = '#39d98a';

// Guide values resolved from bbox.guides + source defaults (the wizard's
// guideVals memo) — slantXs already carries the legacy single-slant_x fallback.
export interface GuideValues {
  slantDeg: number;
  slantXs: number[];
  showAscender: boolean;
  showDescender: boolean;
  entryCoupling: CouplingHeight;
  exitCoupling: CouplingHeight;
}

// The two draggable lineature lines on the Lineatur step.
export type CalibField = 'baseline_y' | 'midband_y';

// Gesture-commit callbacks: WizardCanvas owns the in-flight gesture state and
// calls these on pointer-up with the gesture's final values.
export type CommitCalib = (field: CalibField, curY: number) => Promise<void>;
export type CommitSlant = (index: number, curX: number) => Promise<void>;
export type CommitMaskStroke = (points: Array<[number, number]>) => Promise<void>;
