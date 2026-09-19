// The Übergabekarte — a media break, shown rather than hidden.
//
// Some steps of the capture chain cannot happen in a browser: the scan is on a
// disk, the Siebung is a local page, the follower ships in `tools/`, which the
// API image does not carry. The plan's answer (admin-redesign.md §5.1 Idee 11,
// §9.2) is this card: title, WHY with the doctrine reason, the command in mono
// with its real parameters and a copy button, „Danach hier: …" and the order
// hint. It exists only while the step is due — the state that makes it appear
// is what makes it go away again.
//
// Two things the card deliberately does NOT do:
//
// * It shows only what the SERVER sees. A snapshot, an `ingest` run, the local
//   setup cache leave no trace in the DB, so nothing here can confirm them;
//   where that matters, the copy says so instead of pretending.
// * It carries no „Am Rechner: report --faellig" line of its own. That twin
//   prints the server's due list, so it belongs to the BLOCK of server cards
//   (BestandView) — on a card built in the browser, like the per-Fassung Bahn
//   card, the line would name a command that does not print it.
//
// Surface: `paper.hi` with a hairline (design-system.md §5 — a card is paper,
// white stays reserved for scans and crops), the command through
// `TerminalCommand`, so the mono token has exactly one call site.

import { Box, Stack, Typography } from '@mui/material';

import { de, fmt } from '@/locales/admin';
import { TerminalCommand } from '@/sections/admin/eigenhand/TerminalCommand';
import type { Uebergabe } from '@/sections/admin/eigenhand/uebergabe';
import { paper } from '@/styles/paper';

export function Uebergabekarte({ karte }: { karte: Uebergabe }) {
  const t = de.admin.eigenhand.uebergabe;
  return (
    <Box
      component="section"
      aria-label={karte.titel}
      sx={{ bgcolor: paper.hi, border: 1, borderColor: paper.line, borderRadius: 1, p: 1.5 }}
    >
      <Stack spacing={0.75}>
        <Typography variant="subtitle2" sx={{ color: paper.ink }}>
          {karte.titel}
        </Typography>
        <Typography variant="caption" sx={{ color: paper.inkSoft }}>
          {karte.warum}
        </Typography>
        <TerminalCommand command={karte.befehl} />
        {/* What the one command on the card cannot say — today: the further
            open Bögen, because `pull` takes one `--sheet` at a time and the
            oldest one must not hide the Bogen just printed. */}
        {karte.hinweis && (
          <Typography variant="caption" sx={{ color: paper.inkSoft }}>
            {karte.hinweis}
          </Typography>
        )}
        <Typography variant="caption" sx={{ color: paper.inkSoft }}>
          {fmt(t.danach, { was: karte.danach })}
        </Typography>
        {/* The order hint is a caption like the rest and never a tooltip: it
            carries a decision („snapshot first"), and a decision that only
            exists on hover is a decision half the readers never make
            (design-system.md §9.3). */}
        {karte.reihenfolge && (
          <Typography variant="caption" sx={{ color: paper.inkSoft }}>
            {fmt(t.reihenfolge, { wie: karte.reihenfolge })}
          </Typography>
        )}
      </Stack>
    </Box>
  );
}
