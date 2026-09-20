// What a drawn Bahn is worth knowing about beside the picture: where it comes
// from, when it was drawn, and what it does NOT promise.
//
// What it no longer carries is the „Maske geändert" warning. It was computed
// here, from `flecken_n` against the Fassung's mask, at a time when nothing
// else could say it; since the Tintentreue that same fact is a GREY STATE of
// the Ampel per box, and the Nachfahr-Liste prints it beside the verdict with
// the step it asks for („erst `pfad --apply`"). Two statements about one
// Fassung in two vocabularies is exactly what a second verdict beside
// `befund.vorschlag` would have been — so this one gives way to the one that
// can also say what to do about it (PR 8 of the Phase-2 slice; the hand-off is
// in #638's own body).

import { Box, Chip, Stack, Typography } from '@mui/material';

import type { EigenhandPfad } from '@/lib/api';
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
 * Herkunft, Datum and the honest caveat of a drawn path: the seed is the chart
 * ductus of the style, not this hand.
 */
export function PfadCaption({ pfade }: { pfade: EigenhandPfad[] }) {
  const t = de.admin.eigenhand;
  // Herkunft belongs to the single path, not to the list: a Fassung can hold
  // paths from several runs, so a Verfahren and a day are named only while
  // every drawn path agrees on them — picking one word narrows `pfade` to that
  // word, and the line becomes its own provenance. A mixed list says so and
  // carries the per-word detail in its tooltip, instead of letting the first
  // entry speak for the others (Copilot review, PR #598).
  const herkunft = pfadHerkunft(pfade, t.pfadNoDate, VERFAHREN_LABELS);
  const chipLabel = herkunftChipLabel(herkunft, VERFAHREN_LABELS);
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
      {/* Both chips are plain `div`s — MUI adds no tabIndex — so what hung in
          their hovers (which runs a mixed Fassung is made of; where the seed
          comes from) was mouse-only. They are one subject — the provenance of
          THIS Fassung — so they get ONE `InfoHint` for the row (§9.4), which is
          also one tab stop instead of two. */}
      <Chip size="small" variant="outlined" label={t.pfadSeed} />
      <InfoHint title={t.pfadPedigreeMixedTitle} label={t.pfadSeedAria}>
        <Stack spacing={0.75}>
          {herkunft.gemischt && (
            <Box sx={{ whiteSpace: 'pre-line' }}>{[t.pfadMixedHint, ...herkunft.laeufe].join('\n')}</Box>
          )}
          <Typography variant="body2">{t.pfadSeedHint}</Typography>
        </Stack>
      </InfoHint>
    </Stack>
  );
}
