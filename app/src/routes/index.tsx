// Route map assembly. Pages are lazy() so each route ships as its own chunk;
// one pathless root route provides the shared Suspense boundary and the error
// surface (RootBoundary.tsx).
import { createBrowserRouter } from 'react-router-dom';

import { RootBoundary } from '@/routes/RootBoundary';
import { RouteError } from '@/routes/RouteError';
import { adminRoutes } from '@/routes/sections/admin';
import { publicRoutes } from '@/routes/sections/public';

export const router = createBrowserRouter([
  {
    element: <RootBoundary />,
    errorElement: <RouteError />,
    children: [...publicRoutes, ...adminRoutes],
  },
]);
