// „Gib mir die nächsten Bögen" — the drucken Unteransicht.
//
// The form and its result, moved out of EigenhandView unchanged. One thing did
// NOT move with it: `printed`, the sheet ids of the last job. Those live in the
// shell, because the PDF buttons hang off them and a hop to the Bestand and
// back would otherwise throw them away — the sheets survive on the server, but
// their ids would be gone from the screen with no way to name them again.

import { Alert, Box, Button, Stack, TextField, Typography } from '@mui/material';
import { useState } from 'react';

import { fetchEigenhandSheetPdf, fetchEigenhandStackPdf, printEigenhandSheets } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { apiErrorText } from '@/sections/admin/shell/apiErrorText';
import type { ApiErrorText } from '@/sections/admin/shell/apiErrorText';
import { ErrorText } from '@/sections/admin/shell/ErrorText';
import { Panel } from '@/sections/admin/shell/Panel';
import { paper } from '@/styles/paper';

export function DruckenView({
  hand,
  printed,
  onPrinted,
}: {
  hand: string;
  /** The last job's sheet ids, held by the shell so a view switch keeps them. */
  printed: string[];
  /**
   * A finished job: its sheet ids, and the hand they were printed for. The
   * shell files them and re-reads the Bestand — a printed Bogen moves strips
   * into „unterwegs" — but only while that hand is still the chosen one.
   */
  onPrinted: (forHand: string, sheets: string[]) => void;
}) {
  const t = de.admin.eigenhand;
  const [sheets, setSheets] = useState(1);
  const [repeat, setRepeat] = useState(1);
  const [printing, setPrinting] = useState(false);
  // The print block reports two different failures — the Bogen could not be
  // generated, or its PDF could not be fetched — so the lead sentence travels
  // WITH the error instead of being fixed at the render site. Before this both
  // arrived under „Der Bogen konnte nicht erzeugt werden.", the PDF case with
  // its own lead pasted in front of the raw line on top of that.
  const [printError, setPrintError] = useState<{ prefix: string; error: ApiErrorText } | null>(null);

  const print = () => {
    // Read at CALL time, not in the continuation: the hand selector stays
    // enabled while a job runs, so by the time the sheets come back the shell
    // may be showing someone else. The id goes back with the result and the
    // shell decides whether it is still the right subject (Copilot review,
    // PR #622 — the same race the pre-split handler had).
    const forHand = hand;
    setPrinting(true);
    setPrintError(null);
    printEigenhandSheets({ hand: forHand, sheets, repeat })
      .then((res) => onPrinted(forHand, res.sheets.map((s) => s.sheet)))
      .catch((err: unknown) => setPrintError({ prefix: t.printError, error: apiErrorText(err) }))
      .finally(() => setPrinting(false));
  };

  const showPdf = (blob: Blob) => {
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank', 'noopener');
    // The tab keeps its own reference; releasing ours right away would race
    // the open in some browsers, so give it a beat.
    window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
  };

  const openPdf = async (sheet: string) => {
    try {
      showPdf(await fetchEigenhandSheetPdf(hand, sheet));
    } catch (err: unknown) {
      setPrintError({ prefix: t.pdfError, error: apiErrorText(err) });
    }
  };

  // The whole job as ONE document — what goes to the printer. The per-Bogen
  // buttons stay for reprinting a single page.
  const openStackPdf = async () => {
    try {
      showPdf(await fetchEigenhandStackPdf(hand, printed));
    } catch (err: unknown) {
      setPrintError({ prefix: t.pdfError, error: apiErrorText(err) });
    }
  };

  return (
    <Panel title={t.printTitle} caption={t.printIntro}>
      <Stack direction="row" spacing={2} sx={{ flexWrap: 'wrap', rowGap: 2, alignItems: 'center' }}>
        <TextField
          type="number"
          size="small"
          label={t.printSheets}
          value={sheets}
          onChange={(e) => setSheets(Math.max(1, Math.min(20, Number(e.target.value) || 1)))}
          sx={{ width: '8rem' }}
        />
        <TextField
          type="number"
          size="small"
          label={t.printRepeat}
          value={repeat}
          onChange={(e) => setRepeat(Math.max(1, Math.min(8, Number(e.target.value) || 1)))}
          sx={{ width: '11rem' }}
        />
        <Button variant="contained" onClick={print} disabled={printing || !hand}>
          {printing ? t.printing : t.printAction}
        </Button>
      </Stack>

      {printError && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          <ErrorText error={printError.error} prefix={printError.prefix} />
        </Alert>
      )}

      {printed.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" sx={{ mb: 1 }}>
            {fmt(t.printed, { count: printed.length, sheets: printed.join(', ') })}
          </Typography>
          <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', rowGap: 1, alignItems: 'center' }}>
            <Button size="small" variant="contained" onClick={openStackPdf}>
              {fmt(t.openStackPdf, { count: printed.length })}
            </Button>
            {printed.length > 1 &&
              printed.map((sheet) => (
                <Button key={sheet} size="small" variant="outlined" onClick={() => openPdf(sheet)}>
                  {sheet} · {t.openPdf}
                </Button>
              ))}
          </Stack>
          {/* The `pull` of the Bogen just printed used to stand here as a
              copyable command — and only here, which meant it was gone after a
              reload, while the Bogen itself stayed outstanding for days. The
              step is a state now (`bogen_pull`), so it lives on the Bestand as
              an Übergabekarte and survives the reload; this line says where. */}
          <Typography variant="caption" sx={{ display: 'block', mt: 1.5, color: paper.inkSoft }}>
            {t.printedNext}
          </Typography>
        </Box>
      )}
    </Panel>
  );
}
