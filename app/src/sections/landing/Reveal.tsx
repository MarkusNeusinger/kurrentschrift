import { Box } from '@mui/material';
import { useEffect, useRef, useState, type ReactNode } from 'react';

const reduce = '@media (prefers-reduced-motion: reduce)';
// Print gets the finished page: a reveal that never fired (nothing scrolls
// on paper) would print as a blank section.
const print = '@media print';

// Small scroll-reveal wrapper (IntersectionObserver, fires once). Without the
// observer (an old browser, a reader mode) the content shows at once.
export function Reveal({ children, delay = 0 }: { children: ReactNode; delay?: number }) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [shown, setShown] = useState(() => typeof IntersectionObserver === 'undefined');
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === 'undefined') return;
    const io = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) {
          setShown(true);
          io.disconnect();
        }
      },
      { threshold: 0.18 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    <Box
      ref={ref}
      sx={{
        opacity: shown ? 1 : 0,
        transform: shown ? 'none' : 'translateY(22px)',
        transition: `opacity .8s ease ${delay}s, transform .8s cubic-bezier(.2,.7,.2,1) ${delay}s`,
        [reduce]: { opacity: 1, transform: 'none' },
        [print]: { opacity: 1, transform: 'none', transition: 'none' },
      }}
    >
      {children}
    </Box>
  );
}
