// What the follower measured on a Bahn, as plain numbers — never as a verdict.

import { Box, Chip, Stack, Typography } from '@mui/material';

import type { EigenhandPfad } from '@/lib/api';
import { InfoHint } from '@/components/InfoHint';
import { de, fmt } from '@/locales/admin';
import { countLabel } from '@/sections/admin/eigenhand/readings';
import { pfadRohzahlen } from '@/sections/admin/eigenhand/pfadRohzahlen';
import { paper } from '@/styles/paper';

/**
 * The stored sensors of the drawn word boxes as plain numbers — the Etikett
 * „Zahl, kein Urteil" is part of the block, because the Tintentreue traffic
 * light (#638) judges the same readings in the list under „Nachfahren" and on
 * the word crops of the filtered gallery (`CropTile`), and the two must never
 * be confused (admin-redesign.md V26). The whole-strip tile (`StripTile`)
 * renders this block with no Ampel beside it.
 *
 * One line per Kasten: a Fassung's boxes are followed one by one, so the row's
 * weakest word is precisely what these numbers are read for — an average over
 * the row would hide it. Nothing here is coloured and nothing is judged; an
 * unmeasured Bahn says so rather than showing four zeros.
 *
 * `showBox` prefixes each line with its cut. Over a WHOLE strip that prefix is
 * the only thing that tells the lines apart, and it carries the box INDEX, not
 * just the word: eight rows of the frozen plan hold the same word twice
 * (`ja!`, `„wohl“`, `Übung` …), so two word-only prefixes would be identical
 * and neither reading could be assigned. The index is the one `--box` of
 * `tools.eigenhand.pfad` takes, so a bad reading can be re-followed straight
 * from what the chip says.
 */
export function PfadRohzahlenChips({ pfade, showBox }: { pfade: EigenhandPfad[]; showBox: boolean }) {
  const t = de.admin.eigenhand;
  return (
    <Box sx={{ mt: 0.5 }}>
      <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center', flexWrap: 'wrap', rowGap: 0.5 }}>
        <Typography variant="caption" sx={{ color: paper.inkSoft }}>
          {t.pfadRohzahlen}
        </Typography>
        <InfoHint title={t.pfadRohzahlen}>{t.pfadRohzahlenHint}</InfoHint>
      </Stack>
      {pfade.map((pfad) => {
        const readings = pfadRohzahlen(pfad);
        return (
          <Stack
            key={pfad.box_index}
            direction="row"
            spacing={0.5}
            sx={{ mt: 0.5, alignItems: 'center', flexWrap: 'wrap', rowGap: 0.5 }}
          >
            {showBox && (
              <Typography variant="caption" sx={{ color: paper.inkSoft }}>
                {fmt(t.pfadRohzahlenBox, { nr: pfad.box_index, wort: pfad.word })}
              </Typography>
            )}
            {readings.measured ? (
              <>
                <Chip
                  size="small"
                  variant="outlined"
                  label={
                    readings.inkUnvisitedShare === null
                      ? t.pfadRohzahlenUnvisitedNone
                      : // One decimal at most. The follower rounds the share to
                        // three places, so `0.001` is a real reading — at whole
                        // percent it would print as the „0 %" that only a Bahn
                        // covering all the ink earns, and this whole block
                        // exists to keep a measured zero apart from everything
                        // that merely looks like one. A round value keeps its
                        // clean form (21 %), German decimal comma.
                        fmt(t.pfadRohzahlenUnvisited, {
                          prozent: (readings.inkUnvisitedShare * 100).toLocaleString('de-DE', {
                            maximumFractionDigits: 1,
                          }),
                        })
                  }
                />
                <Chip
                  size="small"
                  variant="outlined"
                  label={fmt(t.pfadRohzahlenLifts, { zahl: countLabel(readings.paperLifts) })}
                />
                <Chip
                  size="small"
                  variant="outlined"
                  label={fmt(t.pfadRohzahlenJumps, { zahl: countLabel(readings.jumps) })}
                />
                <Chip
                  size="small"
                  variant="outlined"
                  label={fmt(t.pfadRohzahlenHairpins, { zahl: countLabel(readings.hairpins) })}
                />
              </>
            ) : (
              // The reason an unmeasured Bahn shows no numbers belongs beside
              // the chip, not in a hover over it: the chip is a `div`, so the
              // sentence never reached keyboard or finger. The block's own
              // InfoHint above says what the numbers are; this one is the
              // per-Bahn answer „why none".
              <>
                <Chip size="small" variant="outlined" label={t.pfadRohzahlenNone} />
                <Typography variant="caption" sx={{ color: paper.inkSoft }}>
                  {t.pfadRohzahlenNoneHint}
                </Typography>
              </>
            )}
          </Stack>
        );
      })}
    </Box>
  );
}
