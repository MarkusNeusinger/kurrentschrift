// When a gallery tile is allowed to ask the server for its pixels.

import { useEffect, useState } from 'react';
import type { RefObject } from 'react';

/**
 * Whether an element has come within reach of the viewport — once true, it
 * stays true. The gallery fetches a crop only then: a page of 24 tiles would
 * otherwise fire 24 cuts at the server the moment a cell is clicked, most of
 * them for rows below the fold. Without IntersectionObserver (old browsers,
 * some test runners) everything counts as in view.
 */
export function useNearViewport(ref: RefObject<HTMLElement | null>): boolean {
  // The fallback is DERIVED rather than written into state from an effect
  // (react-hooks/set-state-in-effect): whether the browser can observe at all
  // is not something that happens later, so with no observer every tile counts
  // as in view from its very first render.
  const observable = typeof IntersectionObserver !== 'undefined';
  const [seen, setSeen] = useState(false);
  const near = !observable || seen;
  useEffect(() => {
    const node = ref.current;
    if (!node || near) return undefined;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setSeen(true);
          observer.disconnect();
        }
      },
      { rootMargin: '300px 0px' },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [ref, near]);
  return near;
}
