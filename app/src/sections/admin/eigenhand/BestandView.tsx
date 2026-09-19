// „Wie weit ist diese Hand?" — the Bestand Unteransicht.
//
// Everything here answers progress against the committed strip plan: the
// standing setup, the counters, the queue, which characters and joins are
// covered, and how much of the Übergangsraum the hand holds. What the INK says
// is the statistik view's question, and the written strips themselves are the
// streifen view's — this one never loads a pixel.
//
// The panels are the ones EigenhandView carried before the split, moved
// unchanged; the filter a coverage cell files now travels through the URL
// (`?reiter=streifen&item=…`) instead of through a scroll into a panel below.

import { Box, Chip, FormControlLabel, Stack, Switch, Tooltip, Typography } from '@mui/material';
import { useMemo, useState } from 'react';

import type { EigenhandBestand, EigenhandBucket } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { glyphOf } from '@/sections/admin/eigenhand/coverageLabels';
import { SetupPanel } from '@/sections/admin/eigenhand/SetupPanel';
import { Stat } from '@/sections/admin/eigenhand/Stat';
import { rechnerBefehl, uebergabeKarten } from '@/sections/admin/eigenhand/uebergabe';
import { Uebergabekarte } from '@/sections/admin/eigenhand/Uebergabekarte';
import { Panel } from '@/sections/admin/shell/Panel';
import { mono, paper } from '@/styles/paper';

const BUCKET_LABELS: Record<string, string> = {
  klein: de.admin.eigenhand.bucketKlein,
  gross: de.admin.eigenhand.bucketGross,
  ligatur: de.admin.eigenhand.bucketLigatur,
  ziffer: de.admin.eigenhand.bucketZiffer,
  zeichen: de.admin.eigenhand.bucketZeichen,
};

/**
 * One glyph class as a grid of its keys — written ones inked, open ones pale.
 * A written key is a button: it brings up the words that hold the glyph.
 */
function BucketGrid({
  name,
  bucket,
  onSelect,
}: {
  name: string;
  bucket: EigenhandBucket;
  onSelect: (key: string) => void;
}) {
  const t = de.admin.eigenhand;
  return (
    <Box sx={{ mb: 2 }}>
      <Stack direction="row" spacing={1} sx={{ mb: 0.5, flexWrap: 'wrap', alignItems: 'baseline' }}>
        <Typography variant="subtitle2" sx={{ color: paper.ink }}>
          {BUCKET_LABELS[name] ?? name}
        </Typography>
        <Typography variant="caption" sx={{ color: paper.inkSoft }}>
          {fmt(t.coverageOf, { covered: bucket.covered, possible: bucket.possible })} ·{' '}
          {fmt(t.coverageBelege, { belege: bucket.belege })}
        </Typography>
      </Stack>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
        {bucket.keys.map((row) => (
          <Tooltip
            key={row.key}
            describeChild
            title={`${fmt(t.keyTooltip, { key: row.key, belege: row.belege, planned: row.planned })}${
              row.belege ? t.keyTooltipShow : ''
            }`}
          >
            {/* A written key is a real <button> (native keyboard + semantics);
                an unwritten one has nothing to show and stays a plain cell. */}
            <Box
              component={row.belege ? 'button' : 'div'}
              type={row.belege ? 'button' : undefined}
              onClick={row.belege ? () => onSelect(row.key) : undefined}
              sx={{
                minWidth: '2.1rem',
                px: 0.5,
                py: 0.25,
                textAlign: 'center',
                font: 'inherit',
                appearance: 'none',
                border: 1,
                borderRadius: 1,
                borderColor: row.belege ? paper.sepia : 'divider',
                bgcolor: row.belege ? 'action.hover' : 'transparent',
                color: row.belege ? paper.ink : 'text.disabled',
                cursor: row.belege ? 'pointer' : 'default',
              }}
            >
              <Typography variant="body2" sx={{ lineHeight: 1.2 }}>
                {glyphOf(row.key)}
              </Typography>
              {/* 0.6rem = 9.6 px, under the design system's 14 px caption
                  floor, and an ad-hoc fontSize on a variant besides. Moved
                  here verbatim on purpose: lifting it re-flows a grid of ~90
                  cells the author reads every day, and changing his optics is
                  not what a page split is for. Filed for his call rather than
                  decided here. */}
              <Typography variant="caption" sx={{ fontSize: '0.6rem', color: 'inherit' }}>
                {row.belege}
              </Typography>
            </Box>
          </Tooltip>
        ))}
      </Box>
    </Box>
  );
}

