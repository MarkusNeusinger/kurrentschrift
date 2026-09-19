// A shell command the author is meant to run, set so it can actually be typed
// or taken.
//
// Every command line of an Übergabekarte is one of these — since the cards
// took over, that is the component's only caller, and the four standing hints
// it used to serve (setup · pull · universe · sync) are states now. Before it
// existed, a command sat INSIDE a running sentence in EB Garamond at 14px — a
// proportional antiqua, in which
// `--`, `-m`, `_` and `.` are exactly the characters that slip while typing,
// and where taking the command means selecting it out of the middle of a
// sentence by hand (audit 2026-09-02, finding 29). Monospace, its own line,
// `user-select: all` for one click, and a copy button beside it.
//
// The face is the `mono` token (a system stack — styles/paper.ts) and the size
// comes from `variant="body2"` = 17 px, not from an ad-hoc `fontSize`
// (design-system.md §3). The 14 px it carried until now was below the caption
// floor for a string that is meant to be TYPED.

import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DoneIcon from '@mui/icons-material/Done';
import { Box, IconButton, Tooltip, Typography } from '@mui/material';
import { useEffect, useRef, useState } from 'react';

import { de } from '@/locales/admin';
import { hitArea } from '@/styles/hitArea';
import { mono, paper } from '@/styles/paper';

export function TerminalCommand({ command, lead }: { command: string; lead?: string }) {
  const t = de.admin.eigenhand;
  const [copied, setCopied] = useState(false);
  // Same handling as ScribeView's copy-link button: one timer in a ref, cleared
  // before each new one and on unmount, so repeated copies cannot stack pending
  // timeouts and a copy right before a re-render cannot setState on a gone
  // component.
  const copyTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  useEffect(() => () => clearTimeout(copyTimer.current), []);

  const copy = () => {
    // No clipboard permission prompt is worth an error box here: the command is
    // readable and selectable either way, so a refusal just leaves the button
    // un-ticked.
    void navigator.clipboard
      ?.writeText(command)
      .then(() => {
        setCopied(true);
        clearTimeout(copyTimer.current);
        copyTimer.current = setTimeout(() => setCopied(false), 2000);
      })
      .catch(() => {});
  };

  return (
    <Box>
      {lead && (
        <Typography variant="caption" sx={{ display: 'block', color: paper.inkSoft }}>
          {lead}
        </Typography>
      )}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.25 }}>
        <Typography
          component="code"
          variant="body2"
          sx={{
            fontFamily: mono,
            bgcolor: paper.hi,
            borderRadius: 1,
            px: 1,
            py: 0.25,
            userSelect: 'all',
            overflowX: 'auto',
            whiteSpace: 'pre',
          }}
        >
          {command}
        </Typography>
        <Tooltip title={copied ? t.commandCopied : t.commandCopy}>
          {/* Drawn small on purpose — it sits beside a line of code, not over
              it — so it grows the invisible 44 px area instead of a bigger
              mark (design-system.md §9.3). Measured at 30 × 30 before this,
              and the button now appears on every Übergabekarte rather than
              four times on one page. */}
          <IconButton size="small" onClick={copy} aria-label={t.commandCopy} sx={hitArea()}>
            {copied ? <DoneIcon fontSize="small" color="success" /> : <ContentCopyIcon fontSize="small" />}
          </IconButton>
        </Tooltip>
      </Box>
    </Box>
  );
}
