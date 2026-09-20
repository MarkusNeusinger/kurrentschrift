// What a drawn Bahn is worth knowing about beside the picture: where it comes
// from, when it was drawn, and what it does NOT promise.

import { Box, Chip, Stack, Typography } from '@mui/material';

import type { EigenhandFleck, EigenhandPfad } from '@/lib/api';
import { InfoHint } from '@/components/InfoHint';
import { de, fmt } from '@/locales/admin';
import { herkunftChipLabel, pfadHerkunft } from '@/sections/admin/eigenhand/pfadHerkunft';
import { paper } from '@/styles/paper';

// The Herkunfts-Chip wording, bound once: the strip row stores its own
// `verfahren`, so it may name the follower — unlike the plate, where nothing
// records one (author decision 2026-09-18, Q8 b).
const VERFAHREN_LABELS = {
  tintenpfad: de.admin.eigenhand.verfahrenTintenpfad,
  authored: de.admin.eigenhand.verfahrenAuthored,
};

/**
 * Herkunft, Datum and the honest caveats of a drawn path: the seed is the
 * chart ductus of the style, not this hand, and a Fleckenmaske edited after
 * the follow means the path read different ink than the picture now shows.
 */
export function PfadCaption({
  pfade,
  flecken,
}: {
  pfade: EigenhandPfad[];
  flecken: EigenhandFleck[] | null | undefined;
}) {
  const t = de.admin.eigenhand;
  // Herkunft belongs to the single path, not to the list: a Fassung can hold
  // paths from several runs, so a Verfahren and a day are named only while
  // every drawn path agrees on them — picking one word narrows `pfade` to that
  // word, and the line becomes its own provenance. A mixed list says so and
  // carries the per-word detail in its tooltip, instead of letting the first
  // entry speak for the others (Copilot review, PR #598).
  const herkunft = pfadHerkunft(pfade, t.pfadNoDate, VERFAHREN_LABELS);
  const chipLabel = herkunftChipLabel(herkunft, VERFAHREN_LABELS);
  const stale = pfade.some((p) => typeof p.flecken_n === 'number' && flecken != null && p.flecken_n !== flecken.length);
  const pedigree = (
    <Typography variant="caption" sx={{ color: paper.inkSoft }}>
      {herkunft.gemischt
        ? fmt(t.pfadPedigreeMixed, { woerter: pfade.length })
        : fmt(t.pfadPedigree, { datum: herkunft.datum ?? '', woerter: pfade.length })}
    </Typography>
  );
  return (
    <Stack direction="row" spacing={1} sx={{ mt: 0.5, flexWrap: 'wrap', rowGap: 0.5, alignItems: 'center' }}>
      {pedigree}
      {/* The Herkunfts-Chip, beside the other markers of this row rather than
          inside the caption (author decision 2026-09-18, Q8 b). It carries NO
          status colour: „von Hand" names an origin, never a verdict — an
          authored Bahn is simply not measured yet (§6.3). It disappears only
          where the VERFAHREN disagree; a Fassung followed on two days keeps
          its one honest origin, and the differing days are the caption's
          business (`herkunftChipLabel`). */}
      {chipLabel !== null && <Chip size="small" variant="outlined" label={chipLabel} />}
      {/* All three chips are plain `div`s — MUI adds no tabIndex — so what hung
          in their hovers (which runs a mixed Fassung is made of; where the seed
          comes from; why the Fassung is stale and what to do about it) was
          mouse-only. The three are one subject — the provenance and state of
          THIS Fassung — so they get ONE `InfoHint` for the row (§9.4), which is
          also one tab stop instead of three. */}
      <Chip size="small" variant="outlined" label={t.pfadSeed} />
      {stale && <Chip size="small" color="warning" variant="outlined" label={t.pfadStale} />}
      <InfoHint title={t.pfadPedigreeMixedTitle} label={t.pfadSeedAria}>
        <Stack spacing={0.75}>
          {herkunft.gemischt && (
            <Box sx={{ whiteSpace: 'pre-line' }}>{[t.pfadMixedHint, ...herkunft.laeufe].join('\n')}</Box>
          )}
          <Typography variant="body2">{t.pfadSeedHint}</Typography>
          {stale && <Typography variant="body2">{t.pfadStaleHint}</Typography>}
        </Stack>
      </InfoHint>
    </Stack>
  );
}
