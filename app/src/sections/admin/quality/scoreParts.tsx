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

import { Box, Chip, LinearProgress, Stack, Typography } from '@mui/material';

import { InfoHint } from '@/components/InfoHint';
import type { QualityData } from '@/lib/api';
import { de } from '@/locales/admin';
import { mono } from '@/styles/paper';
import { labelColumnChars } from './labelColumn';

// Module-private on purpose: a score reaches the screen through ScoreChip, so
// there is exactly one place where a threshold can be changed.
function scoreColor(score: number): 'success' | 'warning' | 'error' {
  if (score >= 85) return 'success';
  if (score >= 70) return 'warning';
  return 'error';
}

/** „Score 81,4" in the score's own colour — the same chip everywhere.
 *
 *  It carries no `Tooltip` of its own any more: the chip is a plain `div`, so
 *  MUI never made that hint focusable and it existed for the mouse alone — and
 *  what it said (stamped at the last derivation, not recomputed) is exactly the
 *  kind of caveat V25 forbids hiding there. It lives in `ScoreHelp` now, which
 *  every surface showing a score renders once. */
export function ScoreChip({ score }: { score: number }) {
  return <Chip size="small" color={scoreColor(score)} label={`${de.wizard.optimize.score} ${score.toFixed(1)}`} />;
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

/**
 * The score vocabulary of a row, behind ONE focusable affordance: what the
 * number is, why a form can carry none, what the Fit mean says, which way the
 * deductions run, and what each category means.
 *
 * This replaces up to NINE hover-only hints per row — six category tooltips on
 * bare `tabIndex={0}` spans of ~22 px, plus the ones on the score, „kein Score"
 * and „Fit ⌀" chips. The six spans were tab stops that wore no focus ring (a
 * `Typography` has no focus-visible rule), so a Buchstaben list page offered up
 * to 72 extra ringless stops and reached none of the text by touch.
 *
 * `InfoHint` is the repo's non-hover disclosure: a real button with the shared
 * ring and a 44 px hit area, opening on click and therefore on a finger too.
 * The rule is ONE per row — the explanation belongs to the row, not to every
 * number in it (design-system.md §9.4).
 */
export function ScoreHelp() {
  const t = de.wizard.optimize;
  const c = de.admin.compare;
  return (
    <InfoHint title={t.breakdownHelpTitle} label={t.breakdownHelpAria}>
      <Stack spacing={0.75}>
        <Typography variant="body2">{c.scoreHint}</Typography>
        <Typography variant="body2">{c.scoreNoneHint}</Typography>
        <Typography variant="body2">{c.fitMeanHint}</Typography>
        <Typography variant="body2">{t.breakdownHint}</Typography>
        {/* One line per category, the name in the same monospace the bars use
            so the popover reads as the legend of what is on screen. A
            definition list with its own column looked like a second table in a
            320 px popover. */}
        <Box component="dl" sx={{ m: 0 }}>
          {COMPONENT_KEYS.map((key) => (
            <Typography key={key} component="dd" variant="body2" sx={{ m: 0, color: 'text.secondary' }}>
              <Box component="span" sx={{ fontFamily: mono, color: 'text.primary' }}>
                {t.cat[key]}
              </Box>
              {` — ${t.catHint[key]}`}
            </Typography>
          ))}
        </Box>
      </Stack>
    </InfoHint>
  );
}

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
          own wording rather than claiming an optimisation that never ran.

          The one help of the block sits ON the heading — the category labels
          below are plain text again, not six tab stops carrying six hovers. */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        <Typography variant="caption" color="text.secondary">
          {heading ?? t.breakdownHeading}
        </Typography>
        <ScoreHelp />
      </Box>
      {rows.length === 0 ? (
        <Typography variant="caption" color="success.main">
          {t.breakdownNone}
        </Typography>
      ) : (
        rows.map((r) => {
          const color = penaltyColor(r.val);
          return (
            <Box key={r.key} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="caption" sx={{ width: LABEL_COL_WIDTH, flexShrink: 0, fontFamily: mono }}>
                {t.cat[r.key]}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={Math.min(r.val / BAR_FULL_PENALTY, 1) * 100}
                color={color}
                sx={{ flex: 1, height: 6, borderRadius: 1, opacity: r.val >= NOTABLE_PENALTY ? 1 : 0.5 }}
              />
              <Typography
                variant="caption"
                sx={{ width: 36, textAlign: 'right', fontFamily: mono }}
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

/** The same deductions in one line — for a grid tile or a list row, where the
 *  full bar chart would outweigh the letter it belongs to. Same order, same
 *  wording, same colours, so it reads as a short form of the breakdown and not
 *  as a second metric.
 *
 *  The numbers are plain text and the ONE `ScoreHelp` of the row sits at the
 *  front. Until this round each category was its own `tabIndex={0}` span with
 *  its own tooltip — six ringless ~22 px stops per row, which on a list page of
 *  twelve rows is 72 tab stops that say nothing when you land on them. */
export function ScoreBreakdownInline({ quality }: { quality: QualityData }) {
  const t = de.wizard.optimize;
  const rows = quality.components ? penaltyRows(quality) : [];
  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.25, alignItems: 'center' }}>
      <ScoreHelp />
      {/* The direction, which the bar-chart variant states under its bars and
          this one had nowhere to put: without it a bare „0.99" beside a
          category name reads as a score, not as the deduction it is. */}
      <Typography variant="caption" color="text.disabled">
        {quality.components ? t.breakdownInlinePrefix : t.breakdownNoComponents}
      </Typography>
      {quality.components && rows.length === 0 && (
        <Typography variant="caption" color="success.main">
          {t.breakdownNone}
        </Typography>
      )}
      {rows.map((r) => {
        const color = penaltyColor(r.val);
        return (
          <Typography key={r.key} variant="caption" sx={{ color: 'text.secondary' }}>
            {t.cat[r.key]}{' '}
            <Box
              component="span"
              sx={{ fontFamily: mono, color: color === 'primary' ? 'text.secondary' : `${color}.main` }}
            >
              {r.val.toFixed(2)}
            </Box>
          </Typography>
        );
      })}
    </Box>
  );
}
