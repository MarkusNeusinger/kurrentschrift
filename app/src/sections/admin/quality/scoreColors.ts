// Which colour a score NUMBER is written in — its own module because
// `scoreParts.tsx` may only export components (react-refresh), the same reason
// `labelColumn.ts` sits beside it.
//
// It is a separate question from the colour of the BAR next to the number, and
// the split is the whole point: a bar is a graphical mark and needs 3:1
// (WCAG 1.4.11), a number is text and needs 4,5:1. The palette's `warning`
// (Ocker `#cc7722`) clears the first and fails the second — 3,37:1 on white and
// less on the card ground — so the warning tier keeps ink here while its bar
// stays ochre (design-system.md §2/§9).
//
// Everything below is meant for `sx`, never for a `color` prop: that prop
// resolves simple palette keys only, and a dotted path there is inert (#628).

import { paper } from '@/styles/paper';

/** Severity tiers of one penalty category, worst first. */
export type PenaltyTier = 'error' | 'warning' | 'primary';

/**
 * Below this a deduction is effectively none. Here rather than in
 * `scoreParts.tsx` because it has a second reader: the Abzugs-Linse uses the
 * same step to decide when the stamped list value and today's re-score
 * disagree enough to print the „gespeichert" line — one threshold, one home.
 */
export const PENALTY_EPS = 0.005;

/** The penalty number's text colour per tier — soft ink → ink → oxblood, so the
 *  ladder still rises monotonically without reaching for an unreadable tone. */
export const PENALTY_TEXT_COLOR: Record<PenaltyTier, string> = {
  primary: 'text.secondary',
  warning: 'text.primary',
  error: 'error.main',
};

/**
 * „Δ +3,4" — the score delta the setup wizard prints beside the chip on two of
 * its steps. Raw Viridian is 3,72:1 on the card ground, so an improvement takes
 * the viridian TEXT shade; oxblood `error.main` is 7,41:1 and needs no
 * substitute.
 */
export const scoreDeltaColor = (delta: number): string => (delta >= 0 ? paper.viridianText : 'error.main');
