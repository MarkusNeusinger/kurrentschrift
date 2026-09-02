// MUI component defaults/overrides. Deliberately tiny — only what the identity
// actually adjusts, plus the three operability floors of design-system.md §9
// (visible focus, recognisable links, 14px type). Resist the file-per-override
// pattern until this outgrows a single screen.

import type { Components, Theme } from '@mui/material/styles';

import { TOUCH_TARGET } from '@/styles/hitArea';
import { paper } from '@/styles/paper';

// The one keyboard-focus ring of the site: 2px viridian, held off the element
// so it reads on the paper ground. Matches the hand-written rules that
// PaperCardLink and HeaderNavLink already carried — those two were, until this
// round, the only focusable surfaces of the public site that showed focus at
// all (audit 2026-09-02: MUI's ButtonBase sets `outline: 0`, so quiz answers,
// chips and icon buttons were indistinguishable when tabbed to).
const focusRing = { outline: `2px solid ${paper.viridian}`, outlineOffset: 2 } as const;

export const components: Components<Theme> = {
  MuiTypography: {
    defaultProps: {
      // MUI maps subtitle1/subtitle2 to <h6> by default, which litters the
      // document outline with phantom heading levels (screen readers announce
      // every definition-row term and timeline year as a section). They are
      // labels, not headings — render as <p>; a subtitle that really IS a
      // heading sets `component` explicitly at the call site.
      variantMapping: { subtitle1: 'p', subtitle2: 'p' },
    },
  },
  // ButtonBase is the shared root of Button, IconButton, ToggleButton and every
  // hand-built ButtonBase on the site — one rule here gives all of them a
  // visible focus ring instead of twelve per-component fixes.
  MuiButtonBase: {
    styleOverrides: {
      root: { '&.Mui-focusVisible': focusRing },
    },
  },
  MuiButton: {
    defaultProps: { disableElevation: true },
    styleOverrides: {
      root: { borderRadius: 4 },
      // MUI's `small` is 0.8125rem = 13px — below the binding 14px caption
      // floor (§9). Lifting it here raises every small button at once
      // („Link kopieren", „Lesetafel als PDF") without touching call sites.
      sizeSmall: { fontSize: '0.875rem' },
    },
    // The unfilled primary label is viridian (#40826d, 3.28:1 on the paper
    // ground) — below AA for label-sized text, and it is what „Lesetafel als
    // PDF" wore. `viridianText` is the token derived exactly for this (5.15:1);
    // the border keeps the brighter period tone. (MUI 9 dropped the
    // `outlinedPrimary`/`textPrimary` override slots — a variant is the
    // supported way to reach a variant+colour pair.)
    variants: [
      { props: { variant: 'outlined', color: 'primary' }, style: { color: paper.viridianText } },
      { props: { variant: 'text', color: 'primary' }, style: { color: paper.viridianText } },
    ],
  },
  MuiChip: {
    styleOverrides: {
      // Chip is not a ButtonBase, so it needs the ring spelled out again.
      root: { '&.Mui-focusVisible': focusRing },
      // The small chip shipped MUI's 0.75rem (12px) label in a 24px box — the
      // Federprobe examples measured 13px on screen, under the §9 floor. The
      // label inherits the root font size, so one value lifts both; the extra
      // 4px of height keeps the type from touching the border and moves the
      // chip closer to the touch floor.
      sizeSmall: { height: 28, fontSize: '0.875rem' },
    },
  },
  MuiLink: {
    // A link in running prose used to differ from the surrounding text by
    // colour alone — and by 1.35:1 at that (audit 2026-09-02), with the
    // underline appearing on hover only, i.e. never for keyboard or touch.
    // `always` plus the contrast-derived viridian is the WCAG 1.4.1 fix.
    // Chrome that deliberately reads as chrome (header nav, footer row) keeps
    // its own `textDecoration: 'none'` in `sx`, which wins over this default.
    defaultProps: { underline: 'always' },
    styleOverrides: {
      root: {
        color: paper.viridianText,
        // A hairline of the link colour rather than a full-strength rule — the
        // letter tone of the pages stays intact (style-guide §12).
        textDecorationColor: `${paper.viridianText}66`,
        transition: 'color .2s, text-decoration-color .2s',
        // Hover strengthens the RULE, not the colour: lifting the text to the
        // brighter #40826d would drop it back to 3.28:1 — a hover state is
        // text too.
        '&:hover': { textDecorationColor: paper.viridianText },
        '&:focus-visible': focusRing,
      },
    },
  },
  MuiPaper: {
    styleOverrides: {
      root: { backgroundImage: 'none' },
    },
  },
  MuiToggleButton: {
    styleOverrides: {
      // MUI's default unselected toggle text is neutral action.active alpha-black
      // (~#6f6b62, only 4.35:1 on the card and off the warm "one ink" palette).
      // Use soft ink instead — legible (~9.7:1) and on-identity; the selected
      // state keeps its own fill, the disabled state its own dimming.
      //
      // On phones the groups measured 38.8px high (audit 2026-09-02); below the
      // `sm` breakpoint they grow to the §9 touch floor. Desktop keeps the
      // tighter proportion, where a pointer is precise.
      root: ({ theme }) => ({
        color: theme.palette.text.secondary,
        [theme.breakpoints.down('sm')]: { minHeight: TOUCH_TARGET },
      }),
      // ToggleButton carries its own 13px `small` size — the Ausgangsschrift,
      // Liniensystem and Tempo switches all wore it, under the §9 floor.
      sizeSmall: { fontSize: '0.875rem' },
    },
  },
};
