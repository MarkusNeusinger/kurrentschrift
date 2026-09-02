// The floating return for the long content pages. /schriftkunde is 16 848px
// tall on a 390px phone — about twenty screens — and its only inner navigation
// is the jump list at the very top, which is unreachable after the first
// screen (audit 2026-09-02). Rather than turning that list into a sticky
// element (an intervention into the page IA, design-system §7), the page keeps
// one quiet way back.
//
// It only appears after two screens of scrolling, so it never sits on a page
// that does not need it, and it honours `prefers-reduced-motion` by jumping
// instead of gliding (design-system §8).

import { useEffect, useState } from 'react';

import { Box, IconButton } from '@mui/material';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';

import { usePrefersReducedMotion } from '@/hooks/usePrefersReducedMotion';
import { de } from '@/locales';
import { TOUCH_TARGET } from '@/styles/hitArea';
import { paper } from '@/styles/paper';

/** Screens of scrolling before the button shows itself. */
const APPEAR_AFTER_SCREENS = 2;

export function BackToTop() {
  const [visible, setVisible] = useState(false);
  const reduced = usePrefersReducedMotion();

  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > APPEAR_AFTER_SCREENS * window.innerHeight);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    return () => {
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
    };
  }, []);

  return (
    <Box
      sx={{
        position: 'fixed',
        zIndex: 1050,
        // Clear of the home indicator on a `viewport-fit=cover` phone.
        right: 'max(16px, env(safe-area-inset-right))',
        bottom: 'calc(16px + env(safe-area-inset-bottom))',
        // Kept mounted so the fade has something to run on; `visibility`
        // (not `display`) takes it out of the tab order while hidden.
        opacity: visible ? 1 : 0,
        visibility: visible ? 'visible' : 'hidden',
        transition: reduced ? 'none' : 'opacity .25s ease, visibility .25s',
      }}
    >
      <IconButton
        aria-label={de.common.backToTop.label}
        tabIndex={visible ? 0 : -1}
        onClick={() => window.scrollTo({ top: 0, behavior: reduced ? 'auto' : 'smooth' })}
        sx={{
          width: TOUCH_TARGET,
          height: TOUCH_TARGET,
          // A leaf of paper with the site's hairline, not a material FAB (§5).
          bgcolor: paper.hi,
          border: `1px solid ${paper.line}`,
          color: paper.inkSoft,
          boxShadow: '0 4px 14px rgba(36,26,16,0.14)',
          '&:hover': { bgcolor: paper.hi, color: paper.viridianText, borderColor: paper.viridian },
        }}
      >
        <KeyboardArrowUpIcon fontSize="small" />
      </IconButton>
    </Box>
  );
}
