// Route map assembly. Pages are lazy() so each route ships as its own chunk;
// one pathless root route provides the shared Suspense boundary (bare paper
// ground while a chunk loads — no spinner flash) and the error surface.
import { Suspense } from 'react';
import { createBrowserRouter, Outlet } from 'react-router-dom';

import { PaperBackground } from '@/components/PaperBackground';
import { RouteError } from '@/routes/RouteError';
import { adminRoutes } from '@/routes/sections/admin';
import { publicRoutes } from '@/routes/sections/public';

function RootBoundary() {
  return (
    <Suspense fallback={<PaperBackground minHeight="100dvh" />}>
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
