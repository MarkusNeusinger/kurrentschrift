// How the workbench prints a failed call: the German sentence from
// `apiErrorText` on the line, the raw server line folded away underneath.
//
// The fold is the point. Before this, every admin surface rendered `String(err)`
// verbatim, so a locked glyph reported itself as
// "Error: 423 Locked: glyph 'longs' is locked; pass force=true to overwrite" —
// unreadable next to German copy and, worse, silent about what to do. Simply
// translating it would have thrown away the only diagnostic there is, so both
// stay: the sentence answers, the <details> proves.
//
// No <Alert> of its own — the call sites already own their severity and their
// box, and a nested Alert would read as two errors.
//
// The fold used to be set at `0.8125rem` = 13px, under the §9 caption floor of
// 14 — in BOTH halves, the summary a reader clicks and the raw line they then
// have to read. It stood for as long as it did because a type-floor sweep only
// sees the states a route actually reaches, and no route reaches an error by
// itself; the first admin-route run caught it on a 429 the run had provoked.
// `0.875rem` is 14px, the floor exactly, and the same step `caption` takes.

import { Box } from '@mui/material';

import { de } from '@/locales/admin';
import { mono } from '@/styles/paper';
import type { ApiErrorText } from './apiErrorText';

export function ErrorText({ error, prefix }: { error: ApiErrorText; prefix?: string }) {
  return (
    <>
      {prefix ? `${prefix} ` : null}
      {error.sentence}
      <Box component="details" sx={{ mt: 0.5, fontSize: '0.875rem' }}>
        <Box component="summary" sx={{ cursor: 'pointer', opacity: 0.8 }}>
          {de.admin.errors.detailSummary}
        </Box>
        <Box
          component="code"
          sx={{ display: 'block', mt: 0.5, fontFamily: mono, wordBreak: 'break-word', whiteSpace: 'pre-wrap' }}
        >
          {error.detail}
        </Box>
      </Box>
    </>
  );
}
