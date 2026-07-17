// useInView — true once the observed element has entered (or come within
// `rootMargin` of) the viewport, then stays true (one-shot). Gates expensive
// per-card work — e.g. the admin compare view's ~30 heavy diagnostic JSON
// fetches — behind actual visibility instead of firing everything on mount.
// Falls back to "always in view" where IntersectionObserver is unavailable.

import { useEffect, useRef, useState, type RefObject } from 'react';

export function useInView<T extends HTMLElement>(rootMargin = '200px'): [RefObject<T | null>, boolean] {
  const ref = useRef<T | null>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    if (inView) return;
    const el = ref.current;
    if (!el || typeof IntersectionObserver === 'undefined') {
      setInView(true);
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setInView(true);
          observer.disconnect();
        }
      },
      { rootMargin },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [inView, rootMargin]);

  return [ref, inView];
}
