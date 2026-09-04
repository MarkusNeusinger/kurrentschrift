import { useLayoutEffect, useState } from 'react';

// The width the FRAME around an element offers it, in px — the sibling of
// `useElementSize` for the one question that hook cannot answer.
//
// A box that hugs its content (the "as written" surfaces are `inline-flex`)
// measures its own ink, not its room: measuring it and then sizing the ink from
// that measurement is a loop that ratchets shut. The room is a property of the
// PARENT, so that is what is observed here — its CONTENT box, via the resize
// entry's own `contentRect`, so the frame's padding is already off (the
// Federprobe's card carries 16–32 px of it; `clientWidth` would hand it back as
// space to write in).
//
// Callers get 0 until the first observation. That is "not measured", never "no
// room": treat it as a reason to fall back, not as a width. Where the parent is
// a flex row with siblings, its content box is more room than the caller
// actually has — the estimate then errs on the wide side, which lands the
// caller back on its unmeasured behaviour rather than under it.
export function useAvailableWidth(el: HTMLElement | null): number {
  const [width, setWidth] = useState(0);
  useLayoutEffect(() => {
    const parent = el?.parentElement;
    if (!parent) return;
    // `observe()` delivers the first measurement itself for an element being
    // rendered (Resize Observer §"Observation will fire when observation starts
    // if Element is being rendered"), still before paint — so no hand-rolled
    // initial read, and no synchronous setState in this effect body.
    const ro = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
    ro.observe(parent);
    return () => ro.disconnect();
  }, [el]);
  return width;
}
