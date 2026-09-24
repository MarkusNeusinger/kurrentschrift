// Die Tintentreue-Verteilung — how many word boxes of this hand the Bahn
// follows, partly follows, does not follow, and how many nothing has judged.
//
// It reads the one hand-wide box read the Nachfahr-Liste and the gallery read
// (`useEigenhandPfadBoxes`) and counts it with a pure helper
// (`tintentreueVerteilung.ts`); nothing is judged here. The step words come
// from the server and are shown untranslated, the colour comes from the ONE
// chip that colours a step (`AmpelChip.tsx`), and every count stands beside its
// word, so hue is never the only channel (design-system §2).
//
// Links go into the Nachfahr-Liste only where an existing list axis selects
// EXACTLY the counted boxes — the list deliberately has no axis per step, and
// a superset behind a number would contradict the number. Where there is none,
// the panel's closing link opens the list in its Schwere order, which puts the
// red boxes first anyway.

import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useMemo, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';

import { InfoHint } from '@/components/InfoHint';
import { de, fmt } from '@/locales/admin';
import { StufeChip } from '@/sections/admin/eigenhand/AmpelChip';
import {
  listenLinkUrl,
  tintentreueVerteilung,
  VERTEILUNG_STUFEN,
  type Gruppe,
} from '@/sections/admin/eigenhand/tintentreueVerteilung';
import { useEigenhandPfadBoxes } from '@/sections/admin/eigenhand/useEigenhandPfadBoxes';
import { ErrorText } from '@/sections/admin/shell/ErrorText';
import { Panel } from '@/sections/admin/shell/Panel';
import { eigenhandUrl } from '@/sections/admin/shell/focus';
import { TOUCH_TARGET } from '@/styles/hitArea';
import { paper } from '@/styles/paper';

const percent = (count: number, total: number): string =>
  total === 0 ? '0' : Math.round((count / total) * 100).toString();

const inflected = (forms: { one: string; many: string }, count: number): string =>
  fmt(count === 1 ? forms.one : forms.many, { count });

function ListLink({ gruppe }: { gruppe: Gruppe }) {
  const t = de.admin.eigenhand.statistikTreue;
  if (!gruppe.link) return null;
  return (
    <Button
      size="small"
      component={RouterLink}
      to={listenLinkUrl(gruppe.link)}
      aria-label={fmt(t.linkAria, { name: gruppe.name, kaesten: inflected(t.kasten, gruppe.count) })}
      sx={{ minHeight: TOUCH_TARGET, textTransform: 'none', flexShrink: 0 }}
    >
      {t.link}
    </Button>
  );
}

