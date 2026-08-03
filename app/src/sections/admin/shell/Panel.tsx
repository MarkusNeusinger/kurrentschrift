// The two layout primitives the three views are built from, so Buchstaben,
// Übergänge and Wörter read as one surface rather than three pages that happen
// to share a header.
//
// `ViewHeader` is the top strip: what is under inspection, its status chips and
// the actions that apply to the whole subject (including ⚑). `Panel` is one
// bordered block of evidence with a title and a one-line caption saying WHAT it
// shows — the captions matter, because every panel here is a different layer of
// the pipeline and the layers are easy to confuse.

import { Alert, Box, CircularProgress, Typography } from '@mui/material';
import type { ReactNode } from 'react';

import { de } from '@/locales/admin';
import { display } from '@/styles/paper';

// The three states every occurrence-backed block shares. Kept here rather than
// repeated per view, because the failure case is the one that used to be
// missing everywhere: a failed occurrence load must SAY so, not leave a
// spinner running forever.
export function EvidenceState({
  loading,
  error,
  empty,
  emptyText,
  children,
}: {
  loading: boolean;
  error: boolean;
  empty?: boolean;
  emptyText?: string;
  children: ReactNode;
}) {
  if (error) {
    return (
      <Alert severity="warning" sx={{ py: 0 }}>
        {de.admin.shell.evidenceError}
      </Alert>
    );
  }
  if (loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <CircularProgress size={14} />
        <Typography variant="caption" color="text.disabled">
          {de.admin.shell.evidenceLoading}
        </Typography>
      </Box>
    );
  }
  if (empty) {
    return (
      <Typography variant="caption" color="text.disabled">
        {emptyText}
      </Typography>
    );
  }
  return <>{children}</>;
}

export function ViewHeader({
  title,
  intro,
  chips,
  children,
}: {
  title: ReactNode;
  intro?: string;
  // Status of the subject (authored? locked? how many occurrences?).
  chips?: ReactNode;
  // Actions — rendered right-aligned on wide screens, wrapping below on phones.
  children?: ReactNode;
}) {
  return (
    <Box sx={{ mb: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
        {typeof title === 'string' ? (
          <Typography sx={{ fontFamily: display, fontSize: 24, fontWeight: 600 }}>{title}</Typography>
        ) : (
          title
        )}
        {chips && <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>{chips}</Box>}
        {children && (
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', ml: { sm: 'auto' } }}>{children}</Box>
        )}
      </Box>
      {intro && (
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, maxWidth: 760 }}>
          {intro}
        </Typography>
      )}
    </Box>
  );
}

export function Panel({
  title,
  caption,
  actions,
  children,
}: {
  title: string;
  caption?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <Box
      component="section"
      sx={{ border: 1, borderColor: 'divider', borderRadius: 2, p: 2, bgcolor: 'background.paper', minWidth: 0 }}
    >
      <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, flexWrap: 'wrap', mb: caption ? 0.25 : 1 }}>
        <Typography variant="subtitle2" sx={{ flex: 1, minWidth: 0 }}>
          {title}
        </Typography>
        {actions}
      </Box>
      {caption && (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
          {caption}
        </Typography>
      )}
      {children}
    </Box>
  );
}
