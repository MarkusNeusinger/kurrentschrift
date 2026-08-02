// „Gemessen" — the one compact chip row a pair card carries between its header
// and the specimen/composition body (Handmodell H2, handmodell-stufenplan.md
// §4). Numbers only, deliberately: the median-connector SKETCH lives in the
// Werkbank's pair lens, and a registered overlay of the measured connector on
// the composed pair is out of scope — the frames differ, and a false
// superposition would read as evidence.
//
// The chips carry the two numbers that decide whether a visibly-off join is
// worth a task: how many occurrences the hand actually has for it, and how far
// the GENERATOR sits from the measured median (`gen_chamfer`, the audit number
// this layer exists for). Everything else — the spread, the fit residuals, the
// offset, the plate mix — hangs in the tooltip, in the order the doctrine
// triages.
//
// Honesty rules carried over from the Werkbank blocks: an absent measurement is
// never printed as a measured zero (no `± 0,00` without a stored MAD), the hand
// is named rather than implied, and a card without an aggregate row says WHICH
// of the four possible reasons applies — „keine Messung" is reserved for the one
// case it actually describes (the layer is loaded and holds rows, just none for
// this join), never used for a read that is still running, was never rebuilt,
// has no hand or could not be loaded at all.

import { Box, Chip, Tooltip, Typography } from '@mui/material';

import { de, fmt, specimenKindLabel } from '@/locales/admin';
import { pairKeyOf } from '@/sections/admin/werkbank/model';

import { countForHand, pairFitUncertain, type AggregateLayerState, type PairMeasurements } from './pairMeasurement';

const num = (value: number, digits: number): string => value.toFixed(digits);

// The offset and its spread come from JSONB — only a finite 2-vector may be
// printed, on both sides of the ± (a NaN MAD would otherwise reach `toFixed`).
const isPoint = (p: unknown): p is number[] =>
  Array.isArray(p) && p.length >= 2 && Number.isFinite(p[0]) && Number.isFinite(p[1]);

// Why this card has no measured median — the short inline word and, for the
// tooltip, the Werkbank's full sentence for the SAME state. `null` while the
// layer is still in flight: nothing is known yet, so nothing is claimed.
function aggregateReason(state: AggregateLayerState): { chip: string; line: string } | null {
  const t = de.admin.compare;
  const w = de.admin.werkbank;
  if (state.status === 'loading') return null;
  if (state.status === 'no-hand') return { chip: t.measuredNoHand, line: w.statsNoHand };
  if (state.status === 'unavailable') return { chip: t.measuredNoAccess, line: w.statsUnavailable };
  if (state.layerEmpty) return { chip: t.measuredNoRebuild, line: w.statsNoRebuild };
  return { chip: t.measuredNone, line: w.statsNonePair };
}

export function PairMeasuredChips({
  measurements,
  leftKey,
  rightKey,
  specimenId,
}: {
  measurements: PairMeasurements;
  leftKey: string;
  rightKey: string;
  specimenId: string;
}) {
  const t = de.admin.compare;
  // The tooltip deliberately reuses the Werkbank's wording for the shared
  // numbers: the two read surfaces show the SAME aggregate, so they must name
  // it identically — a second phrasing would drift.
  const w = de.admin.werkbank;

  if (measurements.status !== 'ready') return null;

  const key = pairKeyOf(leftKey, rightKey);
  const occurrences = measurements.occurrencesByKey.get(key) ?? [];
  const aggregate = measurements.aggregateByKey.get(key);
  const meanStats = aggregate?.mean_stats ?? {};
  const offset = aggregate?.offset_center;
  const offsetMad = aggregate?.hull.offset_mad;
  const kinds = Object.entries(meanStats.kinds ?? {});
  const uncertain = pairFitUncertain(occurrences, specimenId);
  // The aggregate's own count when the layer is there, the matched occurrences
  // OF THE NAMED HAND otherwise — the occurrence list is public, so a card keeps
  // a number even without the admin-gated aggregates, but the tooltip credits
  // that number to one writer and must not mix a second hand into it.
  const count = aggregate?.n_instances ?? countForHand(occurrences, measurements.handId);
  const reason = aggregate ? null : aggregateReason(measurements.aggregates);

  const lines: string[] = [];
  if (measurements.handId) lines.push(`${w.statsPairHeading} · ${fmt(w.statsHand, { hand: measurements.handId })}`);
  if (measurements.handsMixed && measurements.handId) {
    lines.push(fmt(w.statsMixedHands, { hand: measurements.handId }));
  }
  lines.push(fmt(w.statsInstances, { count }));
  if (meanStats.n_specimens !== undefined) lines.push(fmt(w.statsSpecimens, { count: meanStats.n_specimens }));
  if (meanStats.gen_chamfer) {
    lines.push(
      fmt(w.statsGenChamfer, { mean: num(meanStats.gen_chamfer.mean, 3), max: num(meanStats.gen_chamfer.max, 3) }),
    );
  }
  if (meanStats.harvest_chamfer) lines.push(fmt(w.statsHarvestChamfer, { value: num(meanStats.harvest_chamfer.mean, 3) }));
  if (meanStats.resid) {
    lines.push(fmt(w.statsResid, { mean: num(meanStats.resid.mean, 3), max: num(meanStats.resid.max, 3) }));
  }
  if (isPoint(offset)) {
    // Without a stored MAD the ± clause is dropped entirely.
    lines.push(
      isPoint(offsetMad)
        ? fmt(w.statsOffset, {
            x: num(offset[0], 2),
            y: num(offset[1], 2),
            madX: num(offsetMad[0], 2),
            madY: num(offsetMad[1], 2),
          })
        : fmt(w.statsOffsetNoMad, { x: num(offset[0], 2), y: num(offset[1], 2) }),
    );
  }
  if (meanStats.gap_ink_share !== undefined) lines.push(fmt(w.statsGapInk, { value: num(meanStats.gap_ink_share, 2) }));
  if (kinds.length > 0) {
    lines.push(`${w.statsKindsLabel}: ${kinds.map(([kind, n]) => `${specimenKindLabel(kind)} ${n}`).join(' · ')}`);
  }
  if (reason) lines.push(reason.line);
  if (uncertain) lines.push(t.measuredFitHint);

  return (
    <Tooltip
      title={
        <Box>
          {lines.map((line) => (
            <Typography key={line} variant="caption" sx={{ display: 'block' }}>
              {line}
            </Typography>
          ))}
        </Box>
      }
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, flexWrap: 'wrap' }}>
        <Typography variant="caption" color="text.secondary">
          {`${t.measuredLabel}:`}
        </Typography>
        <Chip size="small" variant="outlined" label={fmt(w.statsInstances, { count })} />
        {meanStats.gen_chamfer && (
          <Chip
            size="small"
            variant="outlined"
            label={fmt(t.measuredGenChamfer, { value: num(meanStats.gen_chamfer.mean, 3) })}
          />
        )}
        {reason && (
          <Typography variant="caption" color="text.disabled">
            {reason.chip}
          </Typography>
        )}
        {uncertain && <Chip size="small" color="warning" variant="outlined" label={t.measuredFitWarn} />}
      </Box>
    </Tooltip>
  );
}
