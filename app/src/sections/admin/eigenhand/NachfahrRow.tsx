// One line of the Nachfahr-Liste: one written word box, what the Ampel says
// about it, and the ONE next step it asks for.
//
// The step is the point of the row (§6.4 „Umgeleitet"): „übersprungen:
// unautoriert" is not follower work but a Ground-Truth gap that belongs on the
// Tafel, „Maske geändert" wants `pfad --apply` before anything else, a box
// without `rect_px` („keine Bogen-Geometrie") is „nie machbar" and gets a
// sentence instead of a command, and a box the author drew HIMSELF is never
// offered a re-follow — that line is his own, and inviting the follower to
// replace it is exactly the offer this surface must not make (archiv R7).
//
// Image-free like the other work lists: what the box LOOKS like is the
// gallery's job, one switch away, and a collapsed row that loaded a crop would
// put the strip wall back that the list replaces.

import { Box, Button, Chip, Stack, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

import { InfoHint } from '@/components/InfoHint';
import { de, fmt } from '@/locales/admin';
import type { EigenhandTintentreueSensor, EigenhandTintentreueStufe } from '@/lib/api';
import { verfahrenLabel } from '@/sections/admin/eigenhand/pfadHerkunft';
import { TINTENTREUE_GRUND } from '@/sections/admin/eigenhand/stripBoxRows';
import type { StripBoxRow } from '@/sections/admin/eigenhand/stripBoxRows';
import { TerminalCommand } from '@/sections/admin/eigenhand/TerminalCommand';
import { lettersUrl } from '@/sections/admin/shell/focus';
import { WorkRow } from '@/sections/admin/shell/WorkList';
import { TOUCH_TARGET } from '@/styles/hitArea';
import { garamond, paper } from '@/styles/paper';

// The one place colour is attached to a step. The WORD travels with it in every
// case, so nothing here is carried by hue alone (design-system.md §2, Idee 19)
// — and the grey state takes the default chip rather than a fourth colour,
// because „nicht beurteilt" is the absence of a measurement.
// The same two words the Herkunfts-Chip of a strip uses, through the same
// helper: an unknown Verfahren stays RAW there and has to stay raw here, or a
// foreign follower would be relabelled into the Tintenpfad on one surface and
// not on the other.
const VERFAHREN_LABELS = {
  tintenpfad: de.admin.eigenhand.verfahrenTintenpfad,
  authored: de.admin.eigenhand.verfahrenAuthored,
};

const STUFE_COLOR: Record<EigenhandTintentreueStufe, 'success' | 'warning' | 'error' | 'default'> = {
  folgt: 'success',
  'folgt teils': 'warning',
  'folgt nicht': 'error',
  'nicht beurteilt': 'default',
};

/** A sensor reading as one line — „–" for a sensor this run did not compute,
 * never a 0 (the rule `pfadRohzahlen.ts` was built around). */
function sensorLine(sensor: EigenhandTintentreueSensor): string {
  const t = de.admin.eigenhand.nachfahren;
  const head =
    sensor.wert === null
      ? fmt(t.sensorNone, { name: sensor.name })
      : fmt(t.sensorValue, { name: sensor.name, wert: String(sensor.wert) });
  const bounds =
    sensor.soll !== null
      ? fmt(t.sensorSoll, { soll: String(sensor.soll) })
      : sensor.gruen !== null && sensor.gelb !== null
        ? fmt(t.sensorBounds, { gruen: String(sensor.gruen), gelb: String(sensor.gelb) })
        : '';
  return bounds ? `${head} · ${bounds}` : head;
}

export function NachfahrRow({
  row,
  hand,
  expanded,
  onToggle,
  rowProps,
  onMark,
}: {
  row: StripBoxRow;
  hand: string;
  expanded: boolean;
  onToggle: () => void;
  rowProps?: Record<string, string>;
  /** File this box as an Auftrag (kind=word, specimen_kind='strip', V7). */
  onMark: () => void;
}) {
  const t = de.admin.eigenhand.nachfahren;
  const urteil = row.tintentreue;
  const place = fmt(t.rowPlace, { strip: row.strip, fassung: row.fassung, nr: row.boxIndex });

  return (
    <WorkRow
      rowProps={rowProps}
      expanded={expanded}
      onToggle={onToggle}
      expandLabel={fmt(expanded ? t.rowCollapse : t.rowExpand, { wort: `${row.word} (${place})` })}
      title={
        <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
          <Typography component="span" sx={{ fontFamily: garamond, fontSize: 24, lineHeight: 1.2 }}>
            {row.word}
          </Typography>
          <Typography component="span" variant="caption" color="textSecondary">
            {place}
          </Typography>
        </Box>
      }
      chips={
        <>
          {/* The Ampel itself. The step and its reason both come from the
              server as plain German — the step on the chip, the reason beside
              it, because „folgt nicht" without „Absetzer (Bahn)" says what but
              never which sensor found it. */}
          {/* `flexShrink: 0` on every chip of this row, and it is not cosmetic:
              in the narrow chip box of a phone row a MUI chip shrinks below its
              own text and ellipsises it, so „folgt nicht" shipped as „folgt …"
              — the one word that carries the verdict, cut at the phone width
              where the list is read on the tablet's narrow side (measured at
              390 px). */}
          <Chip
            size="small"
            color={STUFE_COLOR[urteil.stufe]}
            variant={urteil.stufe === 'nicht beurteilt' ? 'outlined' : 'filled'}
            label={urteil.stufe}
            sx={{ flexShrink: 0 }}
          />
          <Typography variant="caption" color="textSecondary">
            {urteil.grund}
          </Typography>
          {/* Stated BESIDE the verdict where the verdict does not say it
              itself: the Ampel shows one grey state at a time, so a hand-drawn
              or skipped box greys for its own reason while its mask may have
              changed all the same. Where the Ampel's reason already IS the
              changed mask, the chip would be the same sentence twice — the
              doubling this PR takes out of the strip caption. */}
          {row.stale && urteil.grund !== TINTENTREUE_GRUND.maske && (
            <Chip
              size="small"
              color="warning"
              variant="outlined"
              label={de.admin.eigenhand.pfadStale}
              sx={{ flexShrink: 0 }}
            />
          )}
          {row.missingKeys.length > 0 && (
            <Chip
              size="small"
              variant="outlined"
              label={fmt(t.tafelFehlt, { keys: row.missingKeys.join(' ') })}
              sx={{ flexShrink: 0 }}
            />
          )}
          {row.korbOpen !== null && row.korbOpen > 0 && (
            <Chip
              size="small"
              color="warning"
              label={fmt(de.admin.liste.chipKorb, { count: row.korbOpen })}
              sx={{ flexShrink: 0 }}
            />
          )}
        </>
      }
      actions={
        <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center' }}>
          {/* The redirect the whole list exists for: a missing Tafel-Duktus is
              the author's own ground truth and belongs in the letter view, not
              in the basket (V9). One button per missing key — a word can owe
              more than one, and „einrichten" without the letter would leave
              the reader to guess which. */}
          {row.missingKeys.map((key) => (
            <Button
              key={key}
              size="small"
              component={RouterLink}
              to={lettersUrl(key, hand)}
              sx={{ minHeight: TOUCH_TARGET }}
            >
              {fmt(t.tafelFehltAction, { key })}
            </Button>
          ))}
          <Button size="small" variant="text" onClick={onMark} sx={{ minHeight: TOUCH_TARGET }}>
            {`⚑ ${t.korbMark}`}
          </Button>
        </Stack>
      }
      subline={
        <Typography variant="caption" sx={{ color: paper.inkSoft }}>
          {[
            row.verfahren === null
              ? t.herkunftNone
              : fmt(t.herkunft, {
                  verfahren: verfahrenLabel(row.verfahren, VERFAHREN_LABELS),
                  datum: row.erzeugtAm ?? de.admin.eigenhand.pfadNoDate,
                }),
            fmt(t.absetzerSoll, { zahl: row.absetzerSoll }),
            row.skipDetail && row.missingKeys.length === 0 ? fmt(t.skipDetail, { detail: row.skipDetail }) : '',
          ]
            .filter(Boolean)
            .join(' · ')}
        </Typography>
      }
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, pt: 1, pl: 1 }}>
        {/* The readings the verdict was folded out of, with the bounds they
            were held against — so „folgt nicht" can be checked rather than
            believed. Absent entirely where nothing was measured: an empty
            table would look like zeroes. */}
        {urteil.sensoren.length > 0 && (
          <Box>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap', rowGap: 0.5 }}>
              <Typography variant="caption" sx={{ color: paper.inkSoft }}>
                {t.sensorHeader}
              </Typography>
              <Chip size="small" variant="outlined" label={fmt(t.ampelFormat, { format: urteil.format })} />
              {/* „vorläufig" is not decoration: until the blind round per hand
                  has run, the eight bounds are borrowed from the plate and no
                  surface may imply a calibration that did not happen. */}
              {urteil.vorlaeufig && (
                <Chip
                  size="small"
                  variant="outlined"
                  label={fmt(t.ampelVorlaeufig, { stand: urteil.schwellen_stand })}
                />
              )}
              <InfoHint title={t.ampelTitle} label={t.ampelAria}>
                <Stack spacing={0.75}>
                  <Typography variant="body2">{t.ampelVorlaeufigHint}</Typography>
                  <Typography variant="body2">{t.absetzerSollHint}</Typography>
                </Stack>
              </InfoHint>
            </Stack>
            {urteil.sensoren.map((sensor) => (
              <Typography
                key={sensor.name}
                variant="caption"
                sx={{
                  display: 'block',
                  fontVariantNumeric: 'tabular-nums',
                  // The sensor that NAMED the step, marked by weight rather
                  // than by a second colour beside the Ampel's own.
                  fontWeight: sensor.name === urteil.sensor ? 600 : 400,
                  color: paper.ink,
                }}
              >
                {sensorLine(sensor)}
              </Typography>
            ))}
          </Box>
        )}

        {/* The next step, and exactly one of them. */}
        {row.missingKeys.length > 0 ? (
          <Typography variant="caption" sx={{ color: paper.inkSoft }}>
            {t.tafelFehltHint}
          </Typography>
        ) : row.verfahren === 'authored' ? (
          // Never „neu folgen" on the author's own line (archiv R7). The
          // sentence says what the terminal flag is instead of hiding that a
          // way exists — it just is not offered here.
          <Typography variant="caption" sx={{ color: paper.inkSoft }}>
            {t.authoredKeinNeuFolgen}
          </Typography>
        ) : row.skipGrund === 'no_geometry' ? (
          // The third redirect of §6.4, and the one that goes nowhere: „nie
          // machbar". `frame_for_box` raises for a Bogen printed before the cut
          // geometry existed, and that is exactly what wrote this entry — so the
          // re-follow command below would reproduce the same skip and pass it
          // off as work.
          <Typography variant="caption" sx={{ color: paper.inkSoft }}>
            {t.bogenOhneGeometrie}
          </Typography>
        ) : (
          <>
            {row.stale && (
              <Typography variant="caption" sx={{ color: paper.inkSoft }}>
                {`${t.maskeAction} — ${t.maskeHint}`}
              </Typography>
            )}
            <TerminalCommand
              lead={t.neuFolgenHint}
              command={fmt(t.befehl, { hand, strip: row.strip, fassung: row.fassung, box: row.boxIndex })}
            />
          </>
        )}
      </Box>
    </WorkRow>
  );
}
