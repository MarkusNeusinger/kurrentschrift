// A shell command the author is meant to run, set so it can actually be typed
// or taken.
//
// The Eigenhand panels hand out five of them, and they used to sit INSIDE a
// running sentence in EB Garamond at 14px — a proportional antiqua, in which
// `--`, `-m`, `_` and `.` are exactly the characters that slip while typing,
// and where taking the command means selecting it out of the middle of a
// sentence by hand (audit 2026-09-02, finding 29). Monospace, its own line,
// `user-select: all` for one click, and a copy button beside it.

import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DoneIcon from '@mui/icons-material/Done';
import { Box, IconButton, Tooltip, Typography } from '@mui/material';
import { useState } from 'react';

import { de } from '@/locales/admin';
import { paper } from '@/styles/paper';

export function TerminalCommand({ command, lead }: { command: string; lead?: string }) {
  const t = de.admin.eigenhand;
  const [copied, setCopied] = useState(false);

  const copy = () => {
    // No clipboard permission prompt is worth an error box here: the command is
    // readable and selectable either way, so a refusal just leaves the button
    // un-ticked.
    void navigator.clipboard
      ?.writeText(command)
      .then(() => {
        setCopied(true);
        window.setTimeout(() => setCopied(false), 2000);
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
        <Box
          component="code"
          sx={{
            fontFamily: 'monospace',
            fontSize: 14,
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
        </Box>
        <Tooltip title={copied ? t.commandCopied : t.commandCopy}>
          <IconButton size="small" onClick={copy} aria-label={t.commandCopy}>
            {copied ? <DoneIcon fontSize="small" color="success" /> : <ContentCopyIcon fontSize="small" />}
          </IconButton>
        </Tooltip>
      </Box>
    </Box>
  );
}
