import { useLayoutEffect, useState, type DependencyList, type RefObject } from 'react';

// Tracks an element's client size via ResizeObserver. The size is measured
// synchronously on (re-)attach and whenever the element resizes. `deps` re-keys
// the effect so the observer re-attaches (and re-measures) when the host node
// may have been swapped or re-shown (e.g. a dialog opening or a step change).
export function useElementSize<T extends HTMLElement>(
  ref: RefObject<T | null>,
  deps: DependencyList = [],
): { w: number; h: number } {
  const [size, setSize] = useState({ w: 0, h: 0 });
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setSize({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el);
    setSize({ w: el.clientWidth, h: el.clientHeight });
    return () => ro.disconnect();
    // The caller-provided deps intentionally drive re-attachment.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return size;
}
