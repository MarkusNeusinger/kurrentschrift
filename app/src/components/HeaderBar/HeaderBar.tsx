// The header chrome both the public site and the admin workbench wear.
//
// Until now the two bars were written twice, inline, and had drifted apart:
// same hairline and blur, but different heights (48 vs. 67px), different brand
// (the admin's wordmark had lost the viridian dot and the italic „.ink"),
// different nav faces (Garamond 13px buttons vs. Playfair links) and two
// different alphas over the same paper. Entering /admin read as leaving the
// site. These three primitives are the single source of that chrome — a change
// to the identity now reaches both bars or neither.
//
// What stays configurable is only what genuinely differs: the public pages sit
// in a centred 1280 column, the workbench is full-bleed (it needs the width for
// chart crops and letter grids), and the admin bar has to out-stack an app-bar
// layer while the public one deliberately sits low.

import { type MouseEvent, type ReactNode } from 'react';
import { Box, Link } from '@mui/material';
import { alpha } from '@mui/material/styles';
import type { SxProps, Theme } from '@mui/material/styles';
import { Link as RouterLink } from 'react-router-dom';

import { PAGE_WIDTHS } from '@/components/PageContainer';
import { de } from '@/locales';
import { display, paper } from '@/styles/paper';

export interface HeaderBarProps {
  children: ReactNode;
  /** Content column cap. `'none'` = full-bleed (the workbench). */
  maxWidth?: number | 'none';
  /** Stacking layer. The public bar sits low over page content; the admin bar
   *  has to stay above the workbench's own layers (but below the Korb drawer
   *  and the LetterPicker popover, which are meant to cover it). */
  zIndex?: number;
  sx?: SxProps<Theme>;
  /** Extra layout on the inner row — the admin's four slots wrap differently
   *  from the public's two. */
  contentSx?: SxProps<Theme>;
}

export function HeaderBar({ children, maxWidth = PAGE_WIDTHS.wide, zIndex = 20, sx, contentSx }: HeaderBarProps) {
  return (
    <Box
      component="header"
      sx={[
        {
          position: 'sticky',
          top: 0,
          zIndex,
          bgcolor: alpha(paper.bg, 0.86),
          backdropFilter: 'blur(6px)',
          borderBottom: '1px solid',
          borderColor: paper.line,
        },
        ...(Array.isArray(sx) ? sx : [sx]),
      ]}
    >
      <Box
        sx={[
          {
            maxWidth: maxWidth === 'none' ? 'none' : maxWidth,
            mx: 'auto',
            px: { xs: 2.5, sm: 4, md: 6 },
            py: 1.75,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: { xs: 1, sm: 2 },
          },
          ...(Array.isArray(contentSx) ? contentSx : [contentSx]),
        ]}
      >
        {children}
      </Box>
    </Box>
  );
}

export interface WordmarkProps {
  /** Where a plain click goes. */
  to: string;
  onClick?: (e: MouseEvent) => void;
}

/** •kurrentschrift.ink — the dot glows viridian, the TLD is viridian italic. */
export function Wordmark({ to, onClick }: WordmarkProps) {
  return (
    <Box
      component={RouterLink}
      to={to}
      onClick={onClick}
      sx={{
        display: 'inline-flex',
        alignItems: 'baseline',
        textDecoration: 'none',
        fontFamily: display,
        fontWeight: 600,
        // Fluid so the long „.ink" wordmark eases down on the narrowest phones
        // instead of forcing the bar wider than the viewport (it used to
        // overflow ≤360px); holds at 1.5rem on sm+.
        fontSize: 'clamp(1.05rem, 0.58rem + 2.4vw, 1.5rem)',
        letterSpacing: '0.02em',
        color: paper.ink,
        whiteSpace: 'nowrap',
      }}
    >
      <Box
        component="span"
        sx={{
          width: '0.42em',
          height: '0.42em',
          borderRadius: '50%',
          bgcolor: paper.viridian,
          alignSelf: 'center',
          mr: '0.2em',
          boxShadow: `0 0 6px ${paper.viridian}80`,
        }}
      />
      {de.common.brand.name}
      <Box component="span" sx={{ color: paper.viridian, fontStyle: 'italic' }}>
        {de.common.brand.tld}
      </Box>
    </Box>
  );
}

export interface HeaderNavLinkProps {
  label: ReactNode;
  to: string;
  /** Whether any page of this area is open. */
  active: boolean;
  /** `true` when this IS the open page — decides page vs. generic aria-current. */
  exact?: boolean;
  sx?: SxProps<Theme>;
}

/** One area link: Playfair, ink when current, with the viridian hairline that
 *  grows from 0 to full width on hover. */
export function HeaderNavLink({ label, to, active, exact = false, sx }: HeaderNavLinkProps) {
  return (
    <Link
      component={RouterLink}
      to={to}
      // "page" only when this IS the open page; a tool page inside the area
      // (e.g. /quiz under Lesen, /admin/buchstaben?g=a under Buchstaben) gets
      // the generic "true" current-marker.
      aria-current={active ? (exact ? 'page' : 'true') : undefined}
      sx={[
        {
          color: active ? paper.ink : paper.inkSoft,
          textDecoration: 'none',
          fontFamily: display,
          fontSize: { xs: '0.95rem', sm: '1.05rem' },
          position: 'relative',
          whiteSpace: 'nowrap',
          transition: 'color .25s',
          '&::after': {
            content: '""',
            position: 'absolute',
            left: 0,
            bottom: -4,
            height: '1px',
            width: active ? '100%' : 0,
            bgcolor: paper.viridian,
            transition: 'width .3s ease',
          },
          '&:hover': { color: paper.ink },
          '&:hover::after': { width: '100%' },
          // Visible keyboard-focus ring (2px viridian, offset).
          '&:focus-visible': { color: paper.ink, outline: `2px solid ${paper.viridian}`, outlineOffset: 3 },
        },
        ...(Array.isArray(sx) ? sx : [sx]),
      ]}
    >
      {label}
    </Link>
  );
}