export function TintentreuePanel({ hand }: { hand: string }) {
  const t = de.admin.eigenhand.statistikTreue;
  const { fassungen, error } = useEigenhandPfadBoxes(hand);
  const verteilung = useMemo(() => (fassungen === null ? null : tintentreueVerteilung(fassungen)), [fassungen]);
  const [perFassung, setPerFassung] = useState(false);

  // „vorläufig" belongs in the head, where it qualifies every number below —
  // and it is stated as long as ANY counted box was graded under borrowed
  // bounds, never inferred from the calibration the plan expects.
  const actions =
    verteilung && verteilung.vorlaeufig !== null ? (
      <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center' }}>
        {verteilung.vorlaeufig && (
          <Typography variant="caption" sx={{ color: paper.ink, fontWeight: 600 }}>
            {t.vorlaeufig}
          </Typography>
        )}
        <InfoHint title={t.vorlaeufigTitle} label={t.vorlaeufigAria}>
          <Stack spacing={0.75}>
            <Typography variant="body2">
              {verteilung.schwellenStaende.length === 1
                ? fmt(t.stand, { stand: verteilung.schwellenStaende[0] })
                : fmt(t.staende, { staende: verteilung.schwellenStaende.join(', ') })}
            </Typography>
            {verteilung.vorlaeufig && (
              <Typography variant="body2">{de.admin.eigenhand.nachfahren.ampelVorlaeufigHint}</Typography>
            )}
            <Typography variant="body2">{t.eineHand}</Typography>
          </Stack>
        </InfoHint>
      </Stack>
    ) : undefined;

  return (
    <Panel title={t.title} caption={t.caption} actions={actions}>
      {error && fassungen === null ? (
        <Alert severity="warning">
          <ErrorText error={error} prefix={t.loadError} />
        </Alert>
      ) : verteilung === null ? (
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
          <CircularProgress size={16} />
          <Typography variant="body2" sx={{ color: paper.inkSoft }}>
            {t.loading}
          </Typography>
        </Stack>
      ) : verteilung.kaesten === 0 ? (
        // Nothing to count is said as such: four zeroes would read as „the
        // hand is written and nothing follows".
        <Typography variant="body2" sx={{ color: paper.ink }}>
          {verteilung.fassungen === 0 ? t.emptyNoStrips : t.emptyNoBoxes}
        </Typography>
      ) : (
        <Stack spacing={2}>
          <Typography variant="body2" sx={{ color: paper.ink }}>
            {fmt(t.summary, {
              kaesten: inflected(t.kasten, verteilung.kaesten),
              fassungen: inflected(t.fassung, verteilung.fassungen),
              gemessen: verteilung.gemessen,
            })}
          </Typography>
          {verteilung.gemessen === 0 && (
            <Typography variant="body2" sx={{ color: paper.inkSoft }}>
              {t.nothingMeasured}
            </Typography>
          )}

          <Box component="ul" sx={{ m: 0, p: 0, listStyle: 'none', display: 'grid', gap: 1.5 }}>
            {verteilung.stufen.map((zeile) => (
              <Box component="li" key={zeile.stufe}>
                <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center', flexWrap: 'wrap', rowGap: 0.5 }}>
                  <StufeChip stufe={zeile.stufe} />
                  <Typography variant="body2" sx={{ color: paper.ink, fontVariantNumeric: 'tabular-nums' }}>
                    {fmt(t.count, {
                      kaesten: inflected(t.kasten, zeile.count),
                      share: percent(zeile.count, verteilung.kaesten),
                    })}
                  </Typography>
                  <ListLink gruppe={zeile} />
                </Stack>
                {/* „folgt" carries one reason, „nichts fällt auf", and listing
                    it would only repeat the step. The other three name WHY:
                    the sensor that decided a measured step, or the grey state's
                    own reason. */}
                {zeile.stufe !== 'folgt' && zeile.gruende.length > 0 && (
                  <Box sx={{ mt: 0.5, pl: 1 }}>
                    <Typography variant="caption" sx={{ display: 'block', color: paper.inkSoft }}>
                      {zeile.stufe === 'nicht beurteilt' ? t.gruendeGrau : t.gruendeSensor}
                    </Typography>
                    <Box component="ul" sx={{ m: 0, pl: 2.5, display: 'grid', gap: 0.25 }}>
                      {zeile.gruende.map((grund) => (
                        <Box
                          component="li"
                          key={grund.name}
                          sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}
                        >
                          <Typography variant="body2" sx={{ color: paper.ink, fontVariantNumeric: 'tabular-nums' }}>
                            {fmt(t.grund, { name: grund.name, count: grund.count })}
                          </Typography>
                          <ListLink gruppe={grund} />
                        </Box>
                      ))}
                    </Box>
                  </Box>
                )}
              </Box>
            ))}
          </Box>

          <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', rowGap: 1, alignItems: 'center' }}>
            <Button
              size="small"
              variant="outlined"
              component={RouterLink}
              to={eigenhandUrl('streifen')}
              sx={{ minHeight: TOUCH_TARGET, textTransform: 'none' }}
            >
              {t.toList}
            </Button>
            <Button
              size="small"
              aria-expanded={perFassung}
              onClick={() => setPerFassung((open) => !open)}
              sx={{ minHeight: TOUCH_TARGET, textTransform: 'none' }}
            >
              {perFassung ? t.perFassungHide : fmt(t.perFassungShow, { count: verteilung.fassungen })}
            </Button>
          </Stack>

          {perFassung && (
            // Its own horizontal scroll on a phone: six columns do not fit 390
            // px, and the page itself must not scroll sideways.
            <Box sx={{ overflowX: 'auto' }}>
              <Table size="small" aria-label={t.perFassungAria}>
                <TableHead>
                  <TableRow>
                    <TableCell>{t.colFassung}</TableCell>
                    <TableCell align="right">{t.colKaesten}</TableCell>
                    {VERTEILUNG_STUFEN.map((stufe) => (
                      <TableCell key={stufe} align="right">
                        {stufe}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {verteilung.proFassung.map((zeile) => (
                    <TableRow key={`${zeile.strip}/${zeile.fassung}`}>
                      <TableCell>{`${zeile.strip} · ${zeile.fassung}`}</TableCell>
                      <TableCell align="right" sx={{ fontVariantNumeric: 'tabular-nums' }}>
                        {zeile.kaesten}
                      </TableCell>
                      {VERTEILUNG_STUFEN.map((stufe) => (
                        <TableCell key={stufe} align="right" sx={{ fontVariantNumeric: 'tabular-nums' }}>
                          {zeile.stufen[stufe]}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          )}
        </Stack>
      )}
    </Panel>
  );
}
