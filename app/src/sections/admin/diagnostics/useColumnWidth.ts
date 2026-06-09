import { useEffect, useState } from 'react';

// Cap the column width to the viewport so the three columns wrap and fit on
// narrow phones instead of forcing horizontal scroll. `cap` is the desktop
// ceiling (320 by default; the Diagnose modal passes a larger one).
export function clampColumnWidth(viewport: number, cap = 320) {
  // Stay positive even on absurdly narrow viewports so the derived scale and
  // SVG/image width/height never go to 0 or negative.
  return Math.max(120, Math.min(cap, viewport - 64));
}

export function useColumnWidth(cap?: number) {
  const [w, setW] = useState(() => clampColumnWidth(typeof window !== 'undefined' ? window.innerWidth : 360, cap));
  useEffect(() => {
    const onResize = () => setW(clampColumnWidth(window.innerWidth, cap));
    // Recompute immediately so a changed cap applies without waiting for the
    // next resize event.
    onResize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [cap]);
  return w;
}
