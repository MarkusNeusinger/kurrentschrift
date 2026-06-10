import { useLayoutEffect, useState } from 'react';

// Tracks an element's client size via ResizeObserver. Takes the element itself
// (held in state via a callback ref) rather than a RefObject: inside a portal
// (e.g. a MUI Dialog) the node mounts a render after its parent's effects ran,
// so a ref-plus-deps effect would measure `null` and never re-attach. Keying on
// the element re-measures exactly when the node (re)appears or is swapped.
export function useElementSize(el: HTMLElement | null): { w: number; h: number } {
  const [size, setSize] = useState({ w: 0, h: 0 });
  useLayoutEffect(() => {
    if (!el) return;
    const ro = new ResizeObserver(() => setSize({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el);
    setSize({ w: el.clientWidth, h: el.clientHeight });
    return () => ro.disconnect();
  }, [el]);
  return size;
}
