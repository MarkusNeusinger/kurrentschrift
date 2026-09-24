// „Was sagt die Tinte dieser Hand?" — the statistik Unteransicht.
//
// Of the four figures §7.2 promises this view, two are built: the nib figure
// below and the Tintentreue distribution (`TintentreuePanel`), which counts the
// per-box verdict the hand-wide read already carries (`GET
// /eigenhand/pfade/{hand}`). The other two stand as a labelled Leerfläche: the
// Ausschnitt-Stapel waits on the Fassung selection of the streifen view, and a
// dated Belegzahl history on a Bestandsverlauf nobody records. Naming them
// beats an empty page that looks like a broken one. Which of the four this
// view opens with is Q7 of the Phase-1 reconnaissance and still the author's
// call — the panels below are one prop apart from being reordered.
//
// The distribution fires its own read rather than riding the Bestand: the box
// read walks every stored path of the hand, and only this view (and the
// Nachfahr-Liste, which reads it for itself) asks that question.
//
// The nib figure IS shown, and it arrives on the Bestand payload the
// shell already reads: `nib_median` is the server's own `hand_nib_median` over
// the hand's accepted, measured Fassungen. Deliberately NOT recomputed here
// from the strips listing — that listing is the stored strip IMAGES, an opt-in
// upload (`sync --mit-streifen`), so a hand whose pixels sit in the private
// archive would be reported as unmeasured while its Befund chips one view over
// state the very number. One figure, one definition, no second read.

import { Box, Stack, Typography } from '@mui/material';

import type { EigenhandBestand } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { Stat } from '@/sections/admin/eigenhand/Stat';
import { TintentreuePanel } from '@/sections/admin/eigenhand/TintentreuePanel';
import { Panel } from '@/sections/admin/shell/Panel';
import { paper } from '@/styles/paper';

export function StatistikView({ hand, bestand }: { hand: string; bestand: EigenhandBestand }) {
  const t = de.admin.eigenhand;

  return (
    <Stack spacing={3}>
      <Typography variant="body2" sx={{ maxWidth: '47rem', color: paper.inkSoft }}>
        {t.statistikIntro}
      </Typography>

      <Panel title={t.statistikNibTitle} caption={t.statistikNibCaption}>
        {/* `typeof`, not `=== null`: app and API ship through separate build
            triggers (frontend-stack.md §8), so for the length of a rollout a
            new bundle can be served an old payload that has no `nib_median`
            at all. `undefined === null` is false, and the next line would
            call `.toFixed` on it. */}
        {typeof bestand.nib_median !== 'number' ? (
          <Stack spacing={0.5}>
            {/* A missing measurement is stated, never rendered as 0.0 — the
                Rohzahlen rule, and here it would read as a hairline. */}
            <Typography variant="body2" sx={{ color: paper.ink }}>
              {t.statistikNibNone}
            </Typography>
            <Typography variant="caption" sx={{ color: paper.inkSoft }}>
              {t.statistikNibNoneHint}
            </Typography>
          </Stack>
        ) : (
          <Stat
            value={fmt(t.statistikNibValue, { value: bestand.nib_median.toFixed(3) })}
            label={fmt(t.statistikNibFrom, { count: bestand.nib_readings ?? 0 })}
          />
        )}
      </Panel>

      {/* Keyed by hand like the strips panel: a switch remounts it, so the
          previous hand's counts never stand under the new hand's name. */}
      <TintentreuePanel key={hand} hand={hand} />

      <Panel title={t.statistikSoonTitle} caption={t.statistikSoonCaption}>
        <Box component="ul" sx={{ m: 0, pl: 2.5, display: 'grid', gap: 0.75 }}>
          {[t.statistikSoonBelege, t.statistikSoonStapel].map((line) => (
            <Typography key={line} component="li" variant="body2" sx={{ color: paper.inkSoft }}>
              {line}
            </Typography>
          ))}
        </Box>
      </Panel>
    </Stack>
  );
}
