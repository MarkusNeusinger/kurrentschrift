// The Streifen-Befund of one Fassung, as the chips of its head row.

import { Chip, Stack, Typography } from '@mui/material';
import type { ReactNode } from 'react';

import type { EigenhandBefund } from '@/lib/api';
import { InfoHint } from '@/components/InfoHint';
import { de, fmt } from '@/locales/admin';
import { VORSCHLAG_COLOR } from '@/sections/admin/eigenhand/befundOrder';
import { num } from '@/sections/admin/eigenhand/readings';

/**
 * One Fassung's verdict sheet as chips: the suggestion, the dominant reason,
 * the rank among its strip's Fassungen, and — where a later Fassung came out
 * cleaner — that it has been superseded. A Fassung filed before the Befund
 * existed says so rather than showing a blank: a missing reading is not a bad
 * reading, and it must not look like one.
 *
 * `extra` rides in the same popover: the tile's head row explains ONE subject —
 * this Fassung — so it carries one `InfoHint`, not one per chip group (§9.4).
 */
export function BefundChips({
  befund,
  extra,
}: {
  befund: EigenhandBefund | null | undefined;
  extra?: ReactNode;
}) {
  const t = de.admin.eigenhand;
  if (!befund) {
    return (
      <>
        <Chip size="small" variant="outlined" label={t.befundNone} />
        <InfoHint title={t.befundNone} label={t.befundNoneAria}>
          <Stack spacing={0.75}>
            <Typography variant="body2">{t.befundNoneHint}</Typography>
            {extra}
          </Stack>
        </InfoHint>
      </>
    );
  }
  const tooltip = fmt(t.befundTooltip, {
    guete: num(befund.guete),
    feder: `${Math.round(Number(befund.nib?.zur_hand ?? 1) * 100)} %`,
    knick: num(befund.unstetigkeit?.kink_max_deg),
    knicke: String(befund.unstetigkeit?.kink_count ?? 0),
    wackler: num(befund.unstetigkeit?.wobble),
    kringel: String((befund.kringel?.zu as number | undefined) ?? 0),
  });
  return (
    <>
      <Chip size="small" color={VORSCHLAG_COLOR[befund.vorschlag]} label={befund.vorschlag} />
      <Chip size="small" variant="outlined" label={befund.grund} />
      {befund.rang !== null && befund.von !== null && befund.von > 1 && (
        <Chip size="small" variant="outlined" label={fmt(t.befundRank, { rang: befund.rang, von: befund.von })} />
      )}
      {befund.abgeloest_von && (
        <Chip
          size="small"
          variant="outlined"
          color="info"
          label={fmt(t.befundReplaced, { fassung: befund.abgeloest_von })}
        />
      )}
      {/* The six sensor readings behind the verdict, and why a Fassung was
          superseded — both were hovers over plain `div` chips, i.e. numbers a
          decision rests on that neither keyboard nor tablet could reach (V25).
          ONE InfoHint per Fassung carries the whole sheet. */}
      <InfoHint title={t.befundSheetTitle} label={t.befundSheetAria}>
        <Stack spacing={0.75}>
          <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>
            {tooltip}
          </Typography>
          {befund.abgeloest_von && <Typography variant="body2">{t.befundReplacedHint}</Typography>}
          {extra}
        </Stack>
      </InfoHint>
    </>
  );
}
