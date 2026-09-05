// The ONE way a template's image-space quality is shown in the admin: the
// colour-coded score chip and the per-category penalty breakdown ("where did
// the score go").
//
// These two used to live inside the setup wizard, where the number was born,
// and every other surface then either re-implemented the thresholds
// (QualityView had its own copy of `scoreColor`) or showed no score at all
// (the letters overview). Same number, three treatments — so the same letter
// could look fine in one place and unrated in the next. One home now: the
// wizard preview, the Diagnose modal and the Buchstaben overview all render a
// score through these.

import { Box, Chip, LinearProgress, Stack, Tooltip, Typography } from '@mui/material';

import type { QualityData } from '@/lib/api';
import { de } from '@/locales/admin';
import { labelColumnChars } from './labelColumn';

// Module-private on purpose: a score reaches the screen through ScoreChip, so
// there is exactly one place where a threshold can be changed.
function scoreColor(score: number): 'success' | 'warning' | 'error' {
  if (score >= 85) return 'success';
  if (score >= 70) return 'warning';
  return 'error';
}

/** „Score 81,4" in the score's own colour — the same chip everywhere. */
export function ScoreChip({ score, title }: { score: number; title?: string }) {
  const chip = (
    <Chip size="small" color={scoreColor(score)} label={`${de.wizard.optimize.score} ${score.toFixed(1)}`} />
  );
  // describeChild: the hint explains the score, it does not rename the chip
  // (a label tooltip would hide the visible „Score 81,4" from screen readers).
  return title ? (
    <Tooltip title={title} describeChild>
      {chip}
    </Tooltip>
  ) : (
    chip
  );
}

// Naturalness-metric components shown as the per-category penalty breakdown
// (Sütterlin/Gleichzug only — the Kurrent metric carries no `components`). Order
// mirrors the glyph bench's stdout; `naturalness` is the aggregate, not a
// category, so it's excluded here.
type ComponentKey = 'smoothness' | 'verticality' | 'corner' | 'collinearity' | 'retrace' | 'coverage';
const COMPONENT_KEYS: ComponentKey[] = ['smoothness', 'verticality', 'corner', 'collinearity', 'retrace', 'coverage'];
const NOTABLE_PENALTY = 0.15; // mirrors glyphlab's _SCORE_HI — a deduction worth flagging
const PENALTY_EPS = 0.005; // below this a category is effectively perfect / not applicable
const BAR_FULL_PENALTY = 0.3; // penalty mapped to a full bar (penalties rarely exceed this)

// The bar starts where the LONGEST label ends. A fixed 78 px column fitted
// about nine characters, so „Deckungslücke" ran 32 px past its box and painted
// over its own bar (author report on PR #533). The labels are set in a
// monospace face, so one `ch` is one character and the widest label's character
// count IS the column width — measured from the strings themselves, so a
// renamed category re-measures itself. The extra pixel absorbs the subpixel
// rounding of a fractional advance: the box must round UP, or the longest label
// clips by a pixel.
//
// Sized over ALL categories, not just the rows on screen: a category below
// `PENALTY_EPS` drops out, and a column that shrank with it would put the two
// cards' bars at different x.
const LABEL_COL_WIDTH = `calc(${labelColumnChars(COMPONENT_KEYS.map((key) => de.wizard.optimize.cat[key]))}ch + 1px)`;

function penaltyColor(val: number): 'error' | 'warning' | 'primary' {
  if (val >= 0.25) return 'error';
  if (val >= NOTABLE_PENALTY) return 'warning';
  return 'primary';
}

function penaltyRows(quality: QualityData): { key: ComponentKey; val: number }[] {
  const c = quality.components;
  if (!c) return [];
  return COMPONENT_KEYS.map((key) => ({ key, val: c[key] }))
    .filter((r) => r.val >= PENALTY_EPS)
    .sort((a, b) => b.val - a.val);
}

// "Where did the points go" — the optimized form's deductions per category,
// sorted worst-first, just like the glyph bench / glyphlab caption.
export function ScoreBreakdown({
  quality,
  heading,
  hint,
}: {
  quality: QualityData;
  heading?: string;
  hint?: string;
}) {
  const t = de.wizard.optimize;
  if (!quality.components) return null; // Kurrent metric: no per-category breakdown
  const rows = penaltyRows(quality);
  return (
    <Stack spacing={0.75} sx={{ maxWidth: 360 }}>
      {/* The wizard heading says „(optimiert)" because it breaks down the
          PREVIEW of a re-derivation; a surface showing a stored form passes its
          own wording rather than claiming an optimisation that never ran. */}
      <Typography variant="caption" color="text.secondary">
        {heading ?? t.breakdownHeading}
      </Typography>
      {rows.length === 0 ? (
        <Typography variant="caption" color="success.main">
          {t.breakdownNone}
        </Typography>
      ) : (
        rows.map((r) => {
          const color = penaltyColor(r.val);
          return (
            <Box key={r.key} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Tooltip title={t.catHint[r.key]} placement="left" describeChild>
                {/* tabIndex so keyboard focus (not just hover) triggers the hint */}
                <Typography
                  variant="caption"
                  tabIndex={0}
                  sx={{ width: LABEL_COL_WIDTH, flexShrink: 0, fontFamily: 'monospace', cursor: 'help' }}
                >
                  {t.cat[r.key]}
                </Typography>
              </Tooltip>
              <LinearProgress
                variant="determinate"
                value={Math.min(r.val / BAR_FULL_PENALTY, 1) * 100}
                color={color}
                sx={{ flex: 1, height: 6, borderRadius: 1, opacity: r.val >= NOTABLE_PENALTY ? 1 : 0.5 }}
              />
              <Typography
                variant="caption"
                sx={{ width: 36, textAlign: 'right', fontFamily: 'monospace' }}
                color={color === 'primary' ? 'text.secondary' : `${color}.main`}
              >
                {r.val.toFixed(2)}
              </Typography>
            </Box>
          );
        })
      )}
      <Typography variant="caption" color="text.disabled">
        {hint ?? t.breakdownHint}
      </Typography>
    </Stack>
  );
}

/** The same deductions in one line — for a grid tile, where the full bar chart
 *  would outweigh the letter it belongs to. Same order, same wording, same
 *  colours, so it reads as a short form of the breakdown and not as a second
 *  metric. */
export function ScoreBreakdownInline({ quality }: { quality: QualityData }) {
  const t = de.wizard.optimize;
  if (!quality.components) return null;
  const rows = penaltyRows(quality);
  if (rows.length === 0) {
    return (
      <Typography variant="caption" color="success.main">
        {t.breakdownNone}
      </Typography>
    );
  }
  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.25, alignItems: 'baseline' }}>
      {/* The direction, which the bar-chart variant states under its bars and
          this one had nowhere to put: without it a bare „0.99" beside a
          category name reads as a score, not as the deduction it is. */}
      <Typography variant="caption" color="text.disabled">
        {t.breakdownInlinePrefix}
      </Typography>
      {rows.map((r) => {
        const color = penaltyColor(r.val);
        return (
          <Tooltip key={r.key} title={t.catHint[r.key]} describeChild>
            <Typography variant="caption" tabIndex={0} sx={{ cursor: 'help', color: 'text.secondary' }}>
              {t.cat[r.key]}{' '}
              <Box
                component="span"
                sx={{ fontFamily: 'monospace', color: color === 'primary' ? 'text.secondary' : `${color}.main` }}
              >
                {r.val.toFixed(2)}
              </Box>
            </Typography>
          </Tooltip>
        );
      })}
    </Box>
  );
}
