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

import { Box } from '@mui/material';

import { de } from '@/locales/admin';
import type { ApiErrorText } from './apiErrorText';

export function ErrorText({ error, prefix }: { error: ApiErrorText; prefix?: string }) {
  return (
    <>
      {prefix ? `${prefix} ` : null}
      {error.sentence}
      <Box component="details" sx={{ mt: 0.5, fontSize: '0.8125rem' }}>
        <Box component="summary" sx={{ cursor: 'pointer', opacity: 0.8 }}>
          {de.admin.errors.detailSummary}
        </Box>
        <Box
          component="code"
          sx={{ display: 'block', mt: 0.5, fontFamily: 'monospace', wordBreak: 'break-word', whiteSpace: 'pre-wrap' }}
        >
          {error.detail}
        </Box>
      </Box>
    </>
  );
}
