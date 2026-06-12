// Route map assembly. Pages are lazy() so each route ships as its own chunk;
// one pathless root route provides the shared Suspense boundary (bare paper
// ground while a chunk loads — no spinner flash) and the error surface.
import { Suspense, useLayoutEffect } from 'react';
import { createBrowserRouter, Outlet, useLocation } from 'react-router-dom';

import { PaperBackground } from '@/components/PaperBackground';
import { RouteError } from '@/routes/RouteError';
import { adminRoutes } from '@/routes/sections/admin';
import { publicRoutes } from '@/routes/sections/public';

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

function RootBoundary() {
  return (
    <Suspense fallback={<PaperBackground minHeight="100dvh" />}>
      <ScrollToTop />
      <Outlet />
    </Suspense>
  );
}

export const router = createBrowserRouter([
  {
    element: <RootBoundary />,
    errorElement: <RouteError />,
    children: [...publicRoutes, ...adminRoutes],
  },
]);

export { paths } from '@/routes/paths';
