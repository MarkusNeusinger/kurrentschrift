import { useLayoutEffect, useState } from 'react';

// Size the diagnostic columns from the box they actually sit in, not from the
// window. Their one mount is the Diagnose modal, whose paper is 64 px narrower
// than the viewport and pads another 32 px inside — a window-derived width was
// too wide by exactly that much, so at 390 px the modal scrolled sideways and
// clipped the crop (author report on PR #533).
//
// `cap` is the desktop ceiling (320 by default; the Diagnose modal passes a
// larger one). The 120 px floor keeps the derived scale and the SVG/image
// width/height positive even in an absurdly narrow box.
export function clampColumnWidth(available: number, cap = 320) {
  return Math.max(120, Math.min(cap, available));
}

// Only for the frames before the container is measured (and for an environment
// without layout at all): the window minus the page gutters, which is what this
// hook used to return for good.
function viewportEstimate() {
  return typeof window === 'undefined' ? 360 : window.innerWidth - 64;
}

/**
 * Returns `[containerRef, columnWidth]`. Put the ref on the element whose width
 * the columns have to fit into.
 */
export function useColumnWidth(cap?: number): [(el: HTMLElement | null) => void, number] {
  // A callback ref rather than `useRef`: both views show a spinner first and
  // mount their container only once the payload lands, and state is what makes
  // that later mount re-run the measurement.
  const [container, setContainer] = useState<HTMLElement | null>(null);
  const [width, setWidth] = useState(() => clampColumnWidth(viewportEstimate(), cap));

  useLayoutEffect(() => {
    if (!container) return;
    const measure = () => setWidth(clampColumnWidth(container.clientWidth, cap));
    measure();
    // The container is block-level, so its width never follows the columns it
    // holds — observing it cannot loop. It also catches the width changes no
    // window resize reports: the modal's own scrollbar appearing, or a
    // breakpoint turning the dialog full-screen.
    if (typeof ResizeObserver === 'undefined') {
      window.addEventListener('resize', measure);
      return () => window.removeEventListener('resize', measure);
    }
    const observer = new ResizeObserver(measure);
    observer.observe(container);
    return () => observer.disconnect();
  }, [container, cap]);

  return [setContainer, width];
}
