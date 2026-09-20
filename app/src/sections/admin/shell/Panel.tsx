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
import { visuallyHidden } from '@mui/utils';
import type { ReactNode } from 'react';

import { de } from '@/locales/admin';
import { TOUCH_TARGET } from '@/styles/hitArea';
import { display, garamond, letterpress, paper } from '@/styles/paper';

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
        <Typography variant="caption" color="textDisabled">
          {de.admin.shell.evidenceLoading}
        </Typography>
      </Box>
    );
  }
  if (empty) {
    return (
      <Typography variant="caption" color="textDisabled">
        {emptyText}
      </Typography>
    );
  }
  return <>{children}</>;
}

export function ViewHeader({
  eyebrow,
  title,
  titleText,
  intro,
  note,
  chips,
  children,
}: {
  // Which of the three views this is — the admin's counterpart to the public
  // pages' area kicker, set exactly like PageHeader's (hairline + tracked
  // uppercase in sepia).
  eyebrow?: string;
  title: ReactNode;
  // The heading as PLAIN TEXT, for the detail views whose visible head is a
  // ReactNode (paging arrows around a glyph chip). A string `title` becomes the
  // h1 itself; a node used to drop the heading level entirely, which left
  // /admin/buchstaben?g=a with six h2 and no h1 at all. Rendering the text as a
  // visually hidden h1 keeps the document outline whole without touching the
  // designed head.
  titleText?: string;
  intro?: string;
  // One short line UNDER the head that qualifies a control in it — today the
  // Subjekt-Stepper's „Reihenfolge: …". Its own slot rather than `intro`,
  // because the two answer different questions („was ist das hier" on an
  // overview vs. „was tun diese Pfeile" on a detail) and would never appear
  // together; caption size, since it is a gloss and not prose.
  note?: string;
  // Status of the subject (authored? locked? how many occurrences?).
  chips?: ReactNode;
  // Actions — rendered right-aligned on wide screens, wrapping below on phones.
  children?: ReactNode;
}) {
  return (
    <Box component="header" sx={{ mb: 2.5 }}>
      {eyebrow && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: '0.7rem', mb: '0.6rem' }}>
          <Box component="span" sx={{ width: 42, height: '1px', bgcolor: paper.sepia }} />
          <Typography
            component="span"
            variant="overline"
            sx={{ fontFamily: garamond, textTransform: 'uppercase', color: paper.sepia }}
          >
            {eyebrow}
          </Typography>
        </Box>
      )}
      {/* The hidden h1 for a node title. Clipped rather than display:none —
          hidden text is skipped by screen readers, and the heading is exactly
          what has to reach them. MUI's own object, not a local one: inside
          `sx`, `width: 1` is not one pixel but 100 % (the sizing transform
          reads values ≤ 1 as a fraction) and `m: -1` is −8 px of theme
          spacing, so the hand-rolled version put a full-viewport-wide box at
          the view's padding edge and pushed every detail page 16 px (8 px on
          phones) past the window. */}
      {typeof title !== 'string' && titleText && (
        <Typography component="h1" sx={visuallyHidden}>
          {titleText}
        </Typography>
      )}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
        {typeof title === 'string' ? (
          // The design system's heading rule: size from the ladder, face and
          // weight in sx — never a hard-coded px on a Playfair title
          // (design-system.md §"Typografie"). h4 is the workbench's page-title
          // step: a view header sits under a chrome bar, not on a landing page.
          <Typography
            component="h1"
            variant="h4"
            sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, textShadow: letterpress }}
          >
            {title}
          </Typography>
        ) : (
          title
        )}
        {chips && <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>{chips}</Box>}
        {/* The actions of a view head are `size="small"` Buttons, i.e. ~32.5 px
            — under the §9.3 floor, and invisible to the standing sweep because
            they only exist in a DETAIL state no route loads by itself. The
            floor sits on the container rather than on each call site: there are
            five heads and the next one would arrive without it. */}
        {children && (
          <Box
            sx={{
              display: 'flex',
              gap: 1,
              flexWrap: 'wrap',
              ml: { sm: 'auto' },
              '& > *': { minHeight: TOUCH_TARGET },
            }}
          >
            {children}
          </Box>
        )}
      </Box>
      {note && (
        <Typography variant="caption" sx={{ display: 'block', mt: 0.5, color: paper.sepia }}>
          {note}
        </Typography>
      )}
      {intro && (
        <Typography variant="body2" sx={{ mt: 0.75, maxWidth: '47rem', color: paper.inkSoft }}>
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
        {/* A panel title is a section heading, not body copy — Garamond at the
            subtitle step (a Playfair display face would compete with the
            specimen glyphs the panels are full of). */}
        <Typography component="h2" variant="subtitle2" sx={{ flex: 1, minWidth: 0, color: paper.ink }}>
          {title}
        </Typography>
        {/* Same floor as the view head above, for the same reason: a panel's
            actions are `size="small"` and live in detail states the standing
            sweep never loads. */}
        {actions && (
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', '& > *': { minHeight: TOUCH_TARGET } }}>
            {actions}
          </Box>
        )}
      </Box>
      {caption && (
        <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mb: 1 }}>
          {caption}
        </Typography>
      )}
      {children}
    </Box>
  );
}
