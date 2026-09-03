// The one pathless root route's element: the shared Suspense boundary (bare
// paper ground while a chunk loads — no spinner flash) plus the scroll reset.
// Split out of routes/index.tsx so that file exports the router and nothing
// else; a module mixing components with a data export takes no Fast-Refresh
// update (react-refresh/only-export-components).
import { Suspense, useLayoutEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';

import { PaperBackground } from '@/components/PaperBackground';

// React Router keeps the scroll position across navigations, so following a
// link from the bottom of one page (e.g. the footer Impressum link) lands you
// at the bottom of the next. Reset to the top whenever the path changes —
// useLayoutEffect runs before paint so the new route never flashes at the old
// scroll position (client-only SPA, so no SSR concern).
function ScrollToTop() {
  const { pathname } = useLocation();
  useLayoutEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export function RootBoundary() {
  return (
    <Suspense fallback={<PaperBackground minHeight="100dvh" />}>
      <ScrollToTop />
      <Outlet />
    </Suspense>
  );
}
