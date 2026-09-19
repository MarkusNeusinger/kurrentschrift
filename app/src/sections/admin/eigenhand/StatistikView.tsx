// „Was sagt die Tinte dieser Hand?" — the statistik Unteransicht.
//
// It ships mostly as a labelled Leerfläche on purpose (author decision Q7 a,
// 2026-09-18). Of the four figures §7.2 promises this view, three need compute
// that does not exist yet: the Tintentreue distribution waits on
// `core/eigenhand/tintentreue.py` (Phase 2), the Ausschnitt-Stapel on the
// Fassung selection of the streifen view, and a dated Belegzahl history on a
// Bestandsverlauf nobody records. Naming them beats an empty page that looks
// like a broken one.
//
// The fourth IS derivable today: `befund.nib.units` sits on every measured
// Fassung in the strips listing. That is one extra admin read for this view —
// deliberate, because it is the view's whole content, and the listing defers
// both the PNG and the Bahnen, so it costs metadata only.

import { Alert, Box, Stack, Typography } from '@mui/material';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { getEigenhandStrips } from '@/lib/api';
import type { EigenhandStrip } from '@/lib/api';
import { latestRequestGate } from '@/lib/latestRequest';
import { de, fmt } from '@/locales/admin';
import { nibMedian } from '@/sections/admin/eigenhand/nibMedian';
import { Stat } from '@/sections/admin/eigenhand/Stat';
import { apiErrorText } from '@/sections/admin/shell/apiErrorText';
import type { ApiErrorText } from '@/sections/admin/shell/apiErrorText';
import { ErrorText } from '@/sections/admin/shell/ErrorText';
import { EvidenceState, Panel } from '@/sections/admin/shell/Panel';
import { paper } from '@/styles/paper';

export function StatistikView({ hand }: { hand: string }) {
  const t = de.admin.eigenhand;
  const [strips, setStrips] = useState<EigenhandStrip[]>([]);
  const [loading, setLoading] = useState(Boolean(hand));
  const [error, setError] = useState<ApiErrorText | null>(null);
  // Same guard as the Bestand load: a hand switched twice in a row must not
  // let the older listing land under the newer hand's name.
  const beginListing = useRef(latestRequestGate()).current;

  // Arming the spinner and dropping the previous hand's readings happens
  // DURING RENDER, the shell's own idiom (react-hooks/set-state-in-effect):
  // an effect that armed them would be setting state synchronously, and the
  // number on screen would belong to the hand just left for one frame.
  const [listedFor, setListedFor] = useState(hand);
  if (listedFor !== hand) {
    setListedFor(hand);
    setStrips([]);
    if (hand) {
      setLoading(true);
      setError(null);
    }
  }

  const load = useCallback(
    (target: string) => {
      if (!target) return;
      const isCurrent = beginListing();
      getEigenhandStrips(target, {}, { retries: 2 })
        .then((data) => isCurrent() && setStrips(data.strips))
        .catch((err: unknown) => {
          if (!isCurrent()) return;
          setStrips([]);
          setError(apiErrorText(err));
        })
        .finally(() => {
          if (isCurrent()) setLoading(false);
        });
    },
    [beginListing],
  );

  useEffect(() => {
    load(hand);
  }, [hand, load]);

  const nib = useMemo(() => nibMedian(strips), [strips]);

  return (
    <Stack spacing={3}>
      <Typography variant="body2" sx={{ maxWidth: '47rem', color: paper.inkSoft }}>
        {t.statistikIntro}
      </Typography>

      <Panel title={t.statistikNibTitle} caption={t.statistikNibCaption}>
        {error ? (
          <Alert severity="warning" sx={{ py: 0 }}>
            <ErrorText error={error} prefix={t.statistikError} />
          </Alert>
        ) : (
          <EvidenceState loading={loading} error={false}>
            {nib.units === null ? (
              <Stack spacing={0.5}>
                {/* A missing measurement is stated, never rendered as 0.0 —
                    the Rohzahlen rule, and here it would read as a hairline. */}
                <Typography variant="body2" sx={{ color: paper.ink }}>
                  {t.statistikNibNone}
                </Typography>
                <Typography variant="caption" sx={{ color: paper.inkSoft }}>
                  {t.statistikNibNoneHint}
                </Typography>
              </Stack>
            ) : (
              <Stat
                value={fmt(t.statistikNibValue, { value: nib.units.toFixed(3) })}
                label={fmt(t.statistikNibFrom, { count: nib.count })}
              />
            )}
          </EvidenceState>
        )}
      </Panel>

      <Panel title={t.statistikSoonTitle} caption={t.statistikSoonCaption}>
        <Box component="ul" sx={{ m: 0, pl: 2.5, display: 'grid', gap: 0.75 }}>
          {[t.statistikSoonTintentreue, t.statistikSoonBelege, t.statistikSoonStapel].map((line) => (
            <Typography key={line} component="li" variant="body2" sx={{ color: paper.inkSoft }}>
              {line}
            </Typography>
          ))}
        </Box>
      </Panel>
    </Stack>
  );
}
