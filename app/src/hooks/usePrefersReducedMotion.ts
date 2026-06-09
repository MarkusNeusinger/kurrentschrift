import { useEffect, useState } from 'react';

export function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  );
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const on = () => setReduced(mq.matches);
    // `addEventListener` on MediaQueryList is missing on older Safari (<14);
    // fall back to the deprecated `addListener` so the toggle never throws.
    if (mq.addEventListener) {
      mq.addEventListener('change', on);
      return () => mq.removeEventListener('change', on);
    }
    mq.addListener(on);
    return () => mq.removeListener(on);
  }, []);
  return reduced;
}