export function BestandView({
  hand,
  bestand,
  labelOf,
  onShowBelege,
}: {
  hand: string;
  bestand: EigenhandBestand;
  /** How a coverage item is spelled for a reader — the shell owns the wording. */
  labelOf: (item: string) => string;
  /** Opens the written evidence for one item, which now means: go to `streifen`. */
  onShowBelege: (item: string) => void;
}) {
  const t = de.admin.eigenhand;
  const [openOnly, setOpenOnly] = useState(true);

  const openJoins = useMemo(
    () => bestand.joins.rows.filter((row) => !openOnly || row.belege === 0),
    [bestand, openOnly],
  );

  // The due local steps, in the server's order. An empty list renders NOTHING —
  // the panel with its headline would otherwise say „next up at the machine"
  // over an empty box on every hand that is up to date.
  const karten = useMemo(() => uebergabeKarten(bestand.faellig), [bestand.faellig]);

  return (
    <Stack spacing={3}>
      <SetupPanel hand={hand} />

      <Panel title={t.stripsTitle} caption={t.queueTitle}>
        <Stack direction="row" spacing={3} sx={{ flexWrap: 'wrap', rowGap: 2 }}>
          <Stat value={bestand.strips.belegt} label={t.stripsBelegt} />
          <Stat value={bestand.strips.unterwegs} label={t.stripsUnterwegs} />
          <Stat value={bestand.strips.geplant} label={t.stripsGeplant} />
          <Stat value={bestand.strips.total} label={t.stripsTotal} />
          <Stat value={bestand.fassungen.angenommen} label={t.fassungenAngenommen} />
          <Stat value={bestand.fassungen.verworfen} label={t.fassungenVerworfen} />
          <Stat value={bestand.sheets.printed} label={t.sheetsPrinted} />
        </Stack>
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 2 }}>
          {bestand.queue.map((sid) => (
            <Chip key={sid} size="small" variant="outlined" label={sid} />
          ))}
        </Box>
      </Panel>

      {karten.length > 0 && (
        <Panel title={t.uebergabe.title} caption={t.uebergabe.caption}>
          <Stack spacing={1.5}>
            {karten.map((karte) => (
              <Uebergabekarte key={karte.id} karte={karte} />
            ))}
            {/* The twin, once under the block rather than on every card: the
                clipboard does not reach from the tablet to the machine, so the
                one command that prints this very list there is meant to be
                READ and typed — no copy button, and no promise that a card
                built in the browser would appear in its output. */}
            <Typography variant="caption" sx={{ color: paper.inkSoft }}>
              {t.uebergabe.rechnerLead}
              <Box component="code" sx={{ fontFamily: mono, userSelect: 'all' }}>
                {rechnerBefehl(hand)}
              </Box>
            </Typography>
          </Stack>
        </Panel>
      )}

      <Panel
        title={t.coverageTitle}
        caption={fmt(t.coverageOf, {
          covered: Object.values(bestand.glyphs).reduce((sum, b) => sum + b.covered, 0),
          possible: Object.values(bestand.glyphs).reduce((sum, b) => sum + b.possible, 0),
        })}
      >
        {Object.entries(bestand.glyphs).map(([name, bucket]) => (
          <BucketGrid key={name} name={name} bucket={bucket} onSelect={onShowBelege} />
        ))}
      </Panel>

      <Panel
        title={t.coverageJoins}
        caption={`${fmt(t.coverageOf, {
          covered: bestand.joins.covered,
          possible: bestand.joins.possible,
        })} — ${t.joinsIntro}`}
        actions={
          <FormControlLabel
            control={<Switch size="small" checked={openOnly} onChange={(e) => setOpenOnly(e.target.checked)} />}
            label={<Typography variant="caption">{t.joinsShowOpen}</Typography>}
          />
        }
      >
        {openJoins.length === 0 ? (
          <Typography variant="caption" sx={{ color: paper.inkSoft }}>
            {t.joinsEmpty}
          </Typography>
        ) : (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, maxHeight: '20rem', overflowY: 'auto' }}>
            {openJoins.map((row) => (
              <Chip
                key={row.item}
                size="small"
                variant={row.belege ? 'filled' : 'outlined'}
                label={`${labelOf(row.item)}${row.belege ? ` · ${row.belege}` : ''}`}
                onClick={row.belege ? () => onShowBelege(row.item) : undefined}
              />
            ))}
          </Box>
        )}
      </Panel>

      <Panel title={t.quotenTitle} caption={t.quotenCaption}>
        {bestand.quoten ? (
          <Stack direction="row" spacing={3} sx={{ flexWrap: 'wrap', rowGap: 2 }}>
            <Stat
              value={`${(bestand.quoten.erstbeleg_weighted * 100).toFixed(1)} %`}
              label={`Erstbeleg (gewichtet) · ${bestand.quoten.erstbeleg}/${bestand.quoten.items}`}
            />
            <Stat
              value={`${(bestand.quoten.ausbau_weighted * 100).toFixed(1)} %`}
              label={`Ausbau (gewichtet) · ${bestand.quoten.ausbau}/${bestand.quoten.soll_belege}`}
            />
          </Stack>
        ) : (
          /* The state, not the command: the step itself stands once, as the
             `universe_push` card above. Saying it twice was how the same
             sentence started drifting in two places. */
          <Typography variant="caption" sx={{ color: paper.inkSoft }}>
            {t.quotenNone}
          </Typography>
        )}
      </Panel>
    </Stack>
  );
}
